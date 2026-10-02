"""Prepare six fixed zero-N navigation probes, without reading any outcomes."""
import argparse
import copy
import json
from pathlib import Path
from datetime import datetime, timezone

import run_roboboat_initial_pose_navigation_operational_v19 as collector
from generate_roboboat_population_v4 import FAMILIES

ROOT = collector.ROOT


def prepare(root, population, parent):
    root, population, parent = (Path(p).resolve() for p in (root, population, parent))
    if root.exists():
        raise FileExistsError('fresh operational namespace required')
    original = json.loads(population.read_text())
    if original['status'] != 'DEVELOPMENT_EXPLORATORY_TERMINAL_DISTANCE_CANDIDATE_UNEXECUTED':
        raise ValueError('unexecuted varied-start development population required')
    prior = json.loads(parent.read_text())
    # Retain/revalidate the full parent launch closure; no queued project edits.
    for item in prior['dependencies']:
        if collector.digest(Path(item['path'])) != item['sha256']:
            raise ValueError('parent launch closure changed')
    rows = []
    origins = {}
    for index, family in enumerate(FAMILIES):
        band = ('near', 'medium', 'far')[index % 3]
        eligible = [r for r in original['rows'] if r['family'] == family and
                    r['distance_band'] == band and r['id'].endswith('-v1')]
        origin = min(eligible, key=lambda r: r['id'])
        row = copy.deepcopy(origin)
        row['id'] = f'boat-start-navigation-v19-001-{index+1:02d}'
        origins[row['id']] = origin['id']
        rows.append(row)
    root.mkdir(parents=True)
    registry = copy.deepcopy(original)
    registry.update(status='NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N', rows=rows,
                    independent_geometry_draws=0, independent_n_added=0)
    registry_path = root/'registry.json'
    collector.save(registry_path, registry)
    d = {k: copy.deepcopy(v) for k, v in prior.items() if k != 'dependencies'}
    d.update(schema='roboboat-initial-pose-navigation-operational-declaration/v1',
        utc=datetime.now(timezone.utc).isoformat(), registry=str(registry_path),
        original_registry=str(population), rows=[r['id'] for r in rows], origin_rows=origins,
        output_root=str(root/'captures'), domain=200, port=11490,
        design='Fixed six first-lexical v1 origins, one per family, distance bands near/medium/far rotated by family index; all once, no retries, no outcomes used for selection.',
        sampling_scope='Operational initialization/full-navigation qualification only; these six geometry origins are inspected development, not untouched confirmation or replication.',
        platform_version=prior['platform_version']+'; opt-in varied physical starts on the same exact player, ROS routes read from bound public JSON',
        primary_operational_check=prior['primary_operational_check']+'; exactly one finite matching initialization receipt in exact worker log')
    paths = {Path(item['path']).resolve() for item in prior['dependencies']}
    paths.update((parent, population, registry_path, Path(__file__).resolve(),
                  Path(collector.__file__).resolve(), ROOT/'analysis/roboboat_initial_pose_contract_v1.py'))
    for row in rows:
        for name in ('path_file', 'task_contract'):
            if name in row:
                paths.add(collector.bound(row[name]).resolve())
    d['dependencies'] = [{'path': str(p), 'sha256': collector.digest(p)} for p in sorted(paths)]
    collector.save(root/'declaration.json', d)
    collector.validate_declaration(d, root/'declaration.json')
    return d


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', required=True); p.add_argument('--population', required=True)
    p.add_argument('--parent', required=True); a = p.parse_args()
    d = prepare(a.root, a.population, a.parent)
    print(json.dumps({'rows': d['rows'], 'origins': d['origin_rows'],
                      'bound_inputs': len(d['dependencies']), 'independent_n_added': 0}))
