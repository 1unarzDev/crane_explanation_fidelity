#!/usr/bin/env python3
"""Reproducible independent geometry draws; exploratory until a separate freeze.

Variants and evidence masks never create independent sample identities. No physics,
scene or controller is edited. Generated routes require empirical feasibility checks.
"""
import argparse
import copy
import hashlib
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/roboboat_terminal_evidence'
FAMILIES = ('nominal-turn', 'wide-turn', 'deep-turn', 'curved-stem', 'shallow-turn', 'direct-goal')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')


def route(lane, bottom, goal, amplitude):
    """Smooth south stem, semicircle and dock-aligned north stem in odom."""
    right = goal['x']
    radius = (right - lane) / 2
    center = (right + lane) / 2
    poses = []
    # No start teleport. Path begins near the measured scene-default start.
    for i in range(33):
        t = i / 32
        x = -2.2768 + (lane + 2.2768) * t + amplitude * math.sin(2*math.pi*t) * math.sin(math.pi*t)
        y = -5.2 + (bottom + 5.2) * t
        poses.append({'x': x, 'y': y, 'yaw': -math.pi/2})
    for i in range(1, 33):
        angle = math.pi + math.pi*i/32
        poses.append({'x': center + radius*math.cos(angle),
                      'y': bottom + radius*math.sin(angle),
                      'yaw': angle + math.pi/2 - 2*math.pi})
    for i in range(1, 17):
        t = i / 16
        poses.append({'x': right, 'y': bottom + (goal['y']-bottom)*t, 'yaw': math.pi/2})
    poses[-1] = dict(goal)
    return {'schema': 'crane-nav2-path-v1', 'frameId': 'odom',
            'description': 'Generated development route; feasibility is not asserted.', 'poses': poses}


def generate(output, count, seed, phase='development'):
    if count < 1 or phase != 'development':
        raise ValueError('positive development count required; confirmation needs separate frozen protocol')
    if output.exists():
        raise FileExistsError('population is immutable; use a new namespace/seed')
    rng = random.Random(seed)
    output.mkdir(parents=True)
    path_root = ROOT / 'packages/crane_ml/Tools/Performance/generated_populations' / output.name
    if path_root.exists():
        raise FileExistsError('generated runtime namespace already exists')
    task = json.loads((DOC / 'task_contract_v2.json').read_text())
    config = ROOT / 'packages/crane_ml/Tools/Performance/roboboat_terminal_v1.yaml'
    rows, clusters = [], []
    for index in range(count):
        family = FAMILIES[index % len(FAMILIES)]
        cluster = f'boat-geom-{seed}-{index+1:05d}'
        lane = rng.uniform(-2.65, -2.1)
        bottom = rng.uniform(-32.0, -30.8)
        amplitude = 0.0
        if family == 'wide-turn': lane = rng.uniform(-3.4, -2.75)
        if family == 'deep-turn': bottom = rng.uniform(-35.0, -32.5)
        if family == 'curved-stem': amplitude = rng.uniform(-0.5, 0.5)
        if family == 'shallow-turn': bottom = rng.uniform(-30.5, -29.5)
        # Goal perturbations stay within the existing physical berth. Public evaluation
        # rectangle remains the actual fixed berth; only the requested target changes.
        goal = {'x': rng.uniform(0.7141434, 1.0141434),
                'y': rng.uniform(-27.736906, -27.436906),
                'yaw': math.pi/2 + rng.uniform(-0.10, 0.10)}
        contract = copy.deepcopy(task)
        contract['id'] = cluster + '-task-v2'
        contract['goal'] = goal
        contract_path = output / 'contracts' / (cluster + '.json')
        write(contract_path, contract)
        path = path_root / (cluster + '.json')
        if family != 'direct-goal': write(path, route(lane, bottom, goal, amplitude))
        cluster_rows = []
        tolerances = (0.2, 0.4) if index % 2 == 0 else (0.4, 0.2)
        for variant, tolerance in enumerate(tolerances, 1):
            row = {'id': cluster + f'-v{variant}', 'cluster_id': cluster, 'family': family,
                   'variant': variant, 'internal_xy_tolerance_m': tolerance,
                   'action_mode': 'navigate-to-pose' if family == 'direct-goal' else 'follow-path',
                   'goal': goal, 'task_contract': {'path': str(contract_path.relative_to(ROOT)), 'sha256': digest(contract_path)},
                   'sampling_seed': seed, 'geometry_draw_index': index,
                   'seed': 41000 + index, 'retry_budget': 0,
                   'disposition': 'DEVELOPMENT_EXPLORATORY',
                   'geometry': {'lane_x': lane, 'turn_y': bottom, 'stem_amplitude': amplitude}}
            if family != 'direct-goal': row['path_file'] = {'path': str(path.relative_to(ROOT)), 'sha256': digest(path)}
            rows.append(row); cluster_rows.append(row['id'])
        clusters.append({'cluster_id': cluster, 'family': family, 'rows': cluster_rows})
    declaration = {'schema': 'roboboat-generated-development-population/v1',
                   'status': 'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION', 'seed': seed,
                   'independent_geometry_draws': count, 'physical_variants': len(rows),
                   'rows': rows, 'clusters': clusters,
                   'nav2_configuration': {'path': str(config.relative_to(ROOT)), 'sha256': digest(config)},
                   'generator': {'path': str(Path(__file__).resolve().relative_to(ROOT)), 'sha256': digest(Path(__file__))},
                   'sampling': 'Balanced family strata with independent continuous parameter draws; variant order AB/BA balanced.',
                   'independence': 'One geometry draw is one candidate cluster. Two tolerances, L0-L2, seeds, masks and repeats add zero N. Common scene alone does not establish broad environmental generalization.',
                   'platform_change': 'None: fixed scene reset, physical berth, player, controller and physics. Goal pose/path differ by declaration; public berth stays fixed.',
                   'validity': 'Technical completeness only; no favorable physical or method outcome admission.',
                   'confirmation_n': 0, 'land_n_added': 0,
                   'population_ceiling': None,
                   'next_batch': 'Expand with a new seed/namespace after feasibility, effect and annotation-noise review; initial count is a pilot batch, not a study ceiling.'}
    write(output / 'registry.json', declaration)
    return declaration


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--clusters', required=True, type=int)
    p.add_argument('--seed', required=True, type=int)
    a = p.parse_args()
    result = generate(a.output.resolve(), a.clusters, a.seed)
    print(json.dumps({'registry': str(a.output / 'registry.json'), 'clusters': result['independent_geometry_draws'], 'rows': len(result['rows'])}))

if __name__ == '__main__': main()
