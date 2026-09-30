import io
import os
from pathlib import Path
import sys
import tarfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from audit_evidence_calibration_runtime_tree import inventory
from build_evidence_calibration_runtime_snapshot import export,verify_archive,BoundedWriter,_mtime


def fixture(tmp_path):
    root=tmp_path/'runtime';root.mkdir();(root/'empty').mkdir()
    (root/'a').write_bytes(b'full file bytes');os.link(root/'a',root/'b')
    (root/'link').symlink_to('/outside/not-followed')
    return root,inventory(root)


def test_exact_snapshot_preserves_hardlinks_symlinks_modes_and_source_mtimes(tmp_path):
    root,record=fixture(tmp_path);stream=io.BytesIO();export(root,record,stream)
    path=tmp_path/'runtime.tar';path.write_bytes(stream.getvalue())
    result=verify_archive(path,record)
    assert result['validated_members']==5 and result['inventory_sha256']==record['inventory_sha256']
    with tarfile.open(path) as archive:
        assert archive.getmember('usr/b').islnk()
        assert archive.getmember('usr/b').linkname=='usr/a'
        assert archive.getmember('usr/link').linkname=='/outside/not-followed'
        assert archive.getmember('usr/a').pax_headers['mtime']==_mtime((root/'a').stat().st_mtime_ns)
    repeated=io.BytesIO();export(root,record,repeated);assert repeated.getvalue()==stream.getvalue()


def test_content_changes_and_extra_paths_fail_without_updating_expected_identity(tmp_path):
    root,record=fixture(tmp_path);(root/'a').write_bytes(b'changed bytes!!')
    with pytest.raises(ValueError,match='content differs'):export(root,record,io.BytesIO())
    record=inventory(root)
    (root/'extra').mkdir()
    with pytest.raises(ValueError,match='metadata/paths differ'):export(root,record,io.BytesIO())


@pytest.mark.parametrize('problem',['omit','duplicate','outside','wrong-bytes','wrong-mode'])
def test_archive_verification_rejects_incomplete_or_changed_material(tmp_path,problem):
    root,record=fixture(tmp_path);raw=io.BytesIO();export(root,record,raw);raw.seek(0)
    entries=[]
    with tarfile.open(fileobj=raw) as archive:
        for member in archive:
            payload=archive.extractfile(member).read() if member.isfile() else None
            entries.append((member,payload))
    if problem=='omit':entries=entries[:-1]
    if problem=='duplicate':entries.append(entries[0])
    if problem=='outside':entries[0][0].name='../outside'
    if problem=='wrong-mode':entries[0][0].mode=0
    if problem=='wrong-bytes':
        for member,payload in entries:
            if member.isfile():
                replacement=b'x'*len(payload);entries[entries.index((member,payload))]=(member,replacement);break
    path=tmp_path/'bad.tar'
    with tarfile.open(path,'w',format=tarfile.PAX_FORMAT) as archive:
        for member,payload in entries:archive.addfile(member,io.BytesIO(payload) if payload is not None else None)
    with pytest.raises(ValueError):verify_archive(path,record)


def test_output_budget_and_negative_nanosecond_format():
    stream=io.BytesIO();out=BoundedWriter(stream,2);out.write(b'ab')
    with pytest.raises(ValueError,match='byte budget'):out.write(b'c')
    assert stream.getvalue()==b'ab'
    assert _mtime(-1)=='-0.000000001'


def test_binary_extended_attributes_are_preserved_in_archive_headers(tmp_path):
    root,record=fixture(tmp_path)
    os.setxattr(root/'a','user.crane-test',b'\x00\xffsnapshot')
    stream=io.BytesIO();export(root,record,stream);path=tmp_path/'runtime.tar';path.write_bytes(stream.getvalue())
    with tarfile.open(path) as archive:
        encoded=archive.getmember('usr/a').pax_headers['SCHILY.xattr.user.crane-test']
        assert encoded.encode('utf-8','surrogateescape')==b'\x00\xffsnapshot'
    assert verify_archive(path,record)['entries_with_extended_attributes']==2


@pytest.mark.parametrize('bad_tail',['truncated','extra-material'])
def test_complete_archive_end_framing_is_required(tmp_path,bad_tail):
    root,record=fixture(tmp_path);stream=io.BytesIO();export(root,record,stream)
    payload=stream.getvalue()
    if bad_tail=='extra-material':payload+=b'x'*512
    else:
        with tarfile.open(fileobj=io.BytesIO(payload),mode='r|') as archive:
            list(archive);end=archive.offset
        payload=payload[:end+512]
    path=tmp_path/'bad-framing.tar';path.write_bytes(payload)
    with pytest.raises(ValueError):verify_archive(path,record)
