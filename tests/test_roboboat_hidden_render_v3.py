import json
import os
from pathlib import Path
import subprocess
import sys
import time
import pytest
import roboboat_hidden_render_v3 as r


def mocked(monkeypatch,fail_disable=False,fail_remove=False):
    monkeypatch.setenv('HYPRLAND_INSTANCE_SIGNATURE','test')
    monkeypatch.setattr(r.os,'getpid',lambda:91)
    calls=[];created=False;fps=15;name=None
    def hypr(*args):
        nonlocal created,fps,name
        calls.append(args)
        if args==('monitors all','-j'):return json.dumps([{'name':name,'id':7,'activeWorkspace':{'name':'900091'}}] if created else [])
        if args==('workspaces','-j'):return json.dumps([{'name':'900091','monitor':name,'windows':0},{'name':'user','monitor':name,'windows':4}] if created else [])
        if args[0]=='clients':return '[]'
        if args[:2]==('output','create'):created=True;name=args[3]
        if args[:2]==('output','remove'):
            if fail_remove:raise RuntimeError('remove refused')
            created=False
        if args[0]=='eval':
            if 'set_enabled(false)' in args[1] and fail_disable:raise RuntimeError('disable refused')
            if 'render_unfocused_fps=60' in args[1]:fps=60
            if 'render_unfocused_fps=15' in args[1]:fps=15
        if args[0]=='getoption':return json.dumps({'int':fps})
        return 'ok'
    monkeypatch.setattr(r,'hypr',hypr)
    return calls


def test_probe_uses_owned_disabled_handles_and_no_global_reload(monkeypatch,tmp_path):
    calls=mocked(monkeypatch)
    path=tmp_path/'audit.json'
    assert r.run([],probe_only=True,audit_path=path)==0
    report=json.loads(path.read_text())
    assert report['restored_fps']==15 and report['owned_output_removed'] is True
    assert not any(a[0]=='reload' for a in calls)
    assert any('set_enabled(false)' in a[1] for a in calls if a[0]=='eval')
    assert report['full_state_preservation_claimed'] is False


def test_cleanup_failures_do_not_skip_fps_restore(monkeypatch,tmp_path):
    calls=mocked(monkeypatch,fail_disable=True,fail_remove=True)
    path=tmp_path/'audit.json'
    with pytest.raises(RuntimeError,match='cleanup incomplete'):r.run([],probe_only=True,audit_path=path)
    report=json.loads(path.read_text())
    assert len(report['cleanup_errors'])==2
    assert report['restored_fps']==15
    assert any(a[:2]==('output','remove') for a in calls)


@pytest.mark.parametrize('message',['Name already taken','output not found','no backend replied to the request','eval is only supported with the lua config manager'])
def test_exit_zero_operation_errors_rejected(monkeypatch,message):
    monkeypatch.setattr(r.subprocess,'run',lambda *a,**k:subprocess.CompletedProcess([],0,message,''))
    with pytest.raises(RuntimeError,match='rejected'):r.hypr('eval','x')


def test_current_unqualified_unity_class_fails_before_mutation(monkeypatch):
    monkeypatch.setenv('HYPRLAND_INSTANCE_SIGNATURE','test')
    monkeypatch.setattr(r,'hypr',lambda *a:pytest.fail('mutation before class qualification'))
    with pytest.raises(ValueError,match='nonce class'):r.run(['player'],expected_class='CRANE.x86_64')


def test_window_ownership_requires_session_pid_and_exact_class(monkeypatch):
    monkeypatch.setattr(r,'process_records',lambda:{42:{'sid':40,'pgid':40,'start':101,'state':'S'},43:{'sid':43,'pgid':43,'start':102,'state':'S'}})
    c={'class':'exclusive','pid':42,'mapped':True,'workspace':{'name':'owned'},'monitor':7}
    assert r.owned_window([c],'exclusive','owned',7,40,100)
    c['pid']=43
    assert not r.owned_window([c],'exclusive','owned',7,40,100)
    c['pid']=42
    assert not r.owned_window([c,c],'exclusive','owned',7,40,100)


def test_cleanup_refuses_group_identity_change(monkeypatch):
    monkeypatch.setattr(r,'process_records',lambda:{10001:{'sid':20000,'pgid':10000,'start':5,'state':'S'}})
    monkeypatch.setattr(r.os,'killpg',lambda *a:pytest.fail('unsafe signal'))
    class P:pid=10000
    with pytest.raises(RuntimeError,match='identity changed'):r.cleanup_group(P(),10)


def test_disposable_exited_parent_surviving_descendant_cleanup(tmp_path):
    marker=tmp_path/'child.json'
    code="import subprocess,sys,json,pathlib,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); pathlib.Path(sys.argv[1]).write_text(json.dumps({'pid':p.pid})); time.sleep(.2)"
    p=subprocess.Popen([sys.executable,'-c',code,str(marker)],start_new_session=True)
    try:
        deadline=time.monotonic()+3
        while p.pid not in r.process_records() and time.monotonic()<deadline:time.sleep(.01)
        anchor=r.process_records()[p.pid]['start']
        p.wait(timeout=3)
        child=json.loads(marker.read_text())['pid']
        assert r.group_owned_pid(child,p.pid,anchor,r.process_records())
        actions=r.cleanup_group(p,anchor,timeout_s=.5)
        assert actions and not r.group_owned_pid(child,p.pid,anchor,r.process_records())
    finally:
        try:os.killpg(p.pid,9)
        except ProcessLookupError:pass
        p.wait()


def test_mocked_owned_launch_and_interrupt_cleanup(monkeypatch,tmp_path):
    calls=mocked(monkeypatch)
    cls='CRANE-owned-'+'a'*32
    original=r.hypr
    running={'launched':False}
    def hypr(*args):
        if args[0]=='clients' and running['launched']:
            return json.dumps([{'class':cls,'pid':42,'mapped':True,'workspace':{'name':'900091'},'monitor':7}])
        return original(*args)
    monkeypatch.setattr(r,'hypr',hypr)
    monkeypatch.setattr(r,'process_records',lambda:{40:{'sid':40,'pgid':40,'start':100,'state':'S'},42:{'sid':40,'pgid':40,'start':101,'state':'S'}})
    cleaned=[]
    monkeypatch.setattr(r,'cleanup_group',lambda p,a:cleaned.append((p.pid,a)))
    class P:
        pid=40
        def __init__(self,*a,**k):running['launched']=True;assert k['start_new_session'] is True
        def poll(self):return None
        def wait(self):raise KeyboardInterrupt('mock signal')
    monkeypatch.setattr(r.subprocess,'Popen',P)
    path=tmp_path/'audit.json'
    with pytest.raises(KeyboardInterrupt):r.run(['disposable'],expected_class=cls,audit_path=path)
    report=json.loads(path.read_text())
    assert report['placement_verified'] and cleaned==[(40,100)]
    assert report['restored_fps']==15 and report['owned_output_removed'] is True
    rules=[a[1] for a in calls if a[0]=='eval' and 'hl.window_rule' in a[1]]
    assert len(rules)==1 and '^'+cls+'$' in rules[0]
    assert 'CRANE.x86_64' not in rules[0]
