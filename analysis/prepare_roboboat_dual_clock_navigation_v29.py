"""Declare fixed zero-N incomplete-window replays after an exact live collection."""
import argparse
import copy
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil

import run_roboboat_dual_clock_navigation_operational_v29 as collector
from roboboat_launch_mount_v24 import stage,binding
from roboboat_after_collection_v29 import predecessor_ready


def prepare(root,parent,candidate,predecessor,pid,start):
    root,parent,candidate,predecessor=[Path(p).resolve() for p in (root,parent,candidate,predecessor)]
    if root!=collector.LAUNCH_PROJECT.parent or root.exists():raise ValueError('fresh exact operational namespace required')
    prior=json.loads(parent.read_text())
    for r in prior['dependencies']:
        if binding(r['path'])!=r:raise ValueError('parent source closure changed')
    c=json.loads(candidate.read_text())
    for key in ('original','original_snapshot','candidate','helper','helper_snapshot','builder'):
        if binding(c[key]['path'])!=c[key]:raise ValueError('capture candidate binding changed')
    original=json.loads(Path(prior['original_registry']).read_text());by_id={r['id']:r for r in original['rows']}
    origins=['boat-geom-42007-00062-v2','boat-geom-42007-00066-v2']
    rows=[];mapping={}
    for index,origin in enumerate(origins):
        row=copy.deepcopy(by_id[origin]);row['id']=f'boat-dual-clock-navigation-v29-001-{index+1:02d}'
        rows.append(row);mapping[row['id']]=origin
    before={'declaration':binding(predecessor),'process':{'pid':pid,'start':start}}
    predecessor_ready(before)
    root.mkdir(parents=True)
    mount=stage(collector.INSTRUMENTATION_PROJECT,collector.LAUNCH_PROJECT,rows,collector.ROOT)
    fixture=collector.LAUNCH_PROJECT/'Tools/Performance/nav2_follow_path_fixture_capture_v15.py'
    old=next(r for r in mount['launch_files'] if r['snapshot']['path']==str(fixture))
    prior_fixture=copy.deepcopy(old)
    shutil.copy2(c['candidate']['path'],fixture)
    old.update(original=c['candidate'],snapshot=binding(fixture),capture_only_candidate=True)
    helper=fixture.parent/'roboboat_post_result_clock_v28.py';shutil.copy2(c['helper_snapshot']['path'],helper)
    mount['launch_files'].append({'original':c['helper_snapshot'],'snapshot':binding(helper)})
    mount.update(runtime_fixture_modified=True,prior_fixture=prior_fixture,capture_only_candidate=binding(candidate),
        scope='Capture-only dual-clock fixture and helper in isolated launch mount; exact original compiled player/physics/navigation/task retained. Runtime qualification pending.')
    base_manifest=collector.LAUNCH_PROJECT/'launch-mount-manifest.json'
    base_manifest.rename(collector.LAUNCH_PROJECT/'launch-mount-base-v24.json')
    collector.save(base_manifest,mount)
    registry=copy.deepcopy(original);registry.update(status='NONSTUDY_OPERATIONAL_REPLAYS_ZERO_INDEPENDENT_N',rows=rows,independent_geometry_draws=0,independent_n_added=0)
    registry_path=root/'registry.json';collector.save(registry_path,registry)
    d={k:copy.deepcopy(v) for k,v in prior.items() if k not in ('dependencies','origin_rows','domain','port','resources')}
    d.update(schema='roboboat-dual-clock-navigation-operational-declaration/v29',utc=datetime.now(timezone.utc).isoformat(),
        registry=str(registry_path),rows=[r['id'] for r in rows],origin_rows=mapping,output_root=str(root/'captures'),
        resources={r['id']:{'domain':206+i,'port':11496+i} for i,r in enumerate(rows)},
        predecessor=before,capture_candidate=binding(candidate),
        design='Fixed two once-only v2 tolerance development replays whose original raw windows were incomplete. Selection is disclosed measurement qualification, not method outcome selection; zero independent N. Await exact v27 full terminal before starting two workers; no extra concurrent players, no retries.',
        platform_version=prior['platform_version']+'; isolated dual-clock post-result capture v28: min8 wall and8 simulator seconds, max120 wall; worker480 outer660; same compiled v17 player, physics/navigation/task/endpoint',
        repaired_scope='Observation-window stopping only; action duration310, task five-second first-post-result dwell and all original admission gates retained.')
    paths={Path(r['path']).resolve() for r in prior['dependencies']}
    paths.update((parent,candidate,predecessor,registry_path,Path(__file__).resolve(),Path(collector.__file__).resolve(),collector.LAUNCH_PROJECT/'launch-mount-manifest.json',collector.LAUNCH_PROJECT/'launch-mount-base-v24.json'))
    paths.update(collector.ROOT/'analysis'/name for name in ('roboboat_after_collection_v29.py','roboboat_post_result_clock_v28.py'))
    for item in mount['launch_files']+mount['routes']:
        paths.update(Path(item[k]['path']) for k in ('original','snapshot'))
    for row in rows:
        paths.update(collector.bound(row[k]).resolve() for k in ('path_file','task_contract') if k in row)
    for key in ('original','original_snapshot','candidate','helper','helper_snapshot','builder'):paths.add(Path(c[key]['path']))
    d['dependencies']=[binding(p) for p in sorted(paths)]
    collector.save(root/'declaration.json',d);collector.validate_declaration(d,root/'declaration.json')
    return d


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('root','parent','candidate','predecessor'):p.add_argument('--'+key,required=True)
    for key in ('pid','start'):p.add_argument('--'+key,type=int,required=True)
    a=p.parse_args();d=prepare(a.root,a.parent,a.candidate,a.predecessor,a.pid,a.start)
    print(json.dumps({'fixed_cases':len(d['rows']),'bound_inputs':len(d['dependencies']),'independent_n_added':0}))
