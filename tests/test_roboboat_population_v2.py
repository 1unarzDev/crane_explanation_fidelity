import json
import math
from pathlib import Path
import pytest
import generate_roboboat_population_v2 as population


def setup(tmp_path,monkeypatch):
    root=tmp_path/'repo';doc=root/'docs';doc.mkdir(parents=True)
    (doc/'task_contract_v2.json').write_bytes((population.DOC/'task_contract_v2.json').read_bytes())
    config=root/'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml';config.parent.mkdir(parents=True);config.write_text('config')
    source=root/'analysis/generate_roboboat_population_v2.py';source.parent.mkdir();source.write_text('fixture source')
    (source.parent/'generate_roboboat_population_v1.py').write_text('fixture dependency')
    monkeypatch.setattr(population,'ROOT',root);monkeypatch.setattr(population,'DOC',doc);monkeypatch.setattr(population,'__file__',str(source))
    return root,doc


def test_large_population_preserves_identity_task_and_geometry(tmp_path,monkeypatch):
    root,doc=setup(tmp_path,monkeypatch)
    a=population.generate(root/'fresh',120,42004)
    b=population.generate(root/'fresh-other',120,42005)
    original=json.loads((doc/'task_contract_v2.json').read_text())
    assert len({r['cluster_id'] for r in a['rows']})==120
    assert {c['family'] for c in a['clusters']}==set(population.FAMILIES)
    assert {r['seed'] for r in a['rows']}.isdisjoint({r['seed'] for r in b['rows']})
    for c in a['clusters']:
        rows=[r for r in a['rows'] if r['cluster_id']==c['cluster_id']]
        assert len(rows)==2 and rows[0]['seed']==rows[1]['seed']
        assert rows[0]['goal']==rows[1]['goal'] and rows[0]['geometry']==rows[1]['geometry']
        contract=json.loads((root/rows[0]['task_contract']['path']).read_text())
        assert contract['berth_center']==original['berth_center']
        assert contract['goal']==rows[0]['goal']
        if 'path_file' not in rows[0]:continue
        path=json.loads((root/rows[0]['path_file']['path']).read_text())
        assert path['poses'][-1]==rows[0]['goal']
        assert (path['poses'][0]['x'],path['poses'][0]['y'])==population.START
        for pose in path['poses']:
            assert all(math.isfinite(pose[k]) for k in ('x','y','yaw'))
            assert -math.pi <= pose['yaw'] <= math.pi
        for first,second in zip(path['poses'],path['poses'][1:]):
            assert math.dist((first['x'],first['y']),(second['x'],second['y']))<=population.SPACING_M+1e-12
        assert rows[0]['geometry']['physical_initial_pose_varied'] is False
        assert rows[0]['geometry']['clearance_validated'] is False
    with pytest.raises(FileExistsError):population.generate(root/'fresh',6,42004)
    with pytest.raises(ValueError):population.generate(root/'confirmation',6,50001,phase='confirmation')


def test_yaw_follows_geometry_except_requested_final_orientation():
    goal={'x':.86,'y':-27.5,'yaw':math.pi/2}
    path=population.route(-2.8,-34,goal,4,.15,.2,'terminal-s-bend')
    poses=path['poses']
    for i,p in enumerate(poses[:-1]):
        a=poses[max(0,i-1)];b=poses[i+1]
        assert p['yaw']==pytest.approx(math.atan2(b['y']-a['y'],b['x']-a['x']))
    assert poses[-1]==goal


def test_input_draws_are_reproducible(tmp_path,monkeypatch):
    root,_=setup(tmp_path,monkeypatch)
    a=population.generate(root/'a',12,42004);b=population.generate(root/'b',12,42004)
    for first,second in zip(a['rows'],b['rows']):
        assert first['goal']==second['goal'] and first['geometry']==second['geometry'] and first['seed']==second['seed']
