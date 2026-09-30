from dataclasses import asdict
import json
import os
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_computation_cpu_ledger import ComputationCpuLedger,ComputationCpuLimit,bounded_json
from evidence_calibration_local_tool_sandbox_v10 import CpuBudget
from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS

CPU=CpuBudget(100_000_000,20,250)
SHA='a'*64


def ledger(tmp_path,total=150_000_000):
    return ComputationCpuLedger(tmp_path/'ledger',SHA,limit=ComputationCpuLimit(total),per_call=CPU)


def evidence(directory,reservation,cpu=70_000_000,status='RETURNED'):
    directory.mkdir()
    budget=reservation['effective_cpu_budget']
    intent={'schema':'crane-service-computation-intent/v10-development','unit':'synthetic',
            'workspace_identity':{'workspace_sha256':SHA},'cpu_budget':budget}
    terminal={'schema':'crane-service-computation-terminal/v10-development','unit':'synthetic','status':status,
              'cpu_accounting':{'budget':budget,'final_cpu_nanoseconds':cpu,'last_observed_cpu_nanoseconds':cpu,
                  'observed_overshoot_nanoseconds':max(0,cpu-budget['cumulative_nanoseconds']),
                  'hard_cpu_cap_verified':False,'whole_turn_cpu_accounting_verified':False,'sample_count':1},
              'cleanup':{'final_state':{'return_code':0,'stdout':'not-found\n'}}}
    props={'LoadState':'loaded','ActiveState':'active' if status=='RETURNED' else 'failed',
           'SubState':'exited' if status=='RETURNED' else 'failed','Result':'success' if status=='RETURNED' else 'signal',
           'ExecMainCode':'1','ExecMainStatus':'0','CPUUsageNSec':str(cpu),'ControlGroup':'','TasksCurrent':'[not set]'}
    sample={'unit':'synthetic','return_code':0,'stdout':'\n'.join(f'{key}={props[key]}' for key in FIELDS.split(','))+'\n'}
    for name,row in [('intent.json',intent),('terminal.json',terminal),('cpu-sample-00000000.json',sample)]:
        (directory/name).write_text(json.dumps(row))


def test_charges_failed_calls_and_overshoot_without_clamping(tmp_path):
    l=ledger(tmp_path)
    first=l.reserve('one',tmp_path/'one','b'*64);evidence(tmp_path/'one',first)
    one=l.settle('one');assert one['spent_after_nanoseconds']==70_000_000
    second=l.reserve('two',tmp_path/'two','c'*64)
    assert second['effective_cpu_budget']['cumulative_nanoseconds']==80_000_000
    evidence(tmp_path/'two',second,110_000_000,'TECHNICAL_FAILURE')
    two=l.settle('two')
    assert two['actual_cpu_nanoseconds']==110_000_000
    assert two['unclamped_overshoot_nanoseconds']==30_000_000
    assert l.snapshot()['spent_nanoseconds']==180_000_000
    assert l.snapshot()['remaining_nanoseconds']==0
    with pytest.raises(ValueError,match='EXHAUSTED'):l.reserve('three',tmp_path/'three','d'*64)
    l.ensure_known() # Computation CPU exhaustion does not measure or prohibit reads.


def test_pending_and_unknown_admission_are_closed_without_a_zero_total(tmp_path):
    l=ledger(tmp_path);l.reserve('one',tmp_path/'absent','b'*64)
    assert l.snapshot()['remaining_nanoseconds'] is None
    with pytest.raises(ValueError,match='UNSETTLED'):l.reserve('two',tmp_path/'two','c'*64)
    unknown=l.settle('one')
    assert unknown['status']=='UNKNOWN_ACCOUNTING_ADMISSION_CLOSED'
    assert unknown['spent_after_nanoseconds'] is None and unknown['actual_cpu_nanoseconds'] is None
    assert l.snapshot()['spent_nanoseconds'] is None and l.snapshot()['remaining_nanoseconds'] is None
    assert l.snapshot()['settled_known_cpu_nanoseconds']==0
    with pytest.raises(ValueError,match='ACCOUNTING_UNKNOWN'):l.ensure_known()


def test_event_and_namespace_cannot_be_replayed_or_adopted(tmp_path):
    l=ledger(tmp_path);r=l.reserve('one',tmp_path/'one','b'*64);evidence(tmp_path/'one',r);l.settle('one')
    with pytest.raises(ValueError,match='no replay'):l.reserve('one',tmp_path/'other','c'*64)
    with pytest.raises(ValueError,match='no replay'):l.settle('one')
    with pytest.raises(FileExistsError):ledger(tmp_path)


def test_remaining_below_executor_minimum_is_not_rounded_up(tmp_path):
    l=ledger(tmp_path,total=75_000_000);r=l.reserve('one',tmp_path/'one','b'*64)
    evidence(tmp_path/'one',r,70_000_000);l.settle('one')
    assert l.snapshot()['remaining_nanoseconds']==5_000_000
    with pytest.raises(ValueError,match='BELOW_EXECUTOR_MINIMUM'):l.reserve('two',tmp_path/'two','c'*64)


@pytest.mark.parametrize('defect',['final_missing','final_bool','final_mismatch','budget','overshoot','cleanup',
                                  'sample_missing','sample_identity','sample_counter','sample_nonquiescent',
                                  'sample_regression','sample_sequence','workspace','unit'])
def test_corrupt_accounting_closes_admission(tmp_path,defect):
    l=ledger(tmp_path);r=l.reserve('one',tmp_path/'one','b'*64);evidence(tmp_path/'one',r)
    directory=tmp_path/'one'
    terminal=json.loads((directory/'terminal.json').read_text());a=terminal['cpu_accounting']
    sample=json.loads((directory/'cpu-sample-00000000.json').read_text())
    if defect=='final_missing':a['final_cpu_nanoseconds']=None
    elif defect=='final_bool':a['final_cpu_nanoseconds']=True
    elif defect=='final_mismatch':a['final_cpu_nanoseconds']=1
    elif defect=='budget':a['budget']['cumulative_nanoseconds']=1000
    elif defect=='overshoot':a['observed_overshoot_nanoseconds']=1
    elif defect=='cleanup':terminal['cleanup']['final_state']['stdout']='loaded'
    elif defect=='sample_missing':a['sample_count']=2
    elif defect=='sample_identity':sample['unit']='other'
    elif defect=='sample_counter':sample['stdout']=sample['stdout'].replace('CPUUsageNSec=70000000','CPUUsageNSec=[not set]')
    elif defect=='sample_nonquiescent':sample['stdout']=sample['stdout'].replace('TasksCurrent=[not set]','TasksCurrent=1')
    elif defect=='sample_regression':
        a['sample_count']=2
        high={**sample,'stdout':sample['stdout'].replace('CPUUsageNSec=70000000','CPUUsageNSec=80000000').replace('SubState=exited','SubState=running')}
        (directory/'cpu-sample-00000000.json').write_text(json.dumps(high))
        (directory/'cpu-sample-00000001.json').write_text(json.dumps(sample))
    elif defect=='sample_sequence':(directory/'cpu-sample-00000000.json').rename(directory/'cpu-sample-00000002.json')
    elif defect in {'workspace','unit'}:
        intent=json.loads((directory/'intent.json').read_text())
        if defect=='workspace':intent['workspace_identity']['workspace_sha256']='f'*64
        else:intent['unit']='other'
        (directory/'intent.json').write_text(json.dumps(intent))
    (directory/'terminal.json').write_text(json.dumps(terminal))
    if defect not in {'sample_regression','sample_sequence'}:(directory/'cpu-sample-00000000.json').write_text(json.dumps(sample))
    result=l.settle('one')
    assert result['status']=='UNKNOWN_ACCOUNTING_ADMISSION_CLOSED'
    assert result['actual_cpu_nanoseconds'] is None
    with pytest.raises(ValueError,match='UNKNOWN'):l.ensure_known()


def test_settlement_retention_failure_keeps_reservation_pending(tmp_path,monkeypatch):
    import evidence_calibration_computation_cpu_ledger as module
    l=ledger(tmp_path);r=l.reserve('one',tmp_path/'one','b'*64);evidence(tmp_path/'one',r)
    original=module.write_once
    def fail(path,value):
        if path.name.endswith('.result.json'):raise OSError('synthetic storage failure')
        return original(path,value)
    monkeypatch.setattr(module,'write_once',fail)
    with pytest.raises(OSError):l.settle('one')
    assert l.pending is not None and l.spent==0
    with pytest.raises(ValueError,match='no replay'):l.settle('one')
    with pytest.raises(ValueError,match='UNSETTLED'):l.ensure_known()


@pytest.mark.parametrize('value',[True,0,1,3_600_000_000_001,None])
def test_total_cpu_limit_is_explicit_and_typed(value):
    with pytest.raises(ValueError):ComputationCpuLimit(value)


def test_operator_record_reader_rejects_links_fifo_and_size_overflow(tmp_path):
    path=tmp_path/'real';path.write_text('{"valid":true}')
    with pytest.raises(ValueError):bounded_json(path,2)
    link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(OSError):bounded_json(link)
    fifo=tmp_path/'fifo';os.mkfifo(fifo)
    with pytest.raises(ValueError,match='regular'):bounded_json(fifo)
