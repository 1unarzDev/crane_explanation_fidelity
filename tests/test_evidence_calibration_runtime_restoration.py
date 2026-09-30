import io
import os
from pathlib import Path
import sys
import tarfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from audit_evidence_calibration_runtime_tree import inventory
from build_evidence_calibration_runtime_snapshot import export
from verify_evidence_calibration_runtime_restoration import verify


def fixture(tmp_path):
    root=tmp_path/'usr';root.mkdir();(root/'empty').mkdir();(root/'file').write_bytes(b'synthetic')
    os.link(root/'file',root/'hard');(root/'link').symlink_to('/outside/not-followed')
    os.setxattr(root/'file','user.crane',b'\xfftest')
    expected=inventory(root);raw=io.BytesIO();export(root,expected,raw)
    archive=tmp_path/'runtime.tar';archive.write_bytes(raw.getvalue())
    return root,expected,archive


def test_source_and_archive_metadata_match(tmp_path):
    root,expected,archive=fixture(tmp_path)
    result=verify(root,archive,expected)
    assert result['members_checked']==5 and result['hardlinks_checked']==1
    assert result['entries_with_extended_attributes']==2
    assert result['execution_parity_verified'] is False


@pytest.mark.parametrize('change',['mtime','xattr','hardlink','content','owner-mode'])
def test_restoration_differences_cannot_be_silently_accepted(tmp_path,change):
    root,expected,archive=fixture(tmp_path)
    if change=='mtime':os.utime(root/'file',ns=(0,0))
    elif change=='xattr':os.setxattr(root/'file','user.crane',b'different')
    elif change=='hardlink':
        before=(root/'hard').stat();(root/'hard').unlink();(root/'hard').write_bytes(b'synthetic')
        os.setxattr(root/'hard','user.crane',b'\xfftest');os.utime(root/'hard',ns=(before.st_atime_ns,before.st_mtime_ns))
    elif change=='content':(root/'file').write_bytes(b'changed')
    else:(root/'file').chmod(0o700)
    with pytest.raises(ValueError):verify(root,archive,expected)


def test_container_setgid_restoration_requires_declared_fsetid_capability(tmp_path):
    import subprocess
    from observe_evidence_calibration_container_runtime_audit import IMAGE
    result_modes=[]
    for suffix,extra in [('without',[]),('with',['--cap-add','FSETID'])]:
        destination=tmp_path/suffix;destination.mkdir()
        code="import os,stat; p='/restore/file'; open(p,'wb').write(b'synthetic'); os.chown(p,0,5); os.chmod(p,0o2755); print(oct(stat.S_IMODE(os.stat(p).st_mode)))"
        argv=['docker','run','--rm','--pull=never','--network','none','--read-only','--cap-drop','ALL',
              '--cap-add','DAC_OVERRIDE','--cap-add','CHOWN','--cap-add','FOWNER',*extra,'--security-opt','no-new-privileges',
              '--mount','type=bind,source='+str(destination)+',target=/restore',
              IMAGE,'python','-I','-S','-B','-c',code]
        result=subprocess.run(argv,capture_output=True,text=True,check=True,timeout=10)
        result_modes.append(result.stdout.strip())
    assert result_modes==['0o755','0o2755']
