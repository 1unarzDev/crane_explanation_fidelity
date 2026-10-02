#!/usr/bin/env python3
"""Outcome-inclusive development evidence description; no explanation scores/tests."""
import argparse
from collections import Counter,defaultdict
import json
from pathlib import Path
from build_roboboat_terminal_batch import save,digest
from roboboat_temporal_certificate_v2 import certificate


def binding(path):return {'path':str(Path(path).resolve()),'sha256':digest(Path(path))}


def profile(registry_path,capture_root):
    registry_path=Path(registry_path);capture_root=Path(capture_root)
    registry=json.loads(registry_path.read_text())
    if registry['status']!='DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION':raise ValueError('development required')
    rows=[];dependencies=[binding(registry_path),binding(__file__),binding(Path(certificate.__code__.co_filename))]
    complete=defaultdict(set);states=Counter(); components=defaultdict(Counter); families=defaultdict(Counter)
    for row in registry['rows']:
        folder=capture_root/row['id'];terminal=folder/'capture-export-terminal-v2.json'
        if not terminal.exists():terminal=folder/'capture-attempt.json'
        if not terminal.exists():rows.append({'id':row['id'],'status':'PENDING_OR_RUNNING'});continue
        d=json.loads(terminal.read_text());dependencies.append(binding(terminal))
        if d['registry_sha256']!=digest(registry_path) or d['row']!=row:raise ValueError('population identity mismatch')
        record={'id':row['id'],'cluster_id':row['cluster_id'],'family':row['family'],'status':d['status']}
        if d['status']=='VALID_DEVELOPMENT':
            complete[row['cluster_id']].add(row['id'])
            packet_path=folder/d.get('export_directory','.')/'method_packets/L2.json'
            dependencies.append(binding(packet_path)); c=certificate(json.loads(packet_path.read_text()))
            record.update(action_status=c['action']['status'],sampled_task_support=c['sampled_task_support'],
                component_support=c['component_support'],complete_sampled_window=c['coverage']['complete_sampled_window'],
                violation_witness_components=sorted(c['witnesses']),
                observed_transition_components=sorted(k for k,v in c['crossing_observation_brackets'].items() if v),
                radial_error_growth_m=c['radial_error_growth_m'])
            states[c['sampled_task_support']]+=1;families[row['family']][c['sampled_task_support']]+=1
            for key,value in c['component_support'].items():components[key][value]+=1
        rows.append(record)
    valid=sum(r['status']=='VALID_DEVELOPMENT' for r in rows)
    return {'schema':'roboboat-development-evidence-profile/v1','phase':'EXPLORATORY_EVIDENCE_MECHANISMS_ONLY',
        'dependencies':dependencies,'rows':rows,'valid_recordings':valid,
        'complete_geometry_pairs':sum(set(c['rows'])==complete[c['cluster_id']] for c in registry['clusters']),
        'L2_sampled_task_recording_counts':dict(states),'L2_component_recording_counts':{k:dict(v) for k,v in components.items()},
        'L2_family_recording_counts':{k:dict(v) for k,v in families.items()},
        'counting':'Counts describe recordings, not independent method comparisons; one geometry draw is one cluster.',
        'selection':'All registry rows, including technical failures/pending; no method answers or annotations inspected.',
        'confirmation_n':0,'replication_n':0,'land_n_added':0,'inference':False}


def main():
    p=argparse.ArgumentParser();p.add_argument('--registry',required=True,type=Path);p.add_argument('--capture-root',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError('immutable profile output exists')
    d=profile(a.registry,a.capture_root);save(a.output,d)
    print(json.dumps({k:d[k] for k in ('valid_recordings','complete_geometry_pairs','L2_sampled_task_recording_counts','L2_component_recording_counts')}))

if __name__=='__main__':main()
