import json
import math

import pytest
import generate_roboboat_population_v4 as population


def setup(tmp_path, monkeypatch):
    base = population.base; root = tmp_path / 'repo'; doc = root / 'docs'; doc.mkdir(parents=True)
    (doc / 'task_contract_v2.json').write_bytes((base.DOC / 'task_contract_v2.json').read_bytes())
    config = root / 'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'
    config.parent.mkdir(parents=True); config.write_text('fixture config')
    analysis = root / 'analysis'; analysis.mkdir()
    for version in (1, 2, 3, 4):
        (analysis / f'generate_roboboat_population_v{version}.py').write_text('fixture source')
    monkeypatch.setattr(base, 'ROOT', root); monkeypatch.setattr(base, 'DOC', doc)
    monkeypatch.setattr(base, '__file__', str(analysis / 'generate_roboboat_population_v2.py'))
    monkeypatch.setattr(population, '__file__', str(analysis / 'generate_roboboat_population_v4.py'))
    return root, json.loads((doc / 'task_contract_v2.json').read_text())


def test_crop_has_exact_reference_arc_distance_and_invalid_ranges_rejected():
    path = {'poses': [{'x': 0., 'y': 0.}, {'x': 3., 'y': 0.}, {'x': 3., 'y': 4.}]}
    points = population.tail_points(path, 5.)
    assert points == [(2., 0.), (3., 0.), (3., 4.)]
    for value in (0., -1., float('nan'), float('inf'), 8.):
        with pytest.raises(ValueError): population.tail_points(path, value)


def test_balanced_terminal_population_preserves_task_pairs_and_unexecuted_scope(tmp_path, monkeypatch):
    root, task = setup(tmp_path, monkeypatch)
    d = population.generate(root / 'fresh', 180, 42007)
    assert len(d['strata_counts']) == 18 and set(d['strata_counts'].values()) == {10}
    assert d['independent_n_added_by_generation'] == 0 and d['initial_pose_extension_qualified'] is False
    assert len({r['seed'] for r in d['rows']}) == 180
    for cluster in d['clusters']:
        a, b = [r for r in d['rows'] if r['cluster_id'] == cluster['cluster_id']]
        assert a['initial_pose_request'] == b['initial_pose_request'] and a['seed'] == b['seed']
        assert sorted(r['internal_xy_tolerance_m'] for r in (a, b)) == [.2, .4]
        contract = json.loads((root / a['task_contract']['path']).read_text())
        assert {k: v for k, v in contract.items() if k not in ('goal', 'id')} == {k: v for k, v in task.items() if k not in ('goal', 'id')}
        assert a['geometry']['physical_initial_pose_varied'] is False
        assert a['geometry']['reference_curve_tail_distance_is_executed_length'] is False
        path_key = 'design_reference_curve' if a['action_mode'] == 'navigate-to-pose' else 'path_file'
        if path_key == 'design_reference_curve': assert 'path_file' not in a
        file = root / a[path_key]['path']; assert population.base.digest(file) == a[path_key]['sha256']
        poses = json.loads(file.read_text())['poses']; start = a['initial_pose_request']
        assert poses[0]['x'] == start['x'] and poses[0]['y'] == start['y'] and poses[-1] == a['goal']
        assert -math.pi <= start['yaw'] <= math.pi
        for p, q in zip(poses, poses[1:]):
            assert all(math.isfinite(p[k]) for k in ('x', 'y', 'yaw'))
            assert math.dist((p['x'], p['y']), (q['x'], q['y'])) <= population.base.SPACING_M + 1e-12


def test_draws_reproduce_and_generation_never_promotes_confirmation(tmp_path, monkeypatch):
    root, _ = setup(tmp_path, monkeypatch)
    a = population.generate(root / 'a', 18, 42007); b = population.generate(root / 'b', 18, 42007)
    for first, second in zip(a['rows'], b['rows']):
        assert first['initial_pose_request'] == second['initial_pose_request']
        assert first['geometry'] == second['geometry'] and first['seed'] == second['seed']
    with pytest.raises(ValueError): population.generate(root / 'confirmation', 18, 50001, phase='confirmation')
    with pytest.raises(FileExistsError): population.generate(root / 'a', 18, 42007)
