"""Declare a once-only successor operational assay with isolated launch mounts."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import run_roboboat_parallel_navigation_operational_v26 as collector
from roboboat_launch_mount_v24 import stage


def prepare(root, parent):
    root, parent = Path(root).resolve(), Path(parent).resolve()
    if root != collector.LAUNCH_PROJECT.parent or root.exists():
        raise ValueError('fresh exact versioned operational root required')
    prior = json.loads(parent.read_text())
    if prior['schema'] != 'roboboat-isolated-mount-initial-pose-navigation-operational-declaration/v1':
        raise ValueError('original v19 declaration required, no outcome-based subset')
    for record in prior['dependencies']:
        if collector.digest(Path(record['path'])) != record['sha256']:
            raise ValueError('original operational closure changed')
    original = json.loads(Path(prior['original_registry']).read_text())
    by_id = {r['id']: r for r in original['rows']}
    rows = []; origins = {}
    for index, old_id in enumerate((prior['rows'][0], prior['rows'][-1])):
        origin = prior['origin_rows'][old_id]; row = copy.deepcopy(by_id[origin])
        row['id'] = f'boat-parallel-navigation-v26-001-{index+1:02d}'
        rows.append(row); origins[row['id']] = origin
    root.mkdir(parents=True)
    mount = stage(collector.INSTRUMENTATION_PROJECT, collector.LAUNCH_PROJECT, rows, collector.ROOT)
    registry = copy.deepcopy(original)
    registry.update(status='NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N', rows=rows,
                    independent_geometry_draws=0, independent_n_added=0)
    registry_path = root/'registry.json'; collector.save(registry_path, registry)
    d = {k: copy.deepcopy(v) for k, v in prior.items() if k != 'dependencies'}
    d.update(schema='roboboat-parallel-navigation-operational-declaration/v26',
        utc=datetime.now(timezone.utc).isoformat(), registry=str(registry_path),
        rows=[r['id'] for r in rows], origin_rows=origins, output_root=str(root/'captures'),
        resources={r['id']: {'domain': 202+i, 'port': 11492+i} for i,r in enumerate(rows)},
        design='First and last origins of the fixed v24 schedule (FollowPath and direct-goal), chosen by action mode before this parallel assay. Both once on distinct domains/ports/bundles. Prior origins remain inspected operational development; zero N. No retries or outcomes-based subset.',
        platform_version=prior['platform_version']+'; unchanged runtime Tools copied into isolated Docker mount with exact route JSON; compiler sources/player unchanged',
        prior_declaration={'path': str(parent), 'sha256': collector.digest(parent)},
        repaired_scope='Concurrent full ROS/navigation isolation only; same player and runtime Tools, separate FPS leases and mount; no physics/control/task/sensor/timer/endpoint change')
    paths = {Path(record['path']).resolve() for record in prior['dependencies']}
    paths.update((parent, registry_path, Path(__file__).resolve(), Path(collector.__file__).resolve(),
                  collector.ROOT/'analysis/roboboat_launch_mount_v24.py',
                  collector.LAUNCH_PROJECT/'launch-mount-manifest.json',
                  collector.ROOT/'scripts/run_roboboat_hidden_render_v4.sh'))
    paths.update(collector.ROOT/'analysis'/name for name in ('roboboat_hidden_render_v4.py','roboboat_render_fps_lease_v1.py','probe_roboboat_parallel_players_v20.py','roboboat_parallel_navigation_contract_v26.py'))
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
