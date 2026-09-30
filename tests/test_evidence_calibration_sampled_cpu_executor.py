from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
import evidence_calibration_local_tool_sandbox_v9 as module
from evidence_calibration_local_tool_sandbox_v2 import Limits, ExecutionFailure
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory
from observe_evidence_calibration_tree_cpu_accounting_v3 import FIELDS

LOCAL = Limits(3, 2, 256*1024**2, 1024)
TREE = module.TreeLimits(64*1024**2, 16, 100)
SCRATCH = module.ScratchLimits(1024**2, 1024**2)
CPU = module.CpuBudget(1_000_000_000, 20, 250)


def execute(tmp_path, code, local=LOCAL, cpu=CPU):
    w = tmp_path/'workspace'; w.mkdir()
    identity = {'inventory': inventory(w)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    return module.run(w, identity, ['-c', code], limits=local, tree_limits=TREE,
                      scratch_limits=SCRATCH, cpu_budget=cpu, event_directory=tmp_path/'events')


def terminal(tmp_path):
    row = json.loads((tmp_path/'events/terminal.json').read_text())
    assert row['cleanup']['final_state']['stdout'].strip() == 'not-found'
    assert row['cpu_accounting']['hard_cpu_cap_verified'] is False
    assert row['cpu_accounting']['whole_turn_cpu_accounting_verified'] is False
    samples = sorted((tmp_path/'events').glob('cpu-sample-*.json'))
    assert len(samples) == row['cpu_accounting']['sample_count']
    assert all(json.loads(p.read_text())['unit'] == row['unit'] for p in samples)
    return row


def test_literal_success_preserves_lifecycle_scratch_and_final_cpu(tmp_path):
    result = execute(tmp_path, "print('%n ${HOME} $$ αβ')")
    assert result.returncode == 0 and result.stdout == '%n ${HOME} $$ αβ\n' and not result.stderr
    row = terminal(tmp_path)
    assert row['status'] == 'RETURNED' and row['namespace_lifecycle']['payload_exit_verified']
    assert 0 < row['cpu_accounting']['final_cpu_nanoseconds'] < CPU.cumulative_nanoseconds
    assert row['success_unit_release']['return_code'] == 0
    intent = json.loads((tmp_path/'events/intent.json').read_text())
    assert intent['cpu_budget']['cumulative_nanoseconds'] == CPU.cumulative_nanoseconds
    assert 'RemainAfterExit=yes' in intent['command']
    assert row['execution_audit']['scratch_limits']['temporary_bytes'] == 1024**2


def test_detached_children_trigger_tree_cpu_limit_with_null_result(tmp_path):
    code = "import subprocess,sys\ncs=[subprocess.Popen([sys.executable,'-c','while True: pass'],start_new_session=True) for _ in range(4)]\nprint('partial',flush=True)\nfor c in cs:c.wait()"
    cpu = replace(CPU, cumulative_nanoseconds=300_000_000)
    with pytest.raises(ExecutionFailure, match='CUMULATIVE_CPU_LIMIT'):
        execute(tmp_path, code, cpu=cpu)
    row = terminal(tmp_path)
    assert row['result'] is None and row['status'] == 'TECHNICAL_FAILURE'
    accounting = row['cpu_accounting']
    assert accounting['final_cpu_nanoseconds'] >= cpu.cumulative_nanoseconds
    assert accounting['observed_overshoot_nanoseconds'] == accounting['final_cpu_nanoseconds'] - cpu.cumulative_nanoseconds
    assert row['cpu_stop_action']['return_code'] == 0


@pytest.mark.parametrize('code,reason', [
    ('print("x"*4096)', 'OUTPUT_LIMIT'),
    ('x=bytearray(128*1024**2)', 'PROCESS_TREE_OOM'),
    ('import os;os.write(1,b"\\xff")', 'INVALID_UTF8_OUTPUT')])
def test_prior_failures_retain_null_dispositions_and_cpu_accounting(tmp_path, code, reason):
    with pytest.raises(ExecutionFailure, match=reason): execute(tmp_path, code)
    row = terminal(tmp_path)
    assert row['result'] is None
    assert row['cpu_accounting']['final_cpu_nanoseconds'] is not None


def test_wall_cutoff_retains_cpu_counter_before_cleanup(tmp_path):
    with pytest.raises(ExecutionFailure, match='WALL_TIME_LIMIT|SERVICE_WALL_TIME_LIMIT'):
        execute(tmp_path, 'import time;time.sleep(20)', local=replace(LOCAL,wall_seconds=1))
    row = terminal(tmp_path)
    assert row['result'] is None and row['cpu_accounting']['final_cpu_nanoseconds'] is not None


def test_program_error_keeps_verified_namespace_failure(tmp_path):
    result = execute(tmp_path, "import sys;print('setup-looking error',file=sys.stderr);sys.exit(7)")
    assert result.returncode == 7 and 'setup-looking error' in result.stderr
    row = terminal(tmp_path)
    assert row['status'] == 'TOOL_RUNTIME_FAILURE'
    assert row['namespace_lifecycle']['payload_exit_verified']
    assert not row['namespace_lifecycle']['model_failure_attributed']


def test_mount_failure_does_not_supply_partial_result(tmp_path, monkeypatch):
    original = module.bounded_namespace_command
    def missing_mount(*args):
        argv = original(*args); index = argv.index('--')
        argv[index:index] = ['--ro-bind', str(tmp_path/'absent'), '/absent']
        return argv
    monkeypatch.setattr(module, 'bounded_namespace_command', missing_mount)
    with pytest.raises(ExecutionFailure, match='NAMESPACE_LIFECYCLE_INCOMPLETE'):
        execute(tmp_path, 'print("must not run")')
    assert terminal(tmp_path)['result'] is None


@pytest.mark.parametrize('field,value', [('cumulative_nanoseconds',True), ('cumulative_nanoseconds',1),
                                       ('poll_milliseconds',0), ('poll_milliseconds',251),
                                       ('query_timeout_milliseconds',None)])
def test_invalid_cpu_limits_fail_before_service_intent(field, value):
    with pytest.raises(ValueError): replace(CPU, **{field:value})


def props(cpu='1000', active='active', sub='running', load='loaded', code='0'):
    row = {'LoadState':load,'ActiveState':active,'SubState':sub,'Result':'success',
           'ExecMainCode':code,'ExecMainStatus':'0','CPUUsageNSec':cpu,
           'ControlGroup':'/synthetic','TasksCurrent':'1'}
    return '\n'.join(f'{key}={row[key]}' for key in FIELDS.split(','))+'\n'


def monitor_with_responses(tmp_path, monkeypatch, responses):
    remaining = iter(responses)
    def query(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 0, next(remaining), '')
    monkeypatch.setattr(module.subprocess, 'run', query)
    return module.CpuMonitor({}, 'synthetic', CPU, tmp_path)


def test_only_unobserved_startup_may_have_missing_cpu(tmp_path, monkeypatch):
    monitor = monitor_with_responses(tmp_path, monkeypatch,
        [props('[not set]','inactive','dead'),props(),props('[not set]','inactive','dead')])
    assert monitor.sample() is None and monitor.last_cpu is None
    assert monitor.sample()['CPUUsageNSec'] == 1000
    with pytest.raises(module.CpuAccountingError): monitor.sample()
    assert len(list(tmp_path.glob('cpu-sample-*'))) == 3


@pytest.mark.parametrize('last', [props('999'), props('[not set]'), props('18446744073709551615'),
                                props('nan'), props('1000',load='not-found')])
def test_invalid_or_lost_counter_is_persisted_then_rejected(tmp_path, monkeypatch, last):
    monitor = monitor_with_responses(tmp_path, monkeypatch, [props(), last])
    monitor.sample()
    with pytest.raises(module.CpuAccountingError): monitor.sample()
    assert len(monitor.samples) == 2
    assert json.loads((tmp_path/'cpu-sample-00000001.json').read_text())['stdout'] == last


def test_running_counter_cannot_be_final_or_treated_as_success(tmp_path, monkeypatch):
    monitor = monitor_with_responses(tmp_path, monkeypatch, [props()])
    with pytest.raises(module.CpuAccountingError): monitor.save_final(monitor.sample())
    assert monitor.final_cpu is None and monitor.audit()['observed_overshoot_nanoseconds'] is None


def test_exact_startup_repair_preserves_failed_v8_source():
    first = (ROOT/'analysis/evidence_calibration_local_tool_sandbox_v8.py').read_text()
    second = (ROOT/'analysis/evidence_calibration_local_tool_sandbox_v9.py').read_text()
    expected = first.replace('intent/v8-development','intent/v9-development').replace('terminal/v8-development','terminal/v9-development')
    expected = expected.replace("        if properties.get('LoadState') == 'not-found' and self.last_cpu is None:\n", "        pending_loaded_startup = (properties.get('LoadState') == 'loaded'\n            and properties.get('ActiveState') == 'inactive' and properties.get('SubState') == 'dead'\n            and properties.get('ExecMainCode') == '0' and properties.get('Result') == 'success'\n            and properties.get('CPUUsageNSec') == '[not set]')\n        if self.last_cpu is None and (properties.get('LoadState') == 'not-found' or pending_loaded_startup):\n")
    assert second == expected
