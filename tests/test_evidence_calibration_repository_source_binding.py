import hashlib
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from evidence_calibration_repository_source_binding import repository_source_hashes


def test_transitive_nested_imports_cycles_and_launch_script_are_bound(tmp_path):
    sources = {'entry.py': 'import child\ndef f():\n import deferred\n',
               'child.py': 'from grandchild import x\n',
               'grandchild.py': 'import entry\nx = 1\n',
               'deferred.py': 'import json\n', 'wrapper.py': 'print(1)\n'}
    for name, content in sources.items():
        (tmp_path / name).write_text(content)
    assert repository_source_hashes(tmp_path, ('entry.py', 'wrapper.py')) == {
        name: hashlib.sha256(content.encode()).hexdigest() for name, content in sorted(sources.items())}


@pytest.mark.parametrize('mutation', ['bytes', 'added_import', 'deleted_dependency'])
def test_dependency_changes_alter_binding(tmp_path, mutation):
    (tmp_path / 'entry.py').write_text('import child\n')
    (tmp_path / 'child.py').write_text('x = 1\n')
    before = repository_source_hashes(tmp_path, ('entry.py',))
    if mutation == 'bytes':
        (tmp_path / 'child.py').write_text('x = 2\n')
    elif mutation == 'added_import':
        (tmp_path / 'child.py').write_text('import other\n')
        (tmp_path / 'other.py').write_text('x = 1\n')
    else:
        (tmp_path / 'child.py').unlink()
    assert repository_source_hashes(tmp_path, ('entry.py',)) != before


@pytest.mark.parametrize('kind', ['symlink', 'dangling_symlink', 'fifo'])
def test_nonregular_import_is_rejected_without_blocking(tmp_path, kind):
    (tmp_path / 'entry.py').write_text('import child\n')
    path = tmp_path / 'child.py'
    if kind == 'fifo':
        os.mkfifo(path)
    else:
        path.symlink_to(tmp_path / ('entry.py' if kind == 'symlink' else 'missing.py'))
    with pytest.raises((OSError, ValueError)):
        repository_source_hashes(tmp_path, ('entry.py',))


@pytest.mark.parametrize('content', ['from . import child', 'import child.part', 'import package'])
def test_unsupported_local_import_layout_fails_closed(tmp_path, content):
    (tmp_path / 'entry.py').write_text(content)
    (tmp_path / 'child.py').write_text('x = 1')
    (tmp_path / 'package').mkdir()
    with pytest.raises(ValueError, match='binding support'):
        repository_source_hashes(tmp_path, ('entry.py',))


@pytest.mark.parametrize('roots', [(), ('entry.py', 'entry.py'), ('../entry.py',)])
def test_missing_duplicate_and_escaping_roots_rejected(tmp_path, roots):
    with pytest.raises(ValueError):
        repository_source_hashes(tmp_path, roots)


def test_current_coordinator_binds_helpers_and_namespace_launch_script():
    from evidence_calibration_condition_session_v6 import source_hashes
    hashes = source_hashes()
    assert len(hashes) > 6
    for name in ['evidence_calibration_io.py', 'evidence_calibration_local_tool_sandbox_v2.py',
                 'evidence_calibration_namespace_wrapper.py',
                 'observe_evidence_calibration_cgroup_limits.py',
                 'run_evidence_calibration_claim_role_v2r2_qualification.py']:
        assert hashes[name] == hashlib.sha256((ROOT / 'analysis' / name).read_bytes()).hexdigest()


@pytest.mark.parametrize('dependency', ['evidence_calibration_io.py', 'evidence_calibration_namespace_wrapper.py'])
def test_preserved_six_file_binding_misses_drift_new_plan_rejects_before_owner(
        tmp_path, monkeypatch, dependency):
    import evidence_calibration_condition_session_v5 as old
    import evidence_calibration_condition_session_v6 as new
    from test_evidence_calibration_condition_session_v6 import configurations
    source_dir = tmp_path / 'sources'
    source_dir.mkdir()
    names = set(new.source_hashes()) | set(old.source_hashes())
    for name in names:
        (source_dir / name).write_bytes((ROOT / 'analysis' / name).read_bytes())
    monkeypatch.setattr(old, '__file__', str(source_dir / 'evidence_calibration_condition_session_v5.py'))
    monkeypatch.setattr(new, '__file__', str(source_dir / 'evidence_calibration_condition_session_v6.py'))
    baseline = old.source_hashes()
    case = tmp_path / 'case'
    case.mkdir()
    configuration = configurations(case)[0]
    path = source_dir / dependency
    path.write_bytes(path.read_bytes() + b'\n# synthetic dependency drift\n')
    assert old.source_hashes() == baseline
    assert new.source_hashes()[dependency] != configuration_source(configuration, dependency)
    with pytest.raises(ValueError, match='source'):
        new.claim(configuration)
    assert not list((case / 'registry').glob('*/session-owner.intent.json'))
    assert not Path(configuration['records']).exists()


def configuration_source(configuration, dependency):
    import json
    return json.loads(Path(configuration['execution_plan']).read_text())['source_sha256'][dependency]


def test_file_byte_limit_rejected(tmp_path):
    (tmp_path / 'entry.py').write_bytes(b'#' + b'x' * (8 * 1024**2))
    with pytest.raises(ValueError, match='byte limit'):
        repository_source_hashes(tmp_path, ('entry.py',))


def test_closure_file_limit_rejected(tmp_path):
    for index in range(513):
        (tmp_path / f'source_{index}.py').write_text(
            f'import source_{index+1}\n' if index < 512 else '')
    with pytest.raises(ValueError, match='file limit'):
        repository_source_hashes(tmp_path, ('source_0.py',))


def test_observation_retains_failure_and_rejects_reuse_without_model_or_service(tmp_path, monkeypatch):
    import json
    import observe_evidence_calibration_repository_source_binding as observer
    def fail(*args):
        raise OSError('synthetic pre-server failure')
    monkeypatch.setattr(observer.candidate, 'serve', fail)
    directory = tmp_path / 'observation'
    with pytest.raises(OSError, match='pre-server'):
        observer.observe(directory)
    record = json.loads((directory / 'observation.error.json').read_text())
    assert record['status'] == 'FAILED_NO_RETRY'
    assert not list(directory.glob('B*/events'))
    with pytest.raises(FileExistsError):
        observer.observe(directory)
