import base64
from dataclasses import replace
import json
from pathlib import Path
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox_v2 import ExecutionFailure, Limits, run
from evidence_calibration_tool_broker_v2 import ToolBroker, COMPUTE, READ, tool_definitions
from stage_evidence_calibration_workspace import inventory

# Synthetic test budgets only: not proposed or frozen method/study budgets.
LIMITS = Limits(wall_seconds=3, cpu_seconds_per_process=1,
                address_space_bytes_per_process=128 * 1024**2, combined_output_bytes=1024)


def identity(workspace, method='B2'):
    bound = {'method_id': method, 'inventory': inventory(workspace)}
    bound['workspace_sha256'] = canonical_sha256(bound)
    return bound


def test_exact_output_including_unicode_and_eof_at_limit(tmp_path):
    result = run(tmp_path, identity(tmp_path), ['-c', "import os; os.write(1,b'a'*512); os.write(2,b'b'*512)"], limits=LIMITS)
    assert result.returncode == 0
    assert result.stdout == 'a' * 512 and result.stderr == 'b' * 512
    unicode_result = run(tmp_path, identity(tmp_path), ['-c', "print('αβ')"], limits=LIMITS)
    assert unicode_result.stdout == 'αβ\n'


@pytest.mark.parametrize('stream', [1, 2])
def test_output_flood_is_bounded_failure_with_partial_audit(tmp_path, stream):
    with pytest.raises(ExecutionFailure, match='OUTPUT_LIMIT') as error:
        run(tmp_path, identity(tmp_path), ['-c', f'import os\nwhile True: os.write({stream}, b"x"*65536)'], limits=LIMITS)
    audit = error.value.audit
    assert audit['partial_output_only']
    assert audit['captured_bytes'] == 1024
    assert audit['observed_bytes_lower_bound'] == 1025
    assert sum(len(base64.b64decode(audit[key])) for key in ('stdout_base64', 'stderr_base64')) == 1024


def test_wall_limit_terminates_invocation_with_detached_descendant(tmp_path):
    started = time.monotonic()
    with pytest.raises(ExecutionFailure, match='WALL_TIME_LIMIT'):
        run(tmp_path, identity(tmp_path), ['-c', 'import os,time\nif os.fork()==0:\n os.setsid(); time.sleep(30)\nelse:\n time.sleep(30)'],
            limits=replace(LIMITS, wall_seconds=1))
    assert time.monotonic() - started < 4


def test_namespace_exit_removes_descendant_holding_pipe(tmp_path):
    started = time.monotonic()
    result = run(tmp_path, identity(tmp_path), ['-c',
        'import os,time\nif os.fork()==0:\n os.setsid(); time.sleep(30)\nelse:\n os._exit(0)'], limits=LIMITS)
    assert result.returncode == 0
    assert time.monotonic() - started < 2


def test_cpu_and_address_space_limits_are_enforced_in_real_namespace(tmp_path):
    cpu = run(tmp_path, identity(tmp_path), ['-c', 'while True: pass'], limits=LIMITS)
    assert cpu.returncode != 0  # Not an output or wall timeout; child killed by RLIMIT_CPU.
    memory = run(tmp_path, identity(tmp_path), ['-c', 'x=bytearray(256*1024**2)'], limits=LIMITS)
    assert memory.returncode != 0 and 'MemoryError' in memory.stderr
    bound = run(tmp_path, identity(tmp_path), ['-c',
        'import resource,json; print(json.dumps([resource.getrlimit(resource.RLIMIT_CPU),resource.getrlimit(resource.RLIMIT_AS),resource.getrlimit(resource.RLIMIT_CORE)]))'], limits=LIMITS)
    assert json.loads(bound.stdout) == [[1, 1], [128*1024**2, 128*1024**2], [0, 0]]


def test_binary_output_is_retained_without_lossy_success(tmp_path):
    with pytest.raises(ExecutionFailure, match='INVALID_UTF8_OUTPUT') as error:
        run(tmp_path, identity(tmp_path), ['-c', 'import os; os.write(1,b"\\xff")'], limits=LIMITS)
    assert base64.b64decode(error.value.audit['stdout_base64']) == b'\xff'


@pytest.mark.parametrize('field,value', [('wall_seconds', True), ('wall_seconds', 61),
    ('cpu_seconds_per_process', 0), ('address_space_bytes_per_process', 1), ('combined_output_bytes', 0)])
def test_invalid_budgets_rejected(field, value):
    with pytest.raises(ValueError, match='explicit local limit'):
        replace(LIMITS, **{field: value})


def test_broker_retains_limits_overflow_and_no_replay(tmp_path):
    workspace = tmp_path / 'job'
    workspace.mkdir()
    b = ToolBroker(workspace, identity(workspace), tmp_path / 'events', max_calls=2, limits=LIMITS)
    with pytest.raises(ExecutionFailure, match='OUTPUT_LIMIT'):
        b.call('flood', COMPUTE, {'code': 'print("x"*4096)'})
    intent = json.loads((b.events / 'flood.intent.json').read_text())
    terminal = json.loads((b.events / 'flood.result.json').read_text())
    assert intent['request'] == terminal['request']
    assert intent['request']['local_limits']['combined_output_bytes'] == 1024
    assert terminal['status'] == 'TECHNICAL_FAILURE' and terminal['result'] is None
    assert terminal['execution_audit']['partial_output_only']
    with pytest.raises(ValueError, match='no replay'):
        b.call('flood', COMPUTE, {'code': 'print(1)'})
    # A distinct call is allowed by the test budget, never a replacement for 'flood'.
    assert b.call('arithmetic', COMPUTE, {'code': 'print(3+4)'})['result']['stdout'] == '7\n'


def test_read_preserves_full_visible_access_outside_subprocess_output_budget(tmp_path):
    workspace = tmp_path / 'job'
    workspace.mkdir()
    text = 'α' * 4096
    (workspace / 'visible.txt').write_text(text)
    b = ToolBroker(workspace, identity(workspace), tmp_path / 'events', max_calls=1, limits=LIMITS)
    result = b.call('read', READ, {'path': 'visible.txt', 'offset': 0, 'length': None})
    assert result['result']['text'] == text and result['result']['eof']
    assert tool_definitions('B0') == tool_definitions('B1') == []
    assert tool_definitions('B2') == tool_definitions('B3') == tool_definitions('B4')


def test_actual_staged_primitive_tool_runs_through_broker(tmp_path):
    import build_evidence_calibration_five_method_packet_candidate as candidate
    from build_evidence_calibration_method_packets import build
    from inspect_evidence_calibration_packet import summarize
    from stage_evidence_calibration_workspace import staged_workspace
    diagnostic = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json").read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    entry = candidate.materialize(diagnostic,"test-configuration","measured_response_recovery",catalog)[-1]
    packets = build(entry,candidate.execution_contract(entry,diagnostic))
    packet = next(p for p in packets["method_packets"] if p["method_id"] == "B2")
    with staged_workspace(entry,packet) as (workspace,bound):
        b = ToolBroker(workspace,bound,tmp_path / "real-events",max_calls=2,limits=replace(LIMITS, combined_output_bytes=1024**2))
        r = b.call("tool",COMPUTE,{"code":"import runpy,sys; sys.argv=['inventory','robot_visible/evidence.json']; runpy.run_path('tools/inspect_evidence_calibration_packet.py',run_name='__main__')"})
        assert json.loads(r["result"]["stdout"]) == summarize(entry["method_packet"])
        with pytest.raises(ValueError):
            b.call("contract",READ,{"path":"contracts/claim_contracts.json","offset":0,"length":None})
