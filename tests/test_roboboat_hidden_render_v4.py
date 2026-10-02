import ast
import json
from pathlib import Path

import pytest
import roboboat_hidden_render_v4 as render
from roboboat_render_fps_lease_v1 import FPSLease
import test_roboboat_hidden_render_v3 as fixtures


def mock_render(monkeypatch, tmp_path, **kw):
    monkeypatch.setattr(fixtures, 'r', render)
    calls = fixtures.mocked(monkeypatch, **kw)
    monkeypatch.setattr(render, 'FPSLease', lambda read, write: FPSLease(read, write,
        gate=tmp_path / 'gate', directory=tmp_path / 'leases',
        identity=lambda pid: {'pid': pid, 'start': 100}))
    return calls


def test_owned_handles_use_lease_and_restore_original_after_last_worker(monkeypatch, tmp_path):
    calls = mock_render(monkeypatch, tmp_path)
    path = tmp_path / 'audit.json'
    assert render.run([], probe_only=True, audit_path=path) == 0
    result = json.loads(path.read_text())
    assert result['schema'] == 'roboboat-hidden-render/v4-development'
    assert result['fps_lease']['active_owners'] == 1
    assert result['fps_lease_release']['original_restored'] is True
    assert result['fps_lease_release']['fps'] == 15
    assert result['owned_output_removed'] is True and not result['cleanup_errors']
    assert not any(command[0] == 'reload' for command in calls)


def test_other_cleanup_failure_still_releases_fps_lease(monkeypatch, tmp_path):
    mock_render(monkeypatch, tmp_path, fail_disable=True, fail_remove=True)
    path = tmp_path / 'audit.json'
    with pytest.raises(RuntimeError, match='cleanup incomplete'):
        render.run([], probe_only=True, audit_path=path)
    result = json.loads(path.read_text())
    assert len(result['cleanup_errors']) == 2
    assert result['fps_lease_release']['original_restored'] is True


def test_unqualified_class_rejected_before_lease_or_compositor_mutation(monkeypatch):
    monkeypatch.setenv('HYPRLAND_INSTANCE_SIGNATURE', 'test')
    monkeypatch.setattr(render, 'hypr', lambda *args: pytest.fail('premature compositor mutation'))
    monkeypatch.setattr(render, 'FPSLease', lambda *args: pytest.fail('premature lease construction'))
    with pytest.raises(ValueError, match='nonce class'):
        render.run(['player'], expected_class='CRANE.x86_64')


def test_process_and_window_ownership_helpers_are_identical_to_qualified_v3():
    root = Path(render.__file__).parent
    def functions(path):
        return {f.name: ast.dump(f) for f in ast.parse(path.read_text()).body if isinstance(f, ast.FunctionDef)}
    a, b = functions(root / 'roboboat_hidden_render_v3.py'), functions(root / 'roboboat_hidden_render_v4.py')
    for name in ('hypr', 'state', 'process_records', 'group_owned_pid', 'cleanup_group', 'owned_window'):
        assert a[name] == b[name]
