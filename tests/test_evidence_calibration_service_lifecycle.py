from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
import evidence_calibration_local_tool_sandbox_v7 as module
from evidence_calibration_local_tool_sandbox_v2 import Limits,ExecutionFailure
from evidence_calibration_namespace_wrapper import launch
from evidence_calibration_io import canonical_sha256
from stage_evidence_calibration_workspace import inventory

LOCAL=Limits(3,2,256*1024**2,1024)
TREE=module.TreeLimits(64*1024**2,16,100)
SCRATCH=module.ScratchLimits(1024**2,1024**2)


def execute(tmp_path,code,local=LOCAL):
    w=tmp_path/'workspace';w.mkdir()
    b={'inventory':inventory(w)};b['workspace_sha256']=canonical_sha256(b)
    return module.run(w,b,['-c',code],limits=local,tree_limits=TREE,scratch_limits=SCRATCH,event_directory=tmp_path/'events')


def terminal(tmp_path):return json.loads((tmp_path/'events/terminal.json').read_text())


def test_literal_output_and_matching_final_status(tmp_path):
    r=execute(tmp_path,"print('%n ${HOME} $$ α')")
    assert r.stdout=='%n ${HOME} $$ α\n' and not r.stderr
    t=terminal(tmp_path)
    assert t['status']=='RETURNED' and t['namespace_lifecycle']['payload_exit_verified']
    request=json.loads((tmp_path/'events/namespace-request.json').read_text())
    assert request['command'][0]=='/usr/bin/bwrap'
    assert '--disable-userns' in request['command'] and '--json-status-fd' not in request['command']


def test_setup_looking_program_error_does_not_become_namespace_error(tmp_path):
    r=execute(tmp_path,"import sys; print('bwrap: synthetic mount error',file=sys.stderr);sys.exit(7)")
    assert r.returncode==7 and 'synthetic mount error' in r.stderr
    t=terminal(tmp_path)
    assert t['status']=='TOOL_RUNTIME_FAILURE' and t['namespace_lifecycle']['payload_exit_verified']
    assert not t['namespace_lifecycle']['model_failure_attributed']


@pytest.mark.parametrize('fault',['mount','exec'])
def test_namespace_setup_or_exec_failure_withholds_result(tmp_path,monkeypatch,fault):
    original=module.bounded_namespace_command
    def broken(*args):
        argv=original(*args); index=argv.index('--')
        if fault=='mount':argv[index:index]=['--ro-bind',str(tmp_path/'registered-absent'),'/absent']
        else:argv[index+1]=str(tmp_path/'registered-absent')
        return argv
    monkeypatch.setattr(module,'bounded_namespace_command',broken)
    with pytest.raises(ExecutionFailure,match='NAMESPACE_LIFECYCLE_INCOMPLETE'):
        execute(tmp_path,"print('must not execute')")
    t=terminal(tmp_path)
    assert t['status']=='TECHNICAL_FAILURE' and t['result'] is None
    assert not t['namespace_lifecycle']['payload_exit_verified']


def test_status_descriptor_is_absent_from_payload_proc_fds(tmp_path):
    r=execute(tmp_path,'''import pathlib,json
visible=[]
for d in pathlib.Path('/proc').iterdir():
 if not d.name.isdigit():continue
 try:
  for f in (d/'fd').iterdir():
   try:
    if 'namespace-status.bin' in str(f.readlink()):visible.append(f.name)
   except OSError:pass
 except OSError:pass
print(json.dumps(visible))''')
    assert json.loads(r.stdout)==[]


@pytest.mark.parametrize('raw',[b'',b'{"child-pid":1}\n',b'corrupt',b'x'*8193])
def test_empty_partial_corrupt_or_oversized_status_suppresses_output(tmp_path,monkeypatch,raw):
    original=module._control
    def control(environment,unit,*args):
        r=original(environment,unit,*args)
        if '--property=LoadState' in args:
            (tmp_path/'events/namespace-status.bin').write_bytes(raw)
        return r
    monkeypatch.setattr(module,'_control',control)
    with pytest.raises(ExecutionFailure):execute(tmp_path,'print("must be withheld")')
    assert terminal(tmp_path)['result'] is None


@pytest.mark.parametrize('code,reason',[
    ('print("x"*4096)','OUTPUT_LIMIT'),
    ('x=bytearray(128*1024**2)','PROCESS_TREE_OOM'),
    ('import os;os.write(1,b"\\xff")','INVALID_UTF8_OUTPUT')])
def test_resource_or_encoding_failures_keep_prior_disposition(tmp_path,code,reason):
    with pytest.raises(ExecutionFailure,match=reason):execute(tmp_path,code)
    t=terminal(tmp_path)
    assert t['result'] is None and t['cleanup']['final_state']['stdout'].strip()=='not-found'


def test_detached_descendant_wall_cleanup(tmp_path):
    with pytest.raises(ExecutionFailure,match='WALL_TIME_LIMIT|SERVICE_WALL_TIME_LIMIT'):
        execute(tmp_path,'import os,time\nif os.fork()==0:os.setsid()\ntime.sleep(20)',replace(LOCAL,wall_seconds=1))
    assert terminal(tmp_path)['cleanup']['final_state']['stdout'].strip()=='not-found'


def test_wrapper_request_tampering_fails_before_status_creation(tmp_path):
    p=tmp_path/'request.json';p.write_text('{}')
    with pytest.raises(ValueError,match='differ'):
        launch(p,'0'*64)
    assert not (tmp_path/'namespace-status.bin').exists()


def test_wrapper_cannot_select_status_path_outside_transaction(tmp_path):
    p=tmp_path/'request.json';p.write_text(json.dumps({'command':['/usr/bin/bwrap'],'status_path':'/tmp/outside-status'}))
    with pytest.raises(ValueError,match='share'):
        launch(p,hashlib.sha256(p.read_bytes()).hexdigest())


def test_staged_primitive_preserves_reference_under_wrapper(tmp_path):
    import build_evidence_calibration_five_method_packet_candidate as candidate
    from build_evidence_calibration_method_packets import build
    from inspect_evidence_calibration_packet import summarize
    from stage_evidence_calibration_workspace import staged_workspace
    diagnostic=json.loads((ROOT/'data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json').read_text())
    catalog=json.loads((ROOT/candidate.CATALOG).read_text())
    entry=candidate.materialize(diagnostic,'test-config','measured_response_recovery',catalog)[-1]
    packet=next(p for p in build(entry,candidate.execution_contract(entry,diagnostic))['method_packets'] if p['method_id']=='B2')
    with staged_workspace(entry,packet) as (w,b):
        r=module.run(w,b,['tools/inspect_evidence_calibration_packet.py','robot_visible/evidence.json'],
                     limits=replace(LOCAL,combined_output_bytes=1024**2),tree_limits=TREE,
                     scratch_limits=SCRATCH,event_directory=tmp_path/'primitive-events')
        assert r.returncode==0,r.stderr
        assert json.loads(r.stdout)==summarize(entry['method_packet'])
