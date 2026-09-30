import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from audit_evidence_calibration_runtime_tree import inventory
from observe_evidence_calibration_container_runtime_audit import command, observe, IMAGE, source_closure


def test_code_closure_contains_only_declared_python_sources_and_no_data():
    files=source_closure()
    assert 'audit_evidence_calibration_runtime_tree.py' in files
    assert all(name.endswith('.py') and '/' not in name for name in files)
    for name,content in files.items():
        assert content==(ROOT/'analysis'/name).read_bytes()


def test_actual_container_hashes_unreadable_fixture_and_leaves_runtime_unchanged():
    with tempfile.TemporaryDirectory(prefix='crane-root-reader-test-') as temporary:
        base=Path(temporary);runtime=base/'runtime';runtime.mkdir()
        file=runtime/'protected';file.write_bytes(b'synthetic protected runtime bytes');file.chmod(0)
        (runtime/'empty').mkdir();(runtime/'outside-link').symlink_to('/not-followed')
        try:
            record=observe(runtime,base/'observation')
            assert record['terminal']['status']=='COMPLETE_CONTENT_OBSERVATION_LIVE_RUNTIME_NOT_FROZEN'
            assert record['terminal']['container_removed_or_absent']
            assert record['request']['capabilities']==['DAC_READ_SEARCH']
            captured=json.loads((base/'observation/inventory.json').read_text())
            assert captured['entries']['protected']['raw_sha256']==hashlib.sha256(b'synthetic protected runtime bytes').hexdigest()
            assert captured['entries']['protected']['mode']==0
            assert captured['entries']['outside-link']['target']=='/not-followed'
            assert file.stat().st_mode & 0o7777 == 0
            assert record['terminal']['model_call_attempted'] is False
            with pytest.raises(ValueError,match='fresh'):
                observe(runtime,base/'observation')
        finally:file.chmod(0o600)


def test_mounts_are_readonly_and_image_reference_is_immutable():
    argv=command(Path('/usr'),Path('/tmp/synthetic-code'),'synthetic-name','0'*64)
    assert IMAGE in argv and '@sha256:' in IMAGE
    assert '--pull=never' in argv and '--read-only' in argv
    assert argv[argv.index('--network')+1]=='none'
    assert argv[argv.index('--cap-add')+1]=='DAC_READ_SEARCH'
    assert all(item.endswith(',readonly') for item in argv if item.startswith('type=bind,'))
    assert not any('docker.sock' in item for item in argv)


def test_daemon_inspection_failure_does_not_become_verified_absence(monkeypatch):
    import observe_evidence_calibration_container_runtime_audit as module
    with tempfile.TemporaryDirectory(prefix='crane-cleanup-failure-test-') as temporary:
        base=Path(temporary);runtime=base/'runtime';runtime.mkdir();(runtime/'file').write_bytes(b'abc')
        expected=inventory(runtime)
        def run(argv,**kwargs):
            if argv[1:3]==['image','inspect']:
                value={'Os':'linux','Architecture':'amd64','Id':'synthetic-image',
                       'RepoDigests':[IMAGE],'RootFS':{'Layers':[]}}
                return subprocess.CompletedProcess(argv,0,json.dumps([value]),'')
            if argv[1]=='run':
                kwargs['stdout'].write(json.dumps(expected).encode())
                return subprocess.CompletedProcess(argv,0)
            if argv[1:3]==['container','inspect']:
                return subprocess.CompletedProcess(argv,1,'','synthetic daemon unavailable')
            raise AssertionError('unexpected cleanup mutation')
        monkeypatch.setattr(module.subprocess,'run',run)
        record=module.observe(runtime,base/'observation')
        assert record['terminal']['status']=='FAILED_CLEANUP_UNKNOWN'
        assert record['terminal']['container_removed_or_absent'] is False
