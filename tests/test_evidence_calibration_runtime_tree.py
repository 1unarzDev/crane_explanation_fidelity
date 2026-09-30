from pathlib import Path
import os
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'analysis'))
from audit_evidence_calibration_runtime_tree import inventory, verify, validate, summary
from evidence_calibration_io import canonical_sha256


def tree(tmp_path):
    root = tmp_path / 'runtime'; root.mkdir()
    (root / 'bin').mkdir(); (root / 'bin/tool').write_bytes(b'abc')
    (root / 'empty').mkdir()
    (root / 'link').symlink_to('/synthetic/outside')
    return root


def test_full_identity_and_verification_are_deterministic_without_following_links(tmp_path):
    root = tree(tmp_path)
    record = inventory(root)
    assert inventory(root) == record
    verify(root, record)
    assert record['entries']['link']['target'] == '/synthetic/outside'
    assert summary(record)['entry_counts'] == {'file': 1, 'directory': 2, 'symlink': 1}
    assert summary(record)['regular_file_bytes'] == 3


@pytest.mark.parametrize('change', ['content', 'mode', 'add', 'remove', 'link', 'empty-directory'])
def test_byte_and_metadata_changes_fail_verification(tmp_path, change):
    root = tree(tmp_path); record = inventory(root); tool = root / 'bin/tool'
    if change == 'content':
        before = tool.stat(); tool.write_bytes(b'xyz'); os.utime(tool, ns=(before.st_atime_ns,before.st_mtime_ns))
    elif change == 'mode':tool.chmod(0o700)
    elif change == 'add':(root / 'new').write_bytes(b'new')
    elif change == 'remove':tool.unlink()
    elif change == 'link':(root / 'link').unlink();(root / 'link').symlink_to('/different')
    else:(root / 'empty').rmdir()
    with pytest.raises(ValueError, match='differs'):
        verify(root, record)


def test_special_file_and_symlink_root_rejected(tmp_path):
    root = tree(tmp_path);os.mkfifo(root / 'fifo')
    with pytest.raises(ValueError, match='special file'):inventory(root)
    link=tmp_path/'root-link';link.symlink_to(root,target_is_directory=True)
    with pytest.raises(OSError):inventory(link)


def test_change_to_previously_hashed_file_is_detected_before_completion(tmp_path, monkeypatch):
    import audit_evidence_calibration_runtime_tree as module
    root=tree(tmp_path);original=module._scan
    def scan(path, *, hash_contents, progress=None):
        result=original(path,hash_contents=hash_contents,progress=progress)
        if hash_contents:(root/'bin/tool').write_bytes(b'xyz')
        return result
    monkeypatch.setattr(module,'_scan',scan)
    with pytest.raises(ValueError,match='no stable identity'):module.inventory(root)


def test_inventory_hash_and_path_structure_cannot_be_silently_changed(tmp_path):
    record=inventory(tree(tmp_path));record['entries']['bin/tool']['raw_sha256']='0'*64
    with pytest.raises(ValueError,match='hash mismatch'):validate(record)
    record['entries']['../escape']=record['entries'].pop('bin/tool')
    record['inventory_sha256']=canonical_sha256({k:v for k,v in record.items() if k!='inventory_sha256'})
    with pytest.raises(ValueError,match='relative path'):validate(record)


def test_unreadable_file_is_not_omitted_or_treated_as_empty(tmp_path):
    if os.geteuid() == 0:
        pytest.skip('permission regression requires an unprivileged reader')
    root=tree(tmp_path);protected=root/'bin/tool';protected.chmod(0)
    try:
        with pytest.raises(PermissionError,match='bin/tool'):
            inventory(root)
    finally:
        protected.chmod(0o600)


def test_directory_symlink_race_cannot_redirect_hashing_outside_root(tmp_path, monkeypatch):
    import audit_evidence_calibration_runtime_tree as module
    root=tree(tmp_path);outside=tmp_path/'outside';outside.mkdir();(outside/'secret').write_bytes(b'synthetic')
    original=module.os.open
    redirected=False
    def opened(path,flags,*args,**kwargs):
        nonlocal redirected
        if path=='bin' and kwargs.get('dir_fd') is not None and not redirected:
            redirected=True
            (root/'bin').rename(root/'old-bin')
            (root/'bin').symlink_to(outside,target_is_directory=True)
        return original(path,flags,*args,**kwargs)
    monkeypatch.setattr(module.os,'open',opened)
    with pytest.raises(OSError):module.inventory(root)
    assert redirected
