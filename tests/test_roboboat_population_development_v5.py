import copy
import json
import pytest
from run_roboboat_population_development_v5 import operational_probe_checks, technical_checks, capture
from test_roboboat_population_v1 import clean_capture


def probe_worker():
    _, w, _ = clean_capture()
    w.update(imageSignatures=False, screenWidth=640, screenHeight=360, timeScale=1,
        enabledCameras=1, enabledSensorCameras=1, enabledSpectatorCameras=0,
        enabledWaterDriverCameras=0, depthCamera={"width":1280,"height":720,"acquisitionCount":10})
    return w


def test_display_probe_keeps_strict_freshness_gate():
    s, _, f = clean_capture(); w=probe_worker()
    assert all({**technical_checks(s,w,f), **operational_probe_checks(w)}.values())
    w["staleObservations"]=1
    assert not all({**technical_checks(s,w,f), **operational_probe_checks(w)}.values())


@pytest.mark.parametrize("field,value",[("screenWidth",320),("timeScale",.5),
    ("enabledSensorCameras",0),("enabledWaterDriverCameras",1)])
def test_probe_rejects_unexpected_operational_or_sensor_change(field,value):
    w=probe_worker(); w[field]=value
    assert not all(operational_probe_checks(w).values())


def test_reduced_sensor_resolution_is_not_display_probe():
    w=probe_worker();w["depthCamera"]["width"]=320
    assert not all(operational_probe_checks(w).values())


def test_retained_failed_capture_is_never_reissued(tmp_path):
    registry=tmp_path/"registry.json"; registry.write_text("{}")
    import run_roboboat_population_development_v5 as v3
    row={"id":"old"}; out=tmp_path/"captures"/"old";out.mkdir(parents=True)
    record={"status":"TECHNICAL_FAILURE","registry_sha256":v3.digest(registry)}
    (out/"capture-attempt.json").write_text(json.dumps(record))
    assert capture(row,{},registry,tmp_path/"captures",191,11481)==record


def test_capture_binds_probe_launch_and_rejects_stale_depth(tmp_path, monkeypatch):
    import run_roboboat_population_development_v5 as v3
    registry=tmp_path/"registry.json"; registry.write_text("{}")
    config=tmp_path/"config.yaml"; config.write_text("configuration")
    player=tmp_path/"player"; player.write_text("player")
    scripts=tmp_path/"scripts"; scripts.mkdir()
    (scripts/"run_roboboat_hidden_render.sh").write_text("wrapper")
    launcher=tmp_path/"packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh"
    launcher.parent.mkdir(parents=True); launcher.write_text("launcher")
    monkeypatch.setattr(v3,"ROOT",tmp_path)
    monkeypatch.setattr(v3,"PLAYER",player)
    monkeypatch.setattr(v3,"bound",lambda binding:config)
    monkeypatch.setattr(v3,"PLAYER_SHA256",v3.digest(player))
    monkeypatch.setattr(v3,"default_affinity",lambda:list(range(20)))
    monkeypatch.setenv("CRANE_NAV2_UNITY_EXTRA_ARGS","--bad-inherited-flag")
    seen={}
    commands=[]
    class Launch:
        pid=1
        def __init__(self,command,env,**kwargs):
            commands.append(command)
            seen.update(env)
            out=__import__('pathlib').Path(env['CRANE_RESULT_ROOT'])
            (out/'worker-0').mkdir()
            s,_,f=clean_capture();w=probe_worker();w['staleObservations']=1
            for path,obj in [('navigation-reset-summary.json',s),('fixture-summary.json',f),('worker-0/result.json',w)]:
                (out/path).write_text(json.dumps(obj))
        def wait(self,timeout): return 0
    monkeypatch.setattr(v3.subprocess,"Popen",Launch)
    monkeypatch.setattr(v3,"project",lambda *args:pytest.fail('invalid recording exported'))
    row={'id':'fresh','goal':{'x':1,'y':2,'yaw':0},'seed':10,
         'internal_xy_tolerance_m':.2,'task_contract':{},'action_mode':'navigate-to-pose'}
    result=capture(row,{'nav2_configuration':{}},registry,tmp_path/'captures',191,11481)
    assert result['status']=='TECHNICAL_FAILURE'
    assert result['checks']['stale_observations_zero'] is False
    assert result['launch_values']['CRANE_SCREEN_WIDTH']=='640'
    assert result['launch_values']['CRANE_SCREEN_HEIGHT']=='360'
    assert result['launch_values']['CRANE_TIME_SCALE']=='1'
    assert seen['CRANE_NOGRAPHICS']=='0'

    assert seen['CRANE_NAV2_UNITY_EXTRA_ARGS']=='--crane-no-signatures'
    assert seen['CRANE_PLAYER']==str(player)
    assert commands==[[str(scripts/'run_roboboat_hidden_render.sh'),str(launcher)]]
    assert result['probe_version']==v3.PROBE_VERSION
    assert result['image_signatures'] is False
    intent=json.loads((tmp_path/'captures/fresh/capture-intent.json').read_text())
    assert intent['collector_sha256']==v3.digest(__import__('pathlib').Path(v3.__file__))


def test_signature_flag_must_be_applied():
    w=probe_worker();w['imageSignatures']=True
    assert not operational_probe_checks(w)['image_signatures_disabled']
    del w['imageSignatures']
    assert not operational_probe_checks(w)['image_signatures_disabled']


def test_immutable_player_binding_is_verified(tmp_path,monkeypatch):
    import run_roboboat_population_development_v5 as v5
    player=tmp_path/'player';player.write_text('changed')
    monkeypatch.setattr(v5,'PLAYER',player)
    with pytest.raises(ValueError,match='player hash mismatch'):v5.verify_player()


def test_restricted_inherited_cpu_affinity_rejected(monkeypatch):
    import run_roboboat_population_development_v5 as v5
    monkeypatch.setattr(v5.os,'cpu_count',lambda:20)
    monkeypatch.setattr(v5.os,'sched_getaffinity',lambda _:set(range(16)))
    with pytest.raises(ValueError,match='default host CPU affinity'):v5.default_affinity()


def test_main_uses_untouched_rows_and_consecutive_new_failure_stop(tmp_path,monkeypatch):
    import run_roboboat_population_development_v5 as v5
    registry=tmp_path/'registry.json'
    registry.write_text(json.dumps({'status':'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION',
                                    'rows':[{'id':f'row-{i}'} for i in range(5)]}))
    output=tmp_path/'captures';(output/'row-0').mkdir(parents=True)
    monkeypatch.setattr(v5,'verify_player',lambda:None)
    monkeypatch.setattr(v5,'default_affinity',lambda:list(range(20)))
    monkeypatch.setattr(v5.fcntl,'flock',lambda *args:None)
    seen=[]
    def fake(row,*args):
        seen.append(row['id']);return {'status':'TECHNICAL_FAILURE'}
    monkeypatch.setattr(v5,'capture',fake)
    monkeypatch.setattr(__import__('sys'),'argv',['collector','--registry',str(registry),
        '--output-root',str(output),'--max-new-attempts','4'])
    v5.main()
    assert seen==['row-1','row-2']
    intent=json.loads((output/'image-signature-probes-v5/probe-row-1.json').read_text())
    assert intent['schema']==v5.PROBE_VERSION
    assert intent['rows']==['row-1','row-2','row-3','row-4']
    assert intent['unity_extra_args']==['--crane-no-signatures']
    terminal=json.loads((output/'image-signature-probes-v5/probe-row-1-terminal.json').read_text())
    assert terminal['physical_attempts']==2
    assert terminal['remaining_rows']==['row-3','row-4']
    assert terminal['study_ceiling'] is None
