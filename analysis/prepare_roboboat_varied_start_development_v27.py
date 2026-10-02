"""Declare the whole remaining outcome-blind varied-start development population."""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path

import run_roboboat_varied_start_development_v27 as collector
from roboboat_development_schedule_v27 import schedule
from roboboat_launch_mount_v24 import stage


def prepare(root, population, operational, qualification):
    root=Path(root).resolve();population=Path(population).resolve()
    operational=Path(operational).resolve();qualification=Path(qualification).resolve()
    if root!=collector.LAUNCH_PROJECT.parent or root.exists():raise ValueError('fresh exact development namespace required')
    prior=json.loads(operational.read_text())
    for record in prior['dependencies']:
        if collector.digest(Path(record['path']))!=record['sha256']:raise ValueError('parent operational closure changed')
    q=json.loads(qualification.read_text())
    if not q['fixed_two_case_parallel_navigation_qualified']:raise ValueError('actual source-reviewed concurrent navigation required')
    original=json.loads(population.read_text())
    if original['schema']!='roboboat-generated-development-population/v4':raise ValueError('original unexecuted terminal-distance development population required')
    rows,clusters,lanes,excluded=schedule(original,list(prior['origin_rows'].values()))
    root.mkdir(parents=True)
    mount=stage(collector.INSTRUMENTATION_PROJECT,collector.LAUNCH_PROJECT,rows,collector.ROOT)
    registry=copy.deepcopy(original)
    registry.update(status='DEVELOPMENT_EXPLORATORY_VARIED_START',rows=rows,clusters=clusters,
        independent_geometry_draws=len(clusters),physical_variants=len(rows),
        excluded_inspected_clusters=excluded,
        platform_qualification_scope='Exact v17 player: fixed six varied-start cases; fixed two concurrent ROS/navigation cases. No population reliability or timeout claim.',
        independent_n_added_by_generation=0,confirmation_n=0,replication_n=0)
    registry_path=root/'registry.json';collector.save(registry_path,registry)
    d={k:copy.deepcopy(v) for k,v in prior.items() if k not in ('dependencies','origin_rows','domain','port','resources','prior_declaration')}
    d.update(schema='roboboat-trace-qualified-development-declaration/v1',utc=datetime.now(timezone.utc).isoformat(),
        registry=str(registry_path),original_registry=str(population),rows=[r['id'] for r in rows],
        output_root=str(root/'captures'),schedule_seed=43227,lanes=lanes,
        resources=[{'domain':204,'port':11494},{'domain':205,'port':11495}],
        excluded_inspected_clusters=excluded,operational_origin_declaration=str(operational),
        parallel_qualification={'path':str(qualification),'sha256':collector.digest(qualification)},
        design='All remaining original development geometries, excluding BOTH variants of six inspected operational origins. Seeded geometry shuffle; paired variants consecutive within round-robin lanes. Every scheduled attempt retained, no quality retries, no outcome-based selection. This batch is not a study ceiling.',
        independent_sampling_unit='Geometry draw; tolerance variants, evidence levels and repeats contribute no additional independent N.',
        sampling_scope='DEVELOPMENT_EXPLORATORY only. Fresh confirmation/replication generated separately after actual paired endpoint/reliability/effect/power maturity.',
        platform_version=prior['platform_version']+'; source-reviewed shared FPS leases and distinct ROS domains/ports for two collection workers',
        prior_capture_roots=[str(collector.ROOT/'artifacts'/name/'captures') for name in (
            'roboboat-initial-pose-navigation-operational-v19-001',
            'roboboat-initial-pose-navigation-operational-v24-001',
            'roboboat-parallel-navigation-operational-v26-001')],
        independent_n_added=0,confirmation_n=0,replication_n=0,land_n_added=0,study_ceiling=None)
    paths={Path(r['path']).resolve() for r in prior['dependencies']}
    paths.update((population,operational,qualification,registry_path,Path(__file__).resolve(),Path(collector.__file__).resolve(),collector.LAUNCH_PROJECT/'launch-mount-manifest.json',collector.ROOT/'scripts/run_roboboat_hidden_render_v4.sh'))
    paths.update(collector.ROOT/'analysis'/name for name in ('export_roboboat_trace_qualified_v4.py',
        'roboboat_hidden_render_v4.py','roboboat_render_fps_lease_v1.py','probe_roboboat_parallel_players_v20.py',
        'roboboat_parallel_navigation_contract_v26.py','roboboat_development_schedule_v27.py',
        'review_roboboat_parallel_navigation_v26.py'))
    for item in mount['launch_files']+mount['routes']:
        paths.update(Path(item[k]['path']) for k in ('original','snapshot'))
    for row in rows:
        paths.update(collector.bound(row[k]).resolve() for k in ('path_file','task_contract') if k in row)
    d['dependencies']=[{'path':str(p),'sha256':collector.digest(p)} for p in sorted(paths)]
    collector.save(root/'declaration.json',d)
    collector.validate_declaration(d,root/'declaration.json')
    return d


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('root','population','operational','qualification'):p.add_argument('--'+name,required=True)
    a=p.parse_args();d=prepare(a.root,a.population,a.operational,a.qualification)
    print(json.dumps({'scheduled_geometries':len(d['rows'])//2,'scheduled_attempts':len(d['rows']),
        'bound_inputs':len(d['dependencies']),'confirmation_n':0,'replication_n':0}))
