"""Unexecuted development population adding requested physical start diversity.

Requires a separately qualified initial-pose build/launcher; v12 cannot launch it.
"""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path

import generate_roboboat_population_v2 as base


def start_route(path, start):
    """Replace the first stem by a smooth connection from the requested start."""
    old = path['poses']
    index = next(i for i, p in enumerate(old) if p['y'] <= base.START[1] - 4)
    join = old[index]
    length = math.dist((start['x'], start['y']), (join['x'], join['y']))
    if length <= .5:
        raise ValueError('initial connector is degenerate')
    points = base.hermite((start['x'], start['y']), (join['x'], join['y']),
        (length * math.cos(start['yaw']), length * math.sin(start['yaw'])),
        (length * math.cos(join['yaw']), length * math.sin(join['yaw'])))
    points.extend((p['x'], p['y']) for p in old[index + 1:])
    dense = [points[0]]
    for a, b in zip(points, points[1:]):
        count = max(1, math.ceil(math.dist(a, b) / base.SPACING_M))
        dense.extend((a[0] + (b[0] - a[0]) * i / count,
                      a[1] + (b[1] - a[1]) * i / count) for i in range(1, count + 1))
    poses = []
    for i, (x, y) in enumerate(dense):
        a, b = dense[max(0, i - 1)], dense[min(len(dense) - 1, i + 1)]
        poses.append({'x': x, 'y': y, 'yaw': math.atan2(b[1] - a[1], b[0] - a[0])})
    poses[-1] = dict(old[-1])
    return {**path, 'description': 'Development v3 requested physical start and smooth connector; clearance unvalidated.',
            'poses': poses}


def launch_seed(namespace, index, used):
    # Int32 launch seed, deterministic collision resolution, no 1000-row namespace assumption.
    nonce = 0
    while True:
        key = f'roboboat-start-v3:{namespace}:{index}:{nonce}'.encode()
        seed = int.from_bytes(hashlib.sha256(key).digest()[:4], 'big') & 0x7fffffff
        if seed not in used:
            used.add(seed)
            return seed
        nonce += 1


def generate(output, count, seed, phase='development'):
    if phase != 'development':
        raise ValueError('unexecuted development candidates only')
    result = base.generate(output, count, seed)
    output = Path(output).resolve()
    upstream = output / 'base-route-generation-v2.json'
    (output / 'registry.json').rename(upstream)
    rng = random.Random(f'roboboat-start-v3:{seed}')
    used = set()
    starts = {}
    for cluster in result['clusters']:
        # Controlled neighbourhood of the existing route anchor; no clearance claim.
        starts[cluster['cluster_id']] = {'x': rng.uniform(base.START[0] - .45, base.START[0] + .45),
                                        'y': rng.uniform(base.START[1] - 1.5, base.START[1] + 1.5),
                                        'yaw': rng.uniform(-1.0, 1.0)}
    processed = set()
    for row in result['rows']:
        cluster = row['cluster_id']
        row['initial_pose_request'] = dict(starts[cluster])
        row['initial_pose_units'] = {'frame': 'odom', 'x': 'm', 'y': 'm', 'yaw': 'rad'}
        row['initial_pose_cli_option'] = '--crane-roboboat-start-pose'
        row['geometry']['physical_start'] = 'Requested varied planar position/yaw; scene height retained; not executed.'
        row['geometry']['physical_initial_pose_varied'] = False
        row['geometry']['requested_initial_pose_varied'] = True
        row['geometry']['initial_pose_runtime_verified'] = False
        if cluster not in processed:
            mapped = launch_seed(seed, row['geometry_draw_index'], used)
            for same in result['rows']:
                if same['cluster_id'] == cluster:
                    same['seed'] = mapped
            if 'path_file' in row:
                file = base.ROOT / row['path_file']['path']
                path = start_route(json.loads(file.read_text()), starts[cluster])
                revised = file.with_name(file.stem + '-startv3.json')
                base.write(revised, path)
                descriptors = base.descriptors(path)
                for same in result['rows']:
                    if same['cluster_id'] == cluster:
                        same['path_file'] = {'path': str(revised.relative_to(base.ROOT)),
                                             'sha256': base.digest(revised)}
                        same['geometry'].update(descriptors)
                        same['geometry']['requested_initial_pose_varied'] = True
            processed.add(cluster)
    result.update(schema='roboboat-generated-development-population/v3',
        status='DEVELOPMENT_EXPLORATORY_START_POSE_CANDIDATE_UNEXECUTED',
        generator={'path': str(Path(__file__).resolve().relative_to(base.ROOT)), 'sha256': base.digest(Path(__file__))},
        dependencies=result['dependencies'] + [{'path': str(Path(base.__file__).resolve().relative_to(base.ROOT)),
                                               'sha256': base.digest(Path(base.__file__))}],
        initial_pose_extension_qualified=False,
        base_route_generation={'path': str(upstream.relative_to(base.ROOT)), 'sha256': base.digest(upstream)},
        sampling='Balanced six route families; independently sampled goal/route/start XY/yaw; fixed berth and task requirements; paired tolerance variants.',
        platform_change='Requires an opt-in start-pose initialization extension. Candidate initial states only; physics/controller/sensor changes not requested.',
        initial_pose_distribution={'x_m': [base.START[0] - .45, base.START[0] + .45],
                                   'y_m': [base.START[1] - 1.5, base.START[1] + 1.5],
                                   'yaw_rad': [-1., 1.], 'height': 'unchanged scene initial height'},
        launch_requirements='Separate exact-build source audit, component and physical operational qualification, launcher option/receipt/readback binding and valid population overlap audit. v12 collector must reject this status.',
        independent_n_added_by_generation=0)
    base.write(output / 'registry.json', result)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True, type=Path)
    p.add_argument('--clusters', required=True, type=int); p.add_argument('--seed', required=True, type=int)
    a = p.parse_args(); result = generate(a.output, a.clusters, a.seed)
    print(json.dumps({'status': result['status'], 'geometry_draws': result['independent_geometry_draws'],
                      'rows': len(result['rows']), 'independent_n_added': 0}))
