"""Unexecuted terminal-approach development draws across route and distance strata.

No outcome data are read. Fixed berth/task, paired tolerances and controller
settings are retained. Requires qualified physical-start launch support.
"""
import argparse
import json
import math
import random
from pathlib import Path

import generate_roboboat_population_v2 as base
from generate_roboboat_population_v3 import launch_seed

FAMILIES = ('reference-tail', 'smooth-terminal', 'terminal-s-bend',
            'terminal-dogleg', 'terminal-turn', 'direct-goal')
BANDS = (('near', 2., 5.), ('medium', 5., 9.), ('far', 9., 14.))


def tail_points(path, distance):
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError('positive finite reference-curve distance required')
    poses = path['poses']; remaining = distance
    for i in range(len(poses) - 2, -1, -1):
        a, b = poses[i], poses[i + 1]
        gap = math.dist((a['x'], a['y']), (b['x'], b['y']))
        if gap == 0:
            continue
        if remaining <= gap:
            fraction = remaining / gap
            cut = (b['x'] - fraction * (b['x'] - a['x']),
                   b['y'] - fraction * (b['y'] - a['y']))
            return [cut] + [(p['x'], p['y']) for p in poses[i + 1:]]
        remaining -= gap
    raise ValueError('requested tail exceeds complete reference curve')


def as_path(points, goal):
    dense = [points[0]]
    for a, b in zip(points, points[1:]):
        count = max(1, math.ceil(math.dist(a, b) / base.SPACING_M))
        dense.extend((a[0] + (b[0] - a[0]) * i / count,
                      a[1] + (b[1] - a[1]) * i / count) for i in range(1, count + 1))
    poses = []
    for i, (x, y) in enumerate(dense):
        a, b = dense[max(0, i - 1)], dense[min(len(dense) - 1, i + 1)]
        poses.append({'x': x, 'y': y, 'yaw': math.atan2(b[1] - a[1], b[0] - a[0])})
    poses[-1] = dict(goal)
    return {'schema': 'crane-nav2-path-v1', 'frameId': 'odom', 'poses': poses,
            'description': 'Development terminal approach; physical start requested, clearance/feasibility unvalidated.'}


def terminal_path(reference, distance, family, amplitude, turn_offset):
    points = tail_points(reference, distance); goal = reference['poses'][-1]
    if family not in FAMILIES:
        raise ValueError('unknown terminal family')
    if family not in ('reference-tail', 'direct-goal'):
        start = points[0]; end = (goal['x'], goal['y']); length = math.dist(start, end)
        heading = math.atan2(points[1][1] - start[1], points[1][0] - start[0])
        if family == 'terminal-turn':
            heading += turn_offset
        points = base.hermite(start, end, (length * math.cos(heading), length * math.sin(heading)),
                              (length * math.cos(goal['yaw']), length * math.sin(goal['yaw'])))
        normal = (-(end[1] - start[1]) / length, (end[0] - start[0]) / length)
        if family in ('terminal-s-bend', 'terminal-dogleg'):
            for i, p in enumerate(points):
                u = i / (len(points) - 1)
                shape = (math.sin(2 * math.pi * u) * math.sin(math.pi * u)
                         if family == 'terminal-s-bend' else math.sin(math.pi * u)**2)
                points[i] = (p[0] + normal[0] * amplitude * shape,
                             p[1] + normal[1] * amplitude * shape)
    return as_path(points, goal)


def generate(output, count, seed, phase='development'):
    if phase != 'development':
        raise ValueError('unexecuted development candidates only')
    result = base.generate(output, count, seed); output = Path(output).resolve()
    upstream = output / 'base-route-generation-v2.json'; (output / 'registry.json').rename(upstream)
    rng = random.Random(f'roboboat-terminal-distance-v4:{seed}'); used = set(); strata = {}
    for index, cluster in enumerate(result['clusters']):
        family = FAMILIES[index % len(FAMILIES)]
        band, low, high = BANDS[(index // len(FAMILIES)) % len(BANDS)]
        rows = [r for r in result['rows'] if r['cluster_id'] == cluster['cluster_id']]
        first = rows[0]; g = first['geometry']; goal = first['goal']
        # Construct the same bounded legacy reference geometry even for direct
        # action mode. That reference is design metadata, never an executed path.
        reference = base.route(g['lane_x'], g['turn_y'], goal, g['terminal_length_m'],
            g['terminal_offset_rad'], g['curvature_amplitude_m'], first['family'])
        distance = rng.uniform(low, high); amplitude = rng.uniform(-.45, .45)
        turn = rng.uniform(-.6, .6); heading_offset = rng.uniform(-.75, .75)
        path = terminal_path(reference, distance, family, amplitude, turn)
        initial = path['poses'][0]
        start = {'x': initial['x'], 'y': initial['y'],
                 'yaw': math.atan2(math.sin(initial['yaw'] + heading_offset),
                                  math.cos(initial['yaw'] + heading_offset))}
        file = base.ROOT / 'packages/crane_ml/Tools/Performance/generated_populations' / output.name / (cluster['cluster_id'] + '-terminalv4.json')
        base.write(file, path)
        path_binding = {'path': str(file.relative_to(base.ROOT)), 'sha256': base.digest(file)}
        mapped = launch_seed(seed, index, used)
        for row in rows:
            row['reference_family'] = row['family']; row['family'] = family
            row['distance_band'] = band
            row['initial_pose_request'] = dict(start)
            row['initial_pose_units'] = {'frame': 'odom', 'x': 'm', 'y': 'm', 'yaw': 'rad'}
            row['initial_pose_cli_option'] = '--crane-roboboat-start-pose'
            row['seed'] = mapped; row['action_mode'] = 'navigate-to-pose' if family == 'direct-goal' else 'follow-path'
            row['geometry'].update(base.descriptors(path))
            row['geometry'].update(physical_start='Requested terminal-approach pose; scene height retained; unexecuted.',
                requested_initial_pose_varied=True, physical_initial_pose_varied=False,
                initial_pose_runtime_verified=False, reference_curve_tail_distance_m=distance,
                requested_start_to_goal_distance_m=math.dist((start['x'], start['y']), (goal['x'], goal['y'])),
                requested_heading_offset_rad=heading_offset, terminal_perturbation_amplitude_m=amplitude,
                terminal_turn_offset_rad=turn, reference_curve_tail_distance_is_executed_length=False)
            if family == 'direct-goal':
                row.pop('path_file', None); row['design_reference_curve'] = path_binding
            else:
                row['path_file'] = path_binding
        cluster['reference_family'] = cluster['family']; cluster['family'] = family; cluster['distance_band'] = band
        strata[f'{family}/{band}'] = strata.get(f'{family}/{band}', 0) + 1
    result.update(schema='roboboat-generated-development-population/v4',
        status='DEVELOPMENT_EXPLORATORY_TERMINAL_DISTANCE_CANDIDATE_UNEXECUTED',
        generator={'path': str(Path(__file__).resolve().relative_to(base.ROOT)), 'sha256': base.digest(Path(__file__))},
        dependencies=result['dependencies'] + [{'path': str(Path(base.__file__).resolve().relative_to(base.ROOT)), 'sha256': base.digest(Path(base.__file__))},
            {'path': str((base.ROOT / 'analysis/generate_roboboat_population_v3.py').relative_to(base.ROOT)), 'sha256': base.digest(base.ROOT / 'analysis/generate_roboboat_population_v3.py')}],
        base_route_generation={'path': str(upstream.relative_to(base.ROOT)), 'sha256': base.digest(upstream)},
        strata_counts=strata, reference_curve_tail_distance_bands_m=[{'band': n, 'limits': [a, b]} for n, a, b in BANDS],
        sampling='Round-robin six terminal families and three reference-tail distance strata; independently sampled continuous configuration parameters. Paired tolerances; no outcome input or selection.',
        platform_change='Requires qualified opt-in physical start initialization. Input geometry revision only; berth, public task, controller, sensors, physics and current launcher deadlines unchanged.',
        initial_pose_extension_qualified=False, independent_n_added_by_generation=0,
        launch_requirements='Exact-build/start-pose and full navigation/trace qualification, initial-pose receipt binding and population identity audit before revised development collection.',
        throughput_claim='No measured gain. Existing launcher still waits fixed worker cap; shorter action paths alone cannot remove that tail.')
    base.write(output / 'registry.json', result); return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True, type=Path)
    p.add_argument('--clusters', required=True, type=int); p.add_argument('--seed', required=True, type=int)
    a = p.parse_args(); value = generate(a.output, a.clusters, a.seed)
    print(json.dumps({'status': value['status'], 'geometry_draws': value['independent_geometry_draws'],
                      'variants': len(value['rows']), 'strata': value['strata_counts'], 'independent_n_added': 0}))
