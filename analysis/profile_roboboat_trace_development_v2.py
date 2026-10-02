"""Describe the declared trace-qualified development batch; never explanation scores."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from generate_roboboat_population_v1 import digest
from roboboat_temporal_certificate_v2 import certificate


def binding(p):return {'path':str(Path(p).resolve()),'sha256':digest(Path(p))}


def profile(declaration_path):
    declaration_path=Path(declaration_path).resolve();d=json.loads(declaration_path.read_text())
    if d['schema']!='roboboat-trace-qualified-development-declaration/v1' or d['confirmation_n']!=0:
        raise ValueError('trace-qualified development declaration required')
    registry_path=Path(d['registry']);registry=json.loads(registry_path.read_text())
    bound={v['path']:v['sha256'] for v in d['dependencies']}
    if digest(registry_path)!=bound[str(registry_path)]:raise ValueError('registry changed')
    by_id={r['id']:r for r in registry['rows']};root=Path(d['output_root'])
    rows=[];states=Counter();families=defaultdict(Counter);complete=defaultdict(set)
    dependencies=[binding(declaration_path),binding(registry_path),binding(__file__),binding(certificate.__code__.co_filename)]
    for identifier in d['rows']:
        row=by_id[identifier];folder=root/identifier
        published=folder/'capture-export-terminal-trace-v4.json';original=folder/'capture-attempt.json'
        record={'id':identifier,'cluster_id':row['cluster_id'],'family':row['family'],'status':'UNATTEMPTED'}
        terminal=published if published.exists() else original
        if not terminal.exists():
            if (folder/'capture-intent.json').exists():record['status']='RUNNING'
            rows.append(record);continue
        value=json.loads(terminal.read_text());dependencies.append(binding(terminal))
        if value['registry_sha256']!=digest(registry_path) or value['row']!=row:raise ValueError('recording identity mismatch')
        record['status']=value['status'];record['error']=value.get('error')
        if value['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT':
            if not published.exists():raise ValueError('admitted recording has no validated export terminal')
            if value.get('operational_replay')is not False or value['platform_version']!=d['platform_version']:raise ValueError('fresh revised-platform recording required')
            if value['prospective_declaration']!=binding(declaration_path):raise ValueError('admission declaration mismatch')
            capture=json.loads(original.read_text())
            if binding(original)!=value['original_capture_terminal'] or not all(capture['checks'].values()):raise ValueError('admission terminal changed or incomplete')
            for item in value['raw_sources']:
                if binding(item['path'])!=item:raise ValueError('raw source changed')
                dependencies.append(item)
            packet_path=folder/value['export_directory']/'method_packets/L2.json'
            dependencies.append(binding(packet_path));cert=certificate(json.loads(packet_path.read_text()))
            record.update(action_status=cert['action']['status'],sampled_task_support=cert['sampled_task_support'],
                component_support=cert['component_support'],complete_sampled_window=cert['coverage']['complete_sampled_window'],
                witness_components=sorted(cert['witnesses']),worker_valid_original=value['worker_valid_original'],
                stale_actions_observed=value['stale_actions_observed'])
            complete[row['cluster_id']].add(identifier);states[cert['sampled_task_support']]+=1
            families[row['family']][cert['sampled_task_support']]+=1
        elif value['status']!='TECHNICAL_FAILURE':raise ValueError('unexpected trace development disposition')
        rows.append(record)
    return {'schema':'roboboat-trace-development-profile/v2','phase':'DEVELOPMENT_EVIDENCE_DISTRIBUTION_ONLY',
        'dependencies':dependencies,'declared_attempts':len(d['rows']),'rows':rows,
        'recording_dispositions':dict(Counter(r['status'] for r in rows)),
        'valid_recordings':sum(r['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT' for r in rows),
        'complete_geometry_pairs':sum(set(c['rows'])==complete[c['cluster_id']] for c in registry['clusters']),
        'L2_sampled_task_recording_counts':dict(states),'L2_family_recording_counts':{k:dict(v) for k,v in families.items()},
        'selection':'Every prospectively scheduled row retained, including technical failures and missing/unattempted records; no method answers or scores read.',
        'counting':'One geometry draw is the independent candidate unit; tolerance variants/evidence levels/repeats add no N. No scored independent method pair is asserted.',
        'platform_version':d['platform_version'],'confirmation_n':0,'replication_n':0,'land_n_added':0,'inference':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('declaration',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=profile(a.declaration)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('declared_attempts','recording_dispositions','valid_recordings','complete_geometry_pairs','L2_sampled_task_recording_counts')}))
