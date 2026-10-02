"""Declare a once-only successor operational assay with isolated launch mounts."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import run_roboboat_initial_pose_navigation_operational_v24 as collector
from roboboat_launch_mount_v24 import stage


def prepare(root, parent):
    root, parent = Path(root).resolve(), Path(parent).resolve()
    if root != collector.LAUNCH_PROJECT.parent or root.exists():
        raise ValueError('fresh exact versioned operational root required')
    prior = json.loads(parent.read_text())
    if prior['schema'] != 'roboboat-initial-pose-navigation-operational-declaration/v1':
        raise ValueError('original v19 declaration required, no outcome-based subset')
    for record in prior['dependencies']:
        if collector.digest(Path(record['path'])) != record['sha256']:
            raise ValueError('original operational closure changed')
    original = json.loads(Path(prior['original_registry']).read_text())
    by_id = {r['id']: r for r in original['rows']}
    rows = []; origins = {}
    for index, old_id in enumerate(prior['rows']):
        origin = prior['origin_rows'][old_id]; row = copy.deepcopy(by_id[origin])
        row['id'] = f'boat-start-navigation-v24-001-{index+1:02d}'
        rows.append(row); origins[row['id']] = origin
    root.mkdir(parents=True)
    mount = stage(collector.INSTRUMENTATION_PROJECT, collector.LAUNCH_PROJECT, rows, collector.ROOT)
    registry = copy.deepcopy(original)
    registry.update(status='NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N', rows=rows,
                    independent_geometry_draws=0, independent_n_added=0)
    registry_path = root/'registry.json'; collector.save(registry_path, registry)
    d = {k: copy.deepcopy(v) for k, v in prior.items() if k != 'dependencies'}
    d.update(schema='roboboat-isolated-mount-initial-pose-navigation-operational-declaration/v1',
        utc=datetime.now(timezone.utc).isoformat(), registry=str(registry_path),
        rows=[r['id'] for r in rows], origin_rows=origins, output_root=str(root/'captures'),
        domain=201, port=11491,
        design='Same six fixed origins/order as v19, all once under a prospectively bound isolated-launch-mount successor. No subset based on outcomes or method wins, no retries; old failures unchanged.',
        platform_version=prior['platform_version']+'; unchanged runtime Tools copied into isolated Docker mount with exact route JSON; compiler sources/player unchanged',
        prior_declaration={'path': str(parent), 'sha256': collector.digest(parent)},
        repaired_scope='Launcher repository-root path translation only; no physics/control/task/sensor/timer/endpoint change')
    paths = {Path(record['path']).resolve() for record in prior['dependencies']}
    paths.update((parent, registry_path, Path(__file__).resolve(), Path(collector.__file__).resolve(),
                  collector.ROOT/'analysis/roboboat_launch_mount_v24.py',
                  collector.LAUNCH_PROJECT/'launch-mount-manifest.json'))
    for item in mount['launch_files'] + mount['routes']:
        paths.update(Path(item[kind]['path']) for kind in ('original', 'snapshot'))
    d['dependencies'] = [{'path': str(p), 'sha256': collector.digest(p)} for p in sorted(paths)]
    collector.save(root/'declaration.json', d)
    collector.validate_declaration(d, root/'declaration.json')
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--root', required=True); p.add_argument('--parent', required=True)
    a = p.parse_args(); d = prepare(a.root, a.parent)
    print(json.dumps({'fixed_rows': len(d['rows']), 'bound_inputs': len(d['dependencies']), 'independent_n_added': 0}))
