#!/usr/bin/env python3
"""Execute frozen ordered B2/B4 pairs with no poor-answer or technical retries.

Uses the existing evidence builder, unchanged strong B2 call, and current B4 v7.
Requires an explicit scientific freeze; preparation alone cannot launch a method.
"""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
from run_evidence_calibration_b2_pilot import ROOT,_materialize,run
from realize_evidence_calibrated_explanation_v7 import realize


def write_once(path,record):
    raw=json.dumps(record,indent=2,sort_keys=True)+'\n'
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_text()!=raw:raise RuntimeError('Retained result differs')
    else:path.write_text(raw)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--freeze',type=Path,required=True)
    parser.add_argument('--maximum-candidates',type=int)
    parser.add_argument('--look',choices=['FIRST','FINAL'],default='FIRST')
    args=parser.parse_args()
    freeze=json.loads(args.freeze.read_text())
    if freeze.get('status')!='FROZEN_BEFORE_FIRST_CONFIRMATORY_SEMANTIC_OUTPUT':raise RuntimeError('No prospective scientific freeze')
    for name,digest in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise RuntimeError('Frozen source changed: '+name)
    ledger=json.loads((ROOT/'manifests/study/diagnostic-sequential-error-ledger-v2.json').read_text())
    allocation=next(a for a in ledger['allocations'] if a['allocation_id']==freeze['alpha_allocation_id'])
    if allocation['status']!='CONSUMED' or allocation['campaign_id']!=freeze['study_id']:raise RuntimeError('Alpha not prospectively bound')
    if allocation.get('freeze_sha256')!=hashlib.sha256(args.freeze.read_bytes()).hexdigest():raise RuntimeError('Declaration differs from the prospectively bound alpha allocation')
    pool=json.loads((ROOT/freeze['candidate_allocation_path']).read_text())
    exceptions=json.loads((ROOT/'manifests/study/evidence-calibration-handoff-freshness-exceptions-v1.json').read_text())
    excluded={e['run_id'] for e in exceptions['exceptions']}
    rows=[r for r in pool['configurations'] if r['stage']=='confirmation' and r['run_id'] not in excluded]
    rows=rows[:freeze['acquired_candidate_cap']]
    if args.maximum_candidates is not None:rows=rows[:args.maximum_candidates]
    ontology=json.loads((ROOT/'configs/evidence_calibration_claim_contracts_v1.json').read_text())
    out=ROOT/'analysis/results/confirmation'/freeze['study_id'];out.mkdir(parents=True,exist_ok=True)
    target_n=freeze['first_look_n'] if args.look=='FIRST' else freeze['valid_paired_episode_n']
    if args.look=='FINAL':
        first=json.loads((out/'look-600'/'primary-analysis-v1.json').read_text())
        if not first.get('continuation_required',False):raise RuntimeError('The frozen futility rule ended this study; no further semantic outputs')
    models=ROOT/'model_outputs'/freeze['study_id']
    pilot=copy.deepcopy(json.loads((ROOT/'research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json').read_text()))
    pilot.update(pilot_id=freeze['study_id'],development_only=False,study_stage='CONFIRMATION',data_split='final',confirmation_alpha=freeze['alpha'])
    pilot['selection']['episode_ids']=[r['run_id'] for r in rows]
    schedule=dict(cohorts=[dict(runs=[dict(r,family='transient-compensation' if 'recovery' in r['response_profile'] else 'persistent-discrepancy') for r in rows])])
    # Run-local schedule is bookkeeping; all candidate identities precede the freeze.
    (out/'pilot.json').write_text(json.dumps(pilot,indent=2)+'\n')
    (out/'schedule.json').write_text(json.dumps(schedule,indent=2)+'\n')
    complete=0;accounting=[]
    for row in rows:
        if complete>=target_n:break
        run_id=row['run_id'];status=models/'status'/(run_id+'.json')
        intent=models/'status'/(run_id+'.intent.json')
        if status.exists():
            record=json.loads(status.read_text());accounting.append(record);complete+=record['complete_pair'];continue
        capture=ROOT/'data/evaluator_only/analysis/handoff-fresh-candidate-collection-v1'/(run_id+'.json')
        if not capture.exists():print(json.dumps(dict(waiting_for_physical_capture=run_id,complete_pairs=complete)));break
        physical=json.loads(capture.read_text())
        if not physical.get('technical_valid',False):
            record=dict(run_id=run_id,complete_pair=False,disposition='PHYSICAL_TECHNICAL_INVALID_NO_METHOD_CALL')
            write_once(status,record);accounting.append(record);continue
        reference=json.loads((ROOT/f'data/evaluator_only/final/{run_id}/command-motion-independent-reference-v1.json').read_text())
        if reference['result']['disposition']!='supported':
            record=dict(run_id=run_id,complete_pair=False,disposition='OUTSIDE_FROZEN_DISCREPANCY_POPULATION_NO_METHOD_CALL')
            write_once(status,record);accounting.append(record);continue
        if intent.exists():raise RuntimeError("Unresolved prior episode intent; no automatic semantic retry: "+run_id)
        write_once(intent,dict(run_id=run_id,study_id=freeze["study_id"],freeze_sha256=hashlib.sha256(args.freeze.read_bytes()).hexdigest(),semantic_attempt_started=True))
        conditions=[run_id+f'-E{i}' for i in range(4)];validation=dict(episodes=[dict(run_id=run_id,condition_ids=conditions,condition_packet_sha256s=[])])
        b4_failures=[]
        for condition in conditions:
            entry,_,family=_materialize(ROOT,pilot,schedule,condition)
            validation['episodes'][0]['condition_packet_sha256s'].append(entry['condition']['method_packet_sha256'])
            try:
                answer=realize(ontology,entry,dict(question_id=family+'-question-v1-development',failure_premise=True,required_mechanism_families=['command_motion']))
                answer.update(development_only=False,study_stage='CONFIRMATION',study_id=freeze['study_id'],family=family,freeze_sha256=hashlib.sha256(args.freeze.read_bytes()).hexdigest())
                write_once(models/'b4'/(condition+'.json'),answer)
            except Exception as e:b4_failures.append(dict(condition_id=condition,error=type(e).__name__+': '+str(e)))
        validpath=out/(run_id+'-input-validation.json');write_once(validpath,validation)
        def call(condition):
            # Cache retains every failed attempt. Existing failed logical requests cannot retry.
            try:
                result=run(SimpleNamespace(condition_id=condition,pilot=out/'pilot.json',schedule=out/'schedule.json',validation=validpath,
                    cache=models/'cache',output_root=models/'b2',timeout_seconds=freeze['b2_timeout_seconds']))
                return dict(condition_id=condition,status='VALID')
            except Exception as e:return dict(condition_id=condition,status='TECHNICAL_FAILURE',error=type(e).__name__+': '+str(e))
        with ThreadPoolExecutor(max_workers=freeze['model_concurrency']) as pool_executor:calls=list(pool_executor.map(call,conditions))
        record=dict(run_id=run_id,study_stage='CONFIRMATION',complete_pair=not b4_failures and all(c['status']=='VALID' for c in calls),b2_calls=calls,b4_technical_failures=b4_failures,quality_driven_retries=0)
        write_once(status,record);accounting.append(record);complete+=record['complete_pair']
        print(json.dumps(dict(run_id=run_id,complete_pair=record['complete_pair'],complete_paired_episode_n=complete)),flush=True)
    (out/('execution-accounting-'+args.look+'.json')).write_text(json.dumps(dict(study_id=freeze['study_id'],look=args.look,complete_paired_episode_n=complete,planned_valid_n=target_n,complete=complete==target_n,records=accounting),indent=2)+'\n')

if __name__=='__main__':main()
