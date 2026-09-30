from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'analysis'))
import evidence_calibration_local_tool_sandbox_v10 as module
from evidence_calibration_local_tool_sandbox_v2 import Limits, ExecutionFailure
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory

LOCAL = Limits(3,2,256*1024**2,1024)
TREE = module.TreeLimits(64*1024**2,16,100)
SCRATCH = module.ScratchLimits(1024**2,1024**2)
CPU = module.CpuBudget(1_000_000_000,20,250)


def execute(tmp_path, code, cpu=CPU):
    w=tmp_path/'workspace';w.mkdir()
    identity={'inventory':inventory(w)};identity['workspace_sha256']=canonical_sha256(identity)
    return module.run(w,identity,['-c',code],limits=LOCAL,tree_limits=TREE,scratch_limits=SCRATCH,
                      cpu_budget=cpu,event_directory=tmp_path/'events')


def terminal(tmp_path):
    t=json.loads((tmp_path/'events/terminal.json').read_text())
    assert t['cleanup']['final_state']['stdout'].strip()=='not-found'
    return t


@pytest.mark.parametrize('active,sub,tasks,cgroup,accepted',[
    ('active','exited','[not set]','',True),
    ('failed','failed','[not set]','',True),
    ('active','exited','0','/retained-but-empty',True),
    ('active','exited','1','/descendants',False),
    ('failed','failed','2','/descendants',False),
    ('active','exited','[not set]','/unknown',False),
    ('active','exited','','',False),
    ('active','exited','-1','',False),
    ('active','running','0','',False),
])
def test_final_cpu_requires_terminal_state_and_quiescent_tree(tmp_path,active,sub,tasks,cgroup,accepted):
    monitor=module.CpuMonitor({},'synthetic',CPU,tmp_path)
    row={'ActiveState':active,'SubState':sub,'TasksCurrent':tasks,'ControlGroup':cgroup,'CPUUsageNSec':123}
    if accepted:
        monitor.save_final(row)
        assert monitor.final_cpu==123
    else:
        with pytest.raises(module.CpuAccountingError):monitor.save_final(row)
        assert monitor.final_cpu is None


def test_literal_success_retains_complete_lifecycle_and_cpu(tmp_path):
    r=execute(tmp_path,"print('%n ${HOME} $$ αβ')")
    assert r.stdout=='%n ${HOME} $$ αβ\n' and r.returncode==0 and not r.stderr
    t=terminal(tmp_path)
    assert t['namespace_lifecycle']['payload_exit_verified']
    assert 0 < t['cpu_accounting']['final_cpu_nanoseconds'] < CPU.cumulative_nanoseconds
    assert t['cpu_accounting']['hard_cpu_cap_verified'] is False


def test_descendant_cutoff_stops_tree_and_retains_overshoot(tmp_path):
    code="import subprocess,sys\ncs=[subprocess.Popen([sys.executable,'-c','while True: pass'],start_new_session=True) for _ in range(4)]\nprint('partial',flush=True)\nfor c in cs:c.wait()"
    cpu=replace(CPU,cumulative_nanoseconds=300_000_000)
    with pytest.raises(ExecutionFailure,match='CUMULATIVE_CPU_LIMIT'):
        execute(tmp_path,code,cpu)
    t=terminal(tmp_path); a=t['cpu_accounting']
    assert t['result'] is None
    assert a['final_cpu_nanoseconds'] >= cpu.cumulative_nanoseconds
    assert a['observed_overshoot_nanoseconds']==a['final_cpu_nanoseconds']-cpu.cumulative_nanoseconds


def test_program_error_keeps_final_cpu_and_namespace_exit(tmp_path):
    r=execute(tmp_path,'import sys;sys.exit(7)')
    assert r.returncode==7
    t=terminal(tmp_path)
    assert t['status']=='TOOL_RUNTIME_FAILURE' and t['namespace_lifecycle']['payload_exit_verified']
    assert t['cpu_accounting']['final_cpu_nanoseconds'] is not None


def test_exact_quiescent_tree_guard_preserves_v9():
    previous=(ROOT/'analysis/evidence_calibration_local_tool_sandbox_v9.py').read_text()
    current=(ROOT/'analysis/evidence_calibration_local_tool_sandbox_v10.py').read_text()
    expected=previous.replace('intent/v9-development','intent/v10-development').replace('terminal/v9-development','terminal/v10-development')
    expected=expected.replace("        self.final_cpu = row['CPUUsageNSec']\n", "        quiescent = (row['TasksCurrent'] == '0' or\n                     (row['TasksCurrent'] == '[not set]' and row['ControlGroup'] == ''))\n        if not quiescent:\n            raise CpuAccountingError('final CPU counter lacks quiescent tree or retired cgroup')\n        self.final_cpu = row['CPUUsageNSec']\n",1)
    assert current==expected


def test_staged_b2_primitive_matches_reference_under_sampled_cpu_guard(tmp_path):
    import build_evidence_calibration_five_method_packet_candidate as candidate
    from build_evidence_calibration_method_packets import build
    from inspect_evidence_calibration_packet import summarize
    from stage_evidence_calibration_workspace import staged_workspace
    diagnostic=json.loads((ROOT/'data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json').read_text())
    catalog=json.loads((ROOT/candidate.CATALOG).read_text())
    entry=candidate.materialize(diagnostic,'test-config','measured_response_recovery',catalog)[-1]
    packet=next(p for p in build(entry,candidate.execution_contract(entry,diagnostic))['method_packets'] if p['method_id']=='B2')
    with staged_workspace(entry,packet) as (w,b):
        r=module.run(w,b,['tools/inspect_evidence_calibration_packet.py','robot_visible/evidence.json'],
            limits=replace(LOCAL,combined_output_bytes=1024**2),tree_limits=TREE,scratch_limits=SCRATCH,
            cpu_budget=CPU,event_directory=tmp_path/'primitive-events')
        assert r.returncode==0,r.stderr
        assert json.loads(r.stdout)==summarize(entry['method_packet'])
    t=json.loads((tmp_path/'primitive-events/terminal.json').read_text())
    assert t['cpu_accounting']['final_cpu_nanoseconds'] is not None
    assert t['cleanup']['final_state']['stdout'].strip()=='not-found'


def test_missing_live_counter_fails_closed_after_startup(tmp_path,monkeypatch):
    import subprocess
    from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS
    original=subprocess.run
    injected=False
    def query(argv,*args,**kwargs):
        nonlocal injected
        result=original(argv,*args,**kwargs)
        if ('--property='+FIELDS in argv and not injected
                and 'ActiveState=active\nSubState=running\n' in result.stdout):
            injected=True
            lines=result.stdout.splitlines()
            result.stdout='\n'.join('CPUUsageNSec=[not set]' if line.startswith('CPUUsageNSec=') else line for line in lines)+'\n'
        return result
    monkeypatch.setattr(subprocess,'run',query)
    with pytest.raises(ExecutionFailure,match='CPU_ACCOUNTING_UNVERIFIED'):
        execute(tmp_path,'import time;print("partial",flush=True);time.sleep(20)')
    t=terminal(tmp_path)
    assert injected and t['result'] is None
    assert t['execution_audit']['partial_output_only']
