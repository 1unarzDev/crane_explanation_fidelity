#!/usr/bin/env python3
"""Prepare blinded frozen confirmation scoring only after all planned pairs complete."""
import argparse
import copy
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from run_evidence_calibration_b2_pilot import ROOT,_materialize


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',required=True,type=Path);parser.add_argument('--look',choices=['FIRST','FINAL'],default='FIRST');args=parser.parse_args()
    freeze=json.loads(args.freeze.read_text())
    if freeze['status']!='FROZEN_BEFORE_FIRST_CONFIRMATORY_SEMANTIC_OUTPUT':raise RuntimeError('Unfrozen study')
    out=ROOT/'analysis/results/confirmation'/freeze['study_id'];models=ROOT/'model_outputs'/freeze['study_id']
    target_n=freeze['first_look_n'] if args.look=='FIRST' else freeze['valid_paired_episode_n']
    accounting=json.loads((out/('execution-accounting-'+args.look+'.json')).read_text())
    if not accounting['complete'] or accounting['complete_paired_episode_n']!=target_n:raise RuntimeError('All planned output pairs must complete before blind scoring')
    pilot=json.loads((out/'pilot.json').read_text());schedule=json.loads((out/'schedule.json').read_text())
    sources=json.loads((ROOT/'analysis/results/evidence-calibration-handoff-development/pilot-cases-v1.json').read_text())['source_assets']
    cases=[];joins=[]
    for row in accounting['records']:
        if not row['complete_pair']:continue
        run_id=row['run_id'];ref=json.loads((ROOT/f'data/evaluator_only/final/{run_id}/command-motion-independent-reference-v1.json').read_text())['result']
        realized='measured_response_recovery' if ref['response_recovery_interval_s'] else 'persistent_command_motion_discrepancy'
        for level in range(4):
            condition=run_id+f'-E{level}';entry,_,family=_materialize(ROOT,pilot,schedule,condition)
            packet=copy.deepcopy(entry['method_packet']);evidence=packet['evidence']
            units=['state the observed navigation action state or outcome, preserving nonterminal outcome uncertainty']
            if 'behavior_tree_transitions' in evidence:
                if evidence['behavior_tree_transitions']['execution_sequence']['source_qualified_wait_recovery_count']:
                    units.append('state the retained source-qualified recovery sequence')
                else:units.append('state that no source-qualified Wait recovery was observed')
            if 'delivered_command_stream' in evidence:units.append('state the delivered command observation')
            if 'command_motion_computation' in evidence:
                units.append('state the supported command-to-measured-motion discrepancy and interval')
                if ref['response_recovery_interval_s'] is not None:units.append('state the later measured-response recovery when supported')
            for value in evidence.values():
                if 'samples' not in value:continue
                samples=value.pop('samples');groups={}
                for s in samples:groups.setdefault(math.floor(s['offset_s']),[]).append(s['planar_speed_mps'])
                value['deterministic_raw_sample_summary']=dict(sample_count=len(samples),window_seconds=1,
                    offset_range_s=[min(s['offset_s'] for s in samples),max(s['offset_s'] for s in samples)] if samples else None,
                    windows=[dict(interval_s=[i,i+1],count=len(v),min_speed_mps=min(v),max_speed_mps=max(v),median_speed_mps=statistics.median(v)) for i,v in sorted(groups.items())])
            for method,directory in [('B2','b2'),('B4v7','b4')]:
                path=models/directory/(condition+'.json');answer=json.loads(path.read_text())
                identifier='cf-'+hashlib.sha256((freeze['study_id']+condition+method).encode()).hexdigest()[:32]
                cases.append(dict(case_id=identifier,response_text=answer['answer'],reference=dict(robot_visible_evidence=packet,
                    required_units={f'u{i:02}':u for i,u in enumerate(units)},required_limitations=['do not identify a unique hidden physical cause','chronology does not establish outcome causation'])))
                joins.append(dict(response_id=identifier,method_id=method,condition_id=condition,configuration_id=entry['condition']['configuration_id'],
                    family=family,realized_family=realized,run_id=run_id,source_path=str(path.relative_to(ROOT)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    random.Random(freeze['study_id']+'-blind-order').shuffle(cases)
    if len(cases)!=8*target_n:raise RuntimeError('Incomplete blind input')
    out=out/('look-'+str(target_n));out.mkdir(exist_ok=True)
    for name,d in [('blind-cases-v1.json',dict(scope='CONFIRMATION',cases=cases,source_assets=sources)),('join-key-v1.json',dict(scope='CONFIRMATION_KEY_NOT_SENT_TO_JUDGE',entries=joins))]:
        raw=json.dumps(d,indent=2)+'\n';p=out/name
        if p.exists() and p.read_text()!=raw:raise RuntimeError('Retained scoring inputs differ')
        if not p.exists():p.write_text(raw)
    print(json.dumps(dict(blind_answers=len(cases),independent_episode_n=target_n,outcomes_joined=False)))

if __name__=='__main__':main()
