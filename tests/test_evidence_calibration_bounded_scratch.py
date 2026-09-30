import errno
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_local_tool_sandbox_v6 import ScratchLimits,TreeLimits,run,bounded_namespace_command
from evidence_calibration_local_tool_sandbox_v2 import Limits,command as old_command
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory

LOCAL=Limits(3,2,256*1024**2,8192)
TREE=TreeLimits(64*1024**2,16,100)
SCRATCH=ScratchLimits(1024**2,1024**2)


def bound(w):
    b={'inventory':inventory(w)};b['workspace_sha256']=canonical_sha256(b);return b


def execute(tmp_path,code):
    w=tmp_path/'workspace';w.mkdir()
    r=run(w,bound(w),['-c',code],limits=LOCAL,tree_limits=TREE,scratch_limits=SCRATCH,event_directory=tmp_path/'events')
    assert r.returncode==0,r.stderr
    return json.loads(r.stdout)


def test_registered_scratch_capacity_and_readonly_other_data_mounts(tmp_path):
    rows=execute(tmp_path,'''import json,os,pathlib
rows={}
for name in ['/', '/tmp', '/dev', '/dev/shm']:
 p=pathlib.Path(name);info=os.statvfs(name);r={'capacity_bytes':info.f_blocks*info.f_frsize}
 try:
  file=p/'probe';file.write_bytes(b'x');file.unlink();r['write']=True
 except OSError as e:r['write']=False;r['errno']=e.errno
 rows[name]=r
print(json.dumps(rows))''')
    assert rows['/tmp']['capacity_bytes']==rows['/dev/shm']['capacity_bytes']==1024**2
    assert rows['/tmp']['write'] and rows['/dev/shm']['write']
    assert rows['/']['errno']==rows['/dev']['errno']==errno.EROFS


def test_each_scratch_mount_exhausts_at_registered_capacity(tmp_path):
    rows=execute(tmp_path,'''import json,os
rows={}
for path in ['/tmp/full','/dev/shm/full']:
 fd=os.open(path,os.O_WRONLY|os.O_CREAT,0o600);total=0
 try:
  for _ in range(24): total+=os.write(fd,b'x'*65536)
 except OSError as e:rows[path]={'errno':e.errno,'bytes_written':total}
 finally:os.close(fd)
print(json.dumps(rows))''')
    assert set(rows)=={'/tmp/full','/dev/shm/full'}
    assert all(row['errno']==errno.ENOSPC and row['bytes_written']==1024**2 for row in rows.values())


def test_nested_user_namespace_cannot_remount_scratch(tmp_path):
    row=execute(tmp_path,'''import ctypes,json
libc=ctypes.CDLL(None,use_errno=True)
r=libc.unshare(0x10000000)
print(json.dumps({'return':r,'errno':ctypes.get_errno()}))''')
    # Bubblewrap disables further user namespaces via the namespace quota.
    assert row=={'return':-1,'errno':errno.ENOSPC}


def test_device_null_and_literal_arithmetic_remain_usable(tmp_path):
    row=execute(tmp_path,'''import json
with open('/dev/null','wb') as f:f.write(b'fixed')
print(json.dumps({'literal':'%n ${HOME} $$ α','arithmetic':sum(range(11))}))''')
    assert row=={'literal':'%n ${HOME} $$ α','arithmetic':55}


def test_sources_and_interpreter_arguments_are_unchanged(tmp_path):
    old=old_command(tmp_path,bound(tmp_path),['-c','pass'],LOCAL)
    new=bounded_namespace_command(tmp_path,bound(tmp_path),['-c','pass'],LOCAL,SCRATCH)
    assert new[new.index('--'):] == old[old.index('--'):]
    assert new[new.index('--ro-bind'):new.index('--ro-bind')+3] == old[old.index('--ro-bind'):old.index('--ro-bind')+3]
    assert '--disable-userns' in new and '--unshare-user' in new


@pytest.mark.parametrize('value',[True,0,65537,4096,512*1024**2])
def test_invalid_scratch_limits_rejected(value):
    with pytest.raises(ValueError,match='scratch limit'):
        ScratchLimits(value,1024**2)


def test_v6_only_adds_explicit_user_namespace_to_retained_v5():
    old=(ROOT/'analysis/evidence_calibration_local_tool_sandbox_v5.py').read_text()
    expected=old.replace("argv[index:index + 2] = ['--size'", "argv.insert(1, '--unshare-user')\n    index += 1\n    argv[index:index + 2] = ['--size'")
    assert (ROOT/'analysis/evidence_calibration_local_tool_sandbox_v6.py').read_text()==expected


def test_existing_staged_primitive_retains_full_source_access(tmp_path):
    from dataclasses import replace
    import build_evidence_calibration_five_method_packet_candidate as candidate
    from build_evidence_calibration_method_packets import build
    from inspect_evidence_calibration_packet import summarize
    from stage_evidence_calibration_workspace import staged_workspace
    diagnostic=json.loads((ROOT/'data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json').read_text())
    catalog=json.loads((ROOT/candidate.CATALOG).read_text())
    entry=candidate.materialize(diagnostic,'test-config','measured_response_recovery',catalog)[-1]
    packets=build(entry,candidate.execution_contract(entry,diagnostic))
    packet=next(p for p in packets['method_packets'] if p['method_id']=='B2')
    with staged_workspace(entry,packet) as (workspace,identity):
        result=run(workspace,identity,['tools/inspect_evidence_calibration_packet.py','robot_visible/evidence.json'],
                   limits=replace(LOCAL,combined_output_bytes=1024**2),tree_limits=TREE,
                   scratch_limits=SCRATCH,event_directory=tmp_path/'primitive-event')
        assert result.returncode==0,result.stderr
        assert json.loads(result.stdout)==summarize(entry['method_packet'])
