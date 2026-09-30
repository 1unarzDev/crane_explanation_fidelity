import base64
from dataclasses import asdict
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from evidence_calibration_tool_broker_v5 import ToolBroker, READ, COMPUTE, tool_definitions
from evidence_calibration_tool_broker_v2 import tool_definitions as old_definitions
from evidence_calibration_local_tool_sandbox_v2 import Limits, ExecutionFailure
from evidence_calibration_local_tool_sandbox_v10 import TreeLimits, ScratchLimits, CpuBudget
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory

LOCAL = Limits(3, 2, 256*1024**2, 1024)
TREE = TreeLimits(64*1024**2,16,100)
SCRATCH = ScratchLimits(1024**2,1024**2)
CPU = CpuBudget(1_000_000_000,20,250)


def broker(tmp_path, method='B2', max_calls=2):
    workspace = tmp_path / 'job'; workspace.mkdir()
    (workspace/'visible.txt').write_text('α' * 4096)
    identity = {'method_id':method,'inventory':inventory(workspace)}
    identity['workspace_sha256']=canonical_sha256(identity)
    return ToolBroker(workspace,identity,tmp_path/'events',max_calls=max_calls,limits=LOCAL,tree_limits=TREE,scratch_limits=SCRATCH,cpu_budget=CPU)


@pytest.mark.parametrize('method',['B0','B1','B2','B3','B4'])
def test_tool_parity_is_exactly_preserved(method):
    assert tool_definitions(method)==old_definitions(method)


def test_lossless_read_is_not_capped_by_compute_output_budget(tmp_path):
    b=broker(tmp_path)
    r=b.call('read',READ,{'path':'visible.txt','offset':0,'length':None})
    assert r['result']['text']=='α'*4096 and r['result']['eof']
    assert not (b.events/'read.execution').exists()


def test_literal_computation_and_nested_one_shot_records(tmp_path):
    b=broker(tmp_path)
    r=b.call('literal',COMPUTE,{'code':"print('%n ${HOME} $$ α')"})
    assert r['result']['stdout']=='%n ${HOME} $$ α\n'
    intent=json.loads((b.events/'literal.intent.json').read_text())
    service=json.loads((b.events/'literal.execution/intent.json').read_text())
    terminal=json.loads((b.events/'literal.execution/terminal.json').read_text())
    assert intent['request']['tree_limits']==service['tree_limits']==asdict(TREE)
    assert intent['request']['local_limits']==service['local_limits']==asdict(LOCAL)
    assert intent['request']['cpu_budget']==service['cpu_budget']==asdict(CPU)
    assert terminal['cpu_accounting']['final_cpu_nanoseconds'] is not None
    assert terminal['cleanup']['final_state']['stdout'].strip()=='not-found'
    with pytest.raises(ValueError,match='no replay'):
        b.call('literal',COMPUTE,{'code':'print(1)'})


@pytest.mark.parametrize('name,code,reason',[
    ('flood','print("x"*4096)','OUTPUT_LIMIT'),
    ('memory','x=bytearray(128*1024**2)','PROCESS_TREE_OOM')])
def test_failed_execution_retains_both_terminal_levels_without_partial_result(tmp_path,name,code,reason):
    b=broker(tmp_path)
    with pytest.raises(ExecutionFailure,match=reason):
        b.call(name,COMPUTE,{'code':code})
    outer=json.loads((b.events/(name+'.result.json')).read_text())
    inner=json.loads((b.events/(name+'.execution')/'terminal.json').read_text())
    assert outer['status']==inner['status']=='TECHNICAL_FAILURE'
    assert outer['result'] is inner['result'] is None
    assert outer['execution_audit']==inner
    assert inner['execution_audit']['partial_output_only']
    with pytest.raises(ValueError,match='no replay'):
        b.call(name,COMPUTE,{'code':'print(1)'})


def test_actual_staged_primitive_matches_existing_reference(tmp_path):
    from dataclasses import replace
    import build_evidence_calibration_five_method_packet_candidate as candidate
    from build_evidence_calibration_method_packets import build
    from inspect_evidence_calibration_packet import summarize
    from stage_evidence_calibration_workspace import staged_workspace
    diagnostic=json.loads((ROOT/'data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json').read_text())
    catalog=json.loads((ROOT/candidate.CATALOG).read_text())
    entry=candidate.materialize(diagnostic,'test-config','measured_response_recovery',catalog)[-1]
    packets=build(entry,candidate.execution_contract(entry,diagnostic))
    packet=next(p for p in packets['method_packets'] if p['method_id']=='B2')
    with staged_workspace(entry,packet) as (workspace,identity):
        b=ToolBroker(workspace,identity,tmp_path/'real-events',max_calls=1,
                     limits=replace(LOCAL,combined_output_bytes=1024**2),tree_limits=TREE,scratch_limits=SCRATCH,cpu_budget=CPU)
        r=b.call('inventory',COMPUTE,{'code':"import runpy,sys; sys.argv=['inventory','robot_visible/evidence.json']; runpy.run_path('tools/inspect_evidence_calibration_packet.py',run_name='__main__')"})
        assert json.loads(r['result']['stdout'])==summarize(entry['method_packet'])


def test_scratch_and_lifecycle_are_bound_in_nested_transactions(tmp_path):
    b=broker(tmp_path)
    b.call('scratch',COMPUTE,{'code':"import os;print(os.statvfs('/tmp').f_blocks*os.statvfs('/tmp').f_frsize)"})
    outer=json.loads((b.events/'scratch.intent.json').read_text())
    inner=json.loads((b.events/'scratch.execution/intent.json').read_text())
    final=json.loads((b.events/'scratch.execution/terminal.json').read_text())
    assert outer['request']['scratch_limits']==inner['scratch_limits']==asdict(SCRATCH)
    assert final['namespace_lifecycle']['payload_exit_verified']


def test_tree_cpu_cutoff_binds_budget_and_withholds_partial_output(tmp_path):
    from dataclasses import replace
    workspace=tmp_path/'job';workspace.mkdir()
    identity={'method_id':'B2','inventory':inventory(workspace)}
    identity['workspace_sha256']=canonical_sha256(identity)
    cpu=replace(CPU,cumulative_nanoseconds=300_000_000)
    b=ToolBroker(workspace,identity,tmp_path/'events',max_calls=1,limits=LOCAL,tree_limits=TREE,
                 scratch_limits=SCRATCH,cpu_budget=cpu)
    code="import subprocess,sys\ncs=[subprocess.Popen([sys.executable,'-c','while True: pass'],start_new_session=True) for _ in range(4)]\nprint('partial',flush=True)\nfor c in cs:c.wait()"
    with pytest.raises(ExecutionFailure,match='CUMULATIVE_CPU_LIMIT'):
        b.call('cpu',COMPUTE,{'code':code})
    outer=json.loads((b.events/'cpu.result.json').read_text())
    inner=json.loads((b.events/'cpu.execution/terminal.json').read_text())
    assert outer['result'] is inner['result'] is None
    assert outer['execution_audit']==inner
    assert inner['cpu_accounting']['budget']==asdict(cpu)
    assert inner['cpu_accounting']['final_cpu_nanoseconds']>=cpu.cumulative_nanoseconds
    assert inner['cpu_accounting']['hard_cpu_cap_verified'] is False
    assert inner['cleanup']['final_state']['stdout'].strip()=='not-found'
    with pytest.raises(ValueError,match='no replay'):
        b.call('cpu',COMPUTE,{'code':'print(1)'})


def test_cpu_configuration_is_mandatory_before_event_namespace(tmp_path):
    workspace=tmp_path/'job';workspace.mkdir()
    identity={'method_id':'B2','inventory':inventory(workspace)}
    identity['workspace_sha256']=canonical_sha256(identity)
    with pytest.raises(ValueError,match='CpuBudget required'):
        ToolBroker(workspace,identity,tmp_path/'events',max_calls=1,limits=LOCAL,tree_limits=TREE,
                   scratch_limits=SCRATCH,cpu_budget=None)
    assert not (tmp_path/'events').exists()
