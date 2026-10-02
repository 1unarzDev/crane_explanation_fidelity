import json
import pytest
import roboboat_hidden_render_v2 as render


def test_only_active_owned_workspace_must_be_empty():
    monitors=[{'name':'owned','id':1,'activeWorkspace':{'name':'99191'}}]
    workspaces=[{'name':'99191','monitor':'owned','windows':0},{'name':'user','monitor':'owned','windows':4}]
    assert render.active_workspace_empty(monitors,workspaces,'owned','99191')
    workspaces[0]['windows']=1
    assert not render.active_workspace_empty(monitors,workspaces,'owned','99191')
    assert not render.active_workspace_empty(monitors,workspaces,'missing','99191')


def test_owned_window_requires_unique_exact_placement():
    client={'class':'CRANE.x86_64','title':'ASV','workspace':{'name':'99191'},'monitor':1,'mapped':True}
    assert render.owned_window([client],'owned','99191',1)
    assert not render.owned_window([client,client],'owned','99191',1)
    assert not render.owned_window([client],'owned','other',1)
    assert not render.owned_window([client],'owned','99191',2)


def mocked(monkeypatch,*,occupied=False,bad_fps=False):
    monkeypatch.setenv('HYPRLAND_INSTANCE_SIGNATURE','test');monkeypatch.setattr(render.os,'getpid',lambda:91)
    name='CRANE-BOAT-91';workspace='900091';calls=[];created=False;fps=15
    def hypr(*args):
        nonlocal created,fps
        calls.append(args)
        if args==('monitors all','-j'):
            return json.dumps([{'name':name,'id':1,'activeWorkspace':{'name':workspace}}] if created else [])
        if args==('workspaces','-j'):
            return json.dumps([{'name':workspace,'monitor':name,'windows':int(occupied)},
                {'name':'user','monitor':name,'windows':3}] if created else [])
        if args==('output','create','headless',name):created=True
        if args==('output','remove',name):created=False
        if args[:2]==('getoption','misc:render_unfocused_fps'):return json.dumps({'int':fps})
        if args[0]=='eval' and 'render_unfocused_fps=60' in args[1] and not bad_fps:fps=60
        if args[0]=='eval' and 'render_unfocused_fps=15' in args[1]:fps=15
        return 'ok'
    monkeypatch.setattr(render,'hypr',hypr)
    return calls


def test_probe_verifies_lua_settings_and_restores_owned_state(monkeypatch):
    calls=mocked(monkeypatch)
    assert render.run([],probe_only=True)==0
    assert ('output','remove','CRANE-BOAT-91') in calls
    assert calls[-1]==('eval','hl.config({misc={render_unfocused_fps=15}})')
    assert any(a[0]=='eval' and 'workspace_rule' in a[1] and '["default"]=true' in a[1] for a in calls)
    assert not any(a[0]=='keyword' for a in calls)


@pytest.mark.parametrize('occupied,bad_fps,match',[(True,False,'not empty'),(False,True,'readback')])
def test_preflight_failure_does_not_launch_and_cleans_up(monkeypatch,occupied,bad_fps,match):
    calls=mocked(monkeypatch,occupied=occupied,bad_fps=bad_fps)
    monkeypatch.setattr(render.subprocess,'Popen',lambda *a,**k:pytest.fail('unexpected launch'))
    with pytest.raises(RuntimeError,match=match):render.run(['player'])
    assert ('output','remove','CRANE-BOAT-91') in calls
    assert calls[-1]==('eval','hl.config({misc={render_unfocused_fps=15}})')
