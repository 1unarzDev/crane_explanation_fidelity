import json
import math
from pathlib import Path

import pytest
import generate_roboboat_population_v3 as candidate


def setup(tmp_path, monkeypatch):
    base = candidate.base
    root = tmp_path / 'repo'; doc = root / 'docs'; doc.mkdir(parents=True)
    (doc / 'task_contract_v2.json').write_bytes((base.DOC / 'task_contract_v2.json').read_bytes())
    config = root / 'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'
    config.parent.mkdir(parents=True); config.write_text('fixture configuration')
    analysis = root / 'analysis'; analysis.mkdir()
    for version in (1, 2, 3):
        (analysis / f'generate_roboboat_population_v{version}.py').write_text('fixture source')
    monkeypatch.setattr(base, 'ROOT', root); monkeypatch.setattr(base, 'DOC', doc)
    monkeypatch.setattr(base, '__file__', str(analysis / 'generate_roboboat_population_v2.py'))
    monkeypatch.setattr(candidate, '__file__', str(analysis / 'generate_roboboat_population_v3.py'))
    return root


def test_requested_start_diversity_is_paired_and_does_not_change_task_or_claim_execution(tmp_path, monkeypatch):
    root = setup(tmp_path, monkeypatch)
    result = candidate.generate(root / 'fresh', 120, 42006)
    assert result['independent_n_added_by_generation'] == 0
    assert result['status'] == 'DEVELOPMENT_EXPLORATORY_START_POSE_CANDIDATE_UNEXECUTED'
    assert result['initial_pose_extension_qualified'] is False
    assert len({r['seed'] for r in result['rows']}) == 120
    assert len({tuple(r['initial_pose_request'].values()) for r in result['rows']}) == 120
    for cluster in result['clusters']:
        a, b = [r for r in result['rows'] if r['cluster_id'] == cluster['cluster_id']]
        assert a['initial_pose_request'] == b['initial_pose_request'] and a['seed'] == b['seed']
        assert a['geometry']['physical_initial_pose_varied'] is False
        assert a['geometry']['requested_initial_pose_varied'] is True
        assert a['geometry']['initial_pose_runtime_verified'] is False
        contract = json.loads((root / a['task_contract']['path']).read_text())
        assert contract['goal'] == a['goal']
        if 'path_file' not in a:
            continue
        file = root / a['path_file']['path']; assert candidate.base.digest(file) == a['path_file']['sha256']
        assert a['path_file'] == b['path_file']
        poses = json.loads(file.read_text())['poses']
        assert poses[0]['x'] == a['initial_pose_request']['x']
        assert poses[0]['y'] == a['initial_pose_request']['y']
        assert poses[-1] == a['goal']
        for p, q in zip(poses, poses[1:]):
            assert math.dist((p['x'], p['y']), (q['x'], q['y'])) <= candidate.base.SPACING_M + 1e-12
            assert all(math.isfinite(p[k]) for k in ('x', 'y', 'yaw'))
    with pytest.raises(ValueError):
        candidate.generate(root / 'confirmation', 6, 50001, phase='confirmation')


def test_seed_collision_resolution_and_int32_range():
    used = set(); a = candidate.launch_seed(42006, 0, used)
    b = candidate.launch_seed(42006, 0, used)
    assert a != b and 0 <= a < 2**31 and 0 <= b < 2**31
    assert candidate.launch_seed(42006, 0, set()) == a


def test_start_and_path_draws_are_reproducible(tmp_path, monkeypatch):
    root = setup(tmp_path, monkeypatch)
    a = candidate.generate(root / 'a', 12, 42006)
    b = candidate.generate(root / 'b', 12, 42006)
    for first, second in zip(a['rows'], b['rows']):
        assert first['initial_pose_request'] == second['initial_pose_request']
        assert first['geometry'] == second['geometry'] and first['seed'] == second['seed']
