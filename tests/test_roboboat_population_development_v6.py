import json
from pathlib import Path
import pytest
import run_roboboat_population_development_v6 as collector
from test_roboboat_population_v1 import clean_capture


def bound_build(tmp_path,monkeypatch):
    root=tmp_path/'build';root.mkdir()
    player=root/'CRANE.x86_64';player.write_bytes(b'unchanged bootstrap')
    assembly=root/'PerformanceAssembly.dll';assembly.write_bytes(b'actual compiled version')
    identity=tmp_path/'build.json'
    identity.write_text(json.dumps({'build_root':str(root),'full_build_files':[
        {'path':p.name,'bytes':p.stat().st_size,'sha256':collector.digest(p)} for p in (player,assembly)]}))
    monkeypatch.setattr(collector,'PLAYER',player)
    monkeypatch.setattr(collector,'BUILD_IDENTITY',identity)
    return root,assembly


def test_full_build_binding_checks_assembly_despite_identical_bootstrap(tmp_path,monkeypatch):
    root,assembly=bound_build(tmp_path,monkeypatch)
    collector.verify_player()
    assembly.write_bytes(b'changed compiled version')
    with pytest.raises(ValueError,match='compiled player binding mismatch'):collector.verify_player()


@pytest.mark.parametrize('fault',['stale','wrong_cap','wrong_step'])
def test_actual_capture_enforces_freshness_and_declared_clock(tmp_path,monkeypatch,fault):
    registry=tmp_path/'registry.json';registry.write_text('{}')
    config=tmp_path/'config.yaml';config.write_text('configuration')
    bound_build(tmp_path,monkeypatch)
    scripts=tmp_path/'scripts';scripts.mkdir();(scripts/'run_roboboat_hidden_render.sh').write_text('wrapper')
    launcher=tmp_path/'packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh'
    launcher.parent.mkdir(parents=True);launcher.write_text('launcher')
    monkeypatch.setattr(collector,'ROOT',tmp_path)
    monkeypatch.setattr(collector,'bound',lambda _:config)
    monkeypatch.setattr(collector,'default_affinity',lambda:list(range(20)))
    seen={}
    class Launch:
        pid=1
        def __init__(self,command,env,**kwargs):
            seen.update(env);out=Path(env['CRANE_RESULT_ROOT']);(out/'worker-0').mkdir()
            s,w,f=clean_capture()
            w.update(imageSignatures=True,screenWidth=640,screenHeight=360,timeScale=1,
                enabledCameras=1,enabledSensorCameras=1,enabledSpectatorCameras=0,
                enabledWaterDriverCameras=0,depthCamera={'width':1280,'height':720,'acquisitionCount':10})
            if fault=='stale':w['staleObservations']=1
            for name,value in [('navigation-reset-summary.json',s),('worker-0/result.json',w),('fixture-summary.json',f)]:
                (out/name).write_text(json.dumps(value))
            step=.01 if fault=='wrong_step' else .02;cap=.08 if fault=='wrong_cap' else .04
            metadata={'schema':'crane-frame-timing-audit/v1-development','kind':'metadata',
                'fixedDeltaTime':step,'appliedMaximumDeltaTime':cap,'originalMaximumDeltaTime':1/3}
            frame={'kind':'frame','frame':1,'wallSeconds':1,'simulationSeconds':1,'deltaTime':.02,
                'unscaledDeltaTime':.02,'fixedDeltaTime':step,'maximumDeltaTime':cap,'fixedUpdates':1,
                'staleIncrement':0,'staleObservations':0,'failedObservations':0,'pendingDepthReadbacks':0}
            (out/'frame-timing.jsonl').write_text(json.dumps(metadata)+'\n'+json.dumps(frame)+'\n')
        def wait(self,timeout):return 0
    monkeypatch.setattr(collector.subprocess,'Popen',Launch)
    monkeypatch.setattr(collector,'project',lambda *a:pytest.fail('invalid run exported'))
    row={'id':'fresh','goal':{'x':1,'y':2,'yaw':0},'seed':10,
         'internal_xy_tolerance_m':.2,'task_contract':{},'action_mode':'navigate-to-pose'}
    result=collector.capture(row,{'nav2_configuration':{}},registry,tmp_path/'captures',191,11481,.04)
    assert result['status']=='TECHNICAL_FAILURE'
    key={'stale':'stale_observations_zero','wrong_cap':'clock_cap_matches_declaration','wrong_step':'fixed_physics_step_002'}[fault]
    assert result['checks'][key] is False
    assert seen['CRANE_NAV2_UNITY_EXTRA_ARGS'].endswith('--crane-maximum-delta-time 0.04')
    assert '--crane-no-signatures' not in seen['CRANE_NAV2_UNITY_EXTRA_ARGS']
    assert result['maximum_delta_time']==.04
