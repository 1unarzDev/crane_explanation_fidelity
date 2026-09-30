import base64
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from evidence_calibration_local_tool_sandbox_v2 import Limits, ExecutionFailure, command as old_command
from evidence_calibration_local_tool_sandbox_v4 import TreeLimits, command, run
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory

LOCAL = Limits(3, 2, 256 * 1024**2, 1024)
TREE = TreeLimits(64 * 1024**2, 16, 100)


def bound(workspace):
    result = {'inventory': inventory(workspace)}
    result['workspace_sha256'] = canonical_sha256(result)
    return result


def execute(tmp_path, code, **kwargs):
    workspace = tmp_path / 'work'
    workspace.mkdir()
    events = tmp_path / 'events'
    result = run(workspace, bound(workspace), ['-c', code], limits=kwargs.get('limits', LOCAL),
                 tree_limits=TREE, event_directory=events)
    return result, events


def test_exact_unicode_output_and_boundary(tmp_path):
    result, events = execute(tmp_path, 'import os; os.write(1,b"a"*512); os.write(2,b"b"*512)')
    assert result.stdout == 'a' * 512 and result.stderr == 'b' * 512
    terminal = json.loads((events / 'terminal.json').read_text())
    assert terminal['status'] == 'RETURNED' and not terminal['execution_audit']['partial_output_only']
    assert terminal['cleanup']['final_state']['stdout'].strip() == 'not-found'


@pytest.mark.parametrize('stream', [1, 2])
def test_flood_bounded_and_service_removed(tmp_path, stream):
    with pytest.raises(ExecutionFailure, match='OUTPUT_LIMIT') as caught:
        execute(tmp_path, f'import os\nwhile True: os.write({stream}, b"x"*65536)')
    terminal = caught.value.audit
    audit = terminal['execution_audit']
    assert audit['captured_bytes'] == 1024 and audit['observed_bytes_lower_bound'] == 1025
    assert sum(len(base64.b64decode(audit[k])) for k in ('stdout_base64', 'stderr_base64')) == 1024
    assert terminal['result'] is None and terminal['status'] == 'TECHNICAL_FAILURE'
    assert terminal['cleanup']['final_state']['stdout'].strip() == 'not-found'


def test_memory_oom_is_technical_failure_not_returned_output(tmp_path):
    with pytest.raises(ExecutionFailure, match='PROCESS_TREE_OOM') as caught:
        execute(tmp_path, 'x=bytearray(128*1024**2)')
    assert caught.value.audit['result'] is None
    assert 'Result=oom-kill' in caught.value.audit['unit_state']['stdout']


def test_wall_cleanup_removes_detached_descendant(tmp_path):
    with pytest.raises(ExecutionFailure, match='WALL_TIME_LIMIT|SERVICE_WALL_TIME_LIMIT') as caught:
        execute(tmp_path, 'import os,time\nif os.fork()==0: os.setsid()\ntime.sleep(20)',
                limits=replace(LOCAL, wall_seconds=1))
    assert caught.value.audit['cleanup']['final_state']['stdout'].strip() == 'not-found'


def test_binary_output_no_lossy_success(tmp_path):
    with pytest.raises(ExecutionFailure, match='INVALID_UTF8_OUTPUT') as caught:
        execute(tmp_path, 'import os; os.write(1,b"\\xff")')
    assert base64.b64decode(caught.value.audit['execution_audit']['stdout_base64']) == b'\xff'


def test_nonzero_program_exit_is_preserved_runtime_failure(tmp_path):
    result, events = execute(tmp_path, "raise RuntimeError('synthetic')")
    assert result.returncode != 0 and 'synthetic' in result.stderr
    assert json.loads((events / 'terminal.json').read_text())['status'] == 'TOOL_RUNTIME_FAILURE'


def test_existing_event_directory_blocks_relaunch(tmp_path):
    workspace = tmp_path / 'work'; workspace.mkdir()
    events = tmp_path / 'events'; events.mkdir()
    with pytest.raises(FileExistsError):
        run(workspace, bound(workspace), ['-c', 'print(1)'], limits=LOCAL, tree_limits=TREE, event_directory=events)


def test_method_workspace_cannot_hold_event_directory(tmp_path):
    with pytest.raises(ValueError, match='outside'):
        run(tmp_path, bound(tmp_path), ['-c', 'pass'], limits=LOCAL, tree_limits=TREE, event_directory=tmp_path/'events')


def test_namespace_suffix_is_unchanged(tmp_path):
    unit = 'crane-compute-' + 'a' * 32
    argv = command(tmp_path, bound(tmp_path), ['-c', 'pass'], LOCAL, TREE, unit)
    assert argv[argv.index('/usr/bin/bwrap'):] == old_command(tmp_path, bound(tmp_path), ['-c', 'pass'], LOCAL)


@pytest.mark.parametrize('field,value', [('memory_bytes', 1), ('tasks', True), ('tasks', 7),
                                        ('cpu_rate_percent', 0), ('cpu_rate_percent', 401)])
def test_invalid_tree_budgets_fail_before_launch(field, value):
    with pytest.raises(ValueError, match='tree limit'):
        replace(TREE, **{field: value})


def test_missing_service_disposition_is_technical_failure(tmp_path, monkeypatch):
    import evidence_calibration_local_tool_sandbox_v4 as module
    original = module._control
    def control(environment, unit, *arguments):
        if '--property=LoadState,Result,ActiveState' in arguments:
            return {'return_code': 0, 'stdout': 'LoadState=not-found\nResult=success\n', 'stderr': ''}
        return original(environment, unit, *arguments)
    monkeypatch.setattr(module, '_control', control)
    with pytest.raises(ExecutionFailure, match='UNIT_START_OR_DISPOSITION_UNVERIFIED'):
        execute(tmp_path, 'raise RuntimeError("synthetic")')


def test_unverified_cleanup_suppresses_completed_output(tmp_path, monkeypatch):
    import evidence_calibration_local_tool_sandbox_v4 as module
    original = module._control
    def control(environment, unit, *arguments):
        if '--property=LoadState' in arguments:
            return {'return_code': 0, 'stdout': 'loaded\n', 'stderr': ''}
        return original(environment, unit, *arguments)
    monkeypatch.setattr(module, '_control', control)
    with pytest.raises(ExecutionFailure, match='SERVICE_CLEANUP_UNVERIFIED') as caught:
        execute(tmp_path, 'print("synthetic")')
    assert caught.value.audit['result'] is None
    assert caught.value.audit['execution_audit']['partial_output_only']


def test_systemd_preserves_literal_dollar_percent_unicode_and_newline_arguments(tmp_path):
    text = '%n $HOME ${HOME} $$ αβ\nnext'
    result, events = execute(tmp_path, 'print(' + repr(text) + ')')
    assert result.stdout == text + '\n' and not result.stderr


def test_v4_changes_only_systemd_argument_expansion():
    original = (ROOT / 'analysis/evidence_calibration_local_tool_sandbox_v3.py').read_text()
    expected = original.replace("'--quiet', '--wait', '--pipe', '--unit=' + unit,",
                                "'--quiet', '--wait', '--pipe', '--expand-environment=no', '--unit=' + unit,")
    assert (ROOT / 'analysis/evidence_calibration_local_tool_sandbox_v4.py').read_text() == expected
