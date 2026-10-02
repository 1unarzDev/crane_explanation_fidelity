#!/usr/bin/env python3
"""Bounded cross-episode confirmation scheduler.

Uses the frozen packet construction, B2 call primitive, B4 realization and
failure policy from the existing runner, but keeps a global B2 queue occupied.
The scheduler never launches more new candidate episodes in a batch than the
number of complete pairs still required for the registered look.
"""
import argparse, copy, hashlib, json, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from types import SimpleNamespace
from run_evidence_calibration_b2_pilot import ROOT, _materialize, run
from realize_evidence_calibrated_explanation_v7 import realize


def write_once(path, record):
    raw=json.dumps(record, indent=2, sort_keys=True)+'\n'; path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text()!=raw: raise RuntimeError('Retained result differs: '+str(path))
    else: path.write_text(raw)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--freeze',required=True,type=Path); ap.add_argument('--look',choices=['FIRST'],default='FIRST')
    ap.add_argument('--b2-concurrency',type=int,default=12)
    ap.add_argument('--episode-batch',type=int,default=24)
    ap.add_argument('--poll-seconds',type=float,default=20)
    args=ap.parse_args()
    freeze=json.loads(args.freeze.read_text())
    if freeze.get('status')!='FROZEN_BEFORE_FIRST_CONFIRMATORY_SEMANTIC_OUTPUT': raise RuntimeError('No prospective freeze')
    for name,digest in freeze['source_sha256'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest: raise RuntimeError('Frozen source changed: '+name)
    if args.b2_concurrency<1 or args.episode_batch<1: raise ValueError('positive concurrency required')
    pool=json.loads((ROOT/freeze['candidate_allocation_path']).read_text())
    exceptions=json.loads((ROOT/'manifests/study/evidence-calibration-handoff-freshness-exceptions-v1.json').read_text())
    excluded={e['run_id'] for e in exceptions['exceptions']}
    rows=[r for r in pool['configurations'] if r['stage']=='confirmation' and r['run_id'] not in excluded][:freeze['acquired_candidate_cap']]
    out=ROOT/'analysis/results/confirmation'/freeze['study_id']; models=ROOT/'model_outputs'/freeze['study_id']; out.mkdir(parents=True,exist_ok=True)
    target=freeze['first_look_n']; accounting_path=out/'execution-accounting-FIRST.json'
    pilot=copy.deepcopy(json.loads((ROOT/'research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json').read_text()))
    pilot.update(pilot_id=freeze['study_id'],development_only=False,study_stage='CONFIRMATION',data_split='final',confirmation_alpha=freeze['alpha'])
    ontology=json.loads((ROOT/'configs/evidence_calibration_claim_contracts_v1.json').read_text())
    accounting=[]
    for row in rows:
        status=models/'status'/(row['run_id']+'.json')
        if status.exists(): accounting.append(json.loads(status.read_text()))
        else: break
    complete=sum(bool(r.get('complete_pair')) for r in accounting)
    # Existing terminal records are authoritative; do not reinterpret their errors.
    print(json.dumps(dict(stage='CONTINUOUS_QUEUE',existing_records=len(accounting),complete_pairs=complete,target=target,b2_concurrency=args.b2_concurrency,episode_batch=args.episode_batch)),flush=True)
    schedule_rows=[]
    for r in rows: schedule_rows.append(dict(r,family='transient-compensation' if 'recovery' in r['response_profile'] else 'persistent-discrepancy'))
    schedule=dict(cohorts=[dict(runs=schedule_rows)])
    pilot['selection']['episode_ids']=[r['run_id'] for r in rows]
    prep=ROOT/'analysis/preparation/frozen-land-confirmation-2026-10-01/continuous-queue'; prep.mkdir(parents=True,exist_ok=True)
    pilot_path=prep/'pilot.json'; schedule_path=prep/'schedule.json'
    if pilot_path.exists(): pilot=json.loads(pilot_path.read_text())
    else: pilot_path.write_text(json.dumps(pilot,indent=2)+'\n')
    if schedule_path.exists(): schedule=json.loads(schedule_path.read_text())
    else: schedule_path.write_text(json.dumps(schedule,indent=2)+'\n')
    index=len(accounting)
    while complete < target:
        pending=[]; new_count=0
        # At most the number of completions still needed can be launched in this batch.
        batch_limit=min(args.episode_batch,target-complete)
        while index<len(rows) and new_count<batch_limit:
            row=rows[index]; index+=1; run_id=row['run_id']; status=models/'status'/(run_id+'.json'); intent=models/'status'/(run_id+'.intent.json')
            if status.exists():
                rec=json.loads(status.read_text()); accounting.append(rec); complete+=bool(rec.get('complete_pair')); continue
            capture=ROOT/'data/evaluator_only/analysis/handoff-fresh-candidate-collection-v1'/(run_id+'.json')
            if not capture.exists():
                index-=1; print(json.dumps(dict(waiting_for_physical_capture=run_id,complete_pairs=complete)),flush=True); break
            physical=json.loads(capture.read_text())
            if not physical.get('technical_valid',False):
                rec=dict(run_id=run_id,complete_pair=False,disposition='PHYSICAL_TECHNICAL_INVALID_NO_METHOD_CALL'); write_once(status,rec); accounting.append(rec); continue
            reference=json.loads((ROOT/f'data/evaluator_only/final/{run_id}/command-motion-independent-reference-v1.json').read_text())
            if reference['result']['disposition']!='supported':
                rec=dict(run_id=run_id,complete_pair=False,disposition='OUTSIDE_FROZEN_DISCREPANCY_POPULATION_NO_METHOD_CALL'); write_once(status,rec); accounting.append(rec); continue
            if intent.exists(): raise RuntimeError('Unresolved prior intent; refuse duplicate: '+run_id)
            write_once(intent,dict(run_id=run_id,study_id=freeze['study_id'],freeze_sha256=hashlib.sha256(args.freeze.read_bytes()).hexdigest(),semantic_attempt_started=True,continuous_queue=True))
            conditions=[run_id+f'-E{i}' for i in range(4)]; validation=dict(episodes=[dict(run_id=run_id,condition_ids=conditions,condition_packet_sha256s=[])])
            b4_fail=[]
            for condition in conditions:
                entry,_,family=_materialize(ROOT,pilot,schedule,condition)
                validation['episodes'][0]['condition_packet_sha256s'].append(entry['condition']['method_packet_sha256'])
                try:
                    ans=realize(ontology,entry,dict(question_id=family+'-question-v1-development',failure_premise=True,required_mechanism_families=['command_motion']))
                    ans.update(development_only=False,study_stage='CONFIRMATION',study_id=freeze['study_id'],family=family,freeze_sha256=hashlib.sha256(args.freeze.read_bytes()).hexdigest())
                    write_once(models/'b4'/(condition+'.json'),ans)
                except Exception as e: b4_fail.append(dict(condition_id=condition,error=type(e).__name__+': '+str(e)))
            validpath=out/(run_id+'-input-validation.json'); write_once(validpath,validation)
            pending.append((run_id,conditions,b4_fail,validpath)); new_count+=1
        if pending:
            def call(item):
                run_id,condition,validpath=item
                try:
                    run(SimpleNamespace(condition_id=condition,pilot=pilot_path,schedule=schedule_path,validation=validpath,cache=models/'cache',output_root=models/'b2',timeout_seconds=freeze['b2_timeout_seconds']))
                    return dict(condition_id=condition,status='VALID')
                except Exception as e:
                    return dict(condition_id=condition,status='TECHNICAL_FAILURE',error=type(e).__name__+': '+str(e))
            futures={}
            with ThreadPoolExecutor(max_workers=args.b2_concurrency) as ex:
                for run_id,conditions,b4_fail,validpath in pending:
                    for condition in conditions: futures[ex.submit(call,(run_id,condition,validpath))]=run_id
                grouped={run_id:[] for run_id,_,_,_ in pending}
                for fut in as_completed(futures): grouped[futures[fut]].append(fut.result())
            for run_id,conditions,b4_fail,validpath in pending:
                calls=grouped[run_id]; rec=dict(run_id=run_id,study_stage='CONFIRMATION',complete_pair=not b4_fail and len(calls)==4 and all(c['status']=='VALID' for c in calls),b2_calls=calls,b4_technical_failures=b4_fail,quality_driven_retries=0,continuous_queue=True)
                write_once(models/'status'/(run_id+'.json'),rec); accounting.append(rec); complete+=bool(rec['complete_pair'])
                print(json.dumps(dict(run_id=run_id,complete_pair=rec['complete_pair'],complete_paired_episode_n=complete,pending_batch=len(pending))),flush=True)
        if not pending and index>=len(rows): break
        if not pending and complete<target: time.sleep(args.poll_seconds)
        # Recompute from authoritative terminal statuses, preserving frozen prefix.
        complete=sum(bool(r.get('complete_pair')) for r in accounting)
    write_once(accounting_path,dict(study_id=freeze['study_id'],look='FIRST',complete_paired_episode_n=complete,planned_valid_n=target,complete=complete==target,records=accounting,dispatcher='continuous-cross-episode-v1',b2_concurrency=args.b2_concurrency,episode_batch=args.episode_batch))
    print(json.dumps(dict(complete_pairs=complete,target=target,first_look_ready=complete==target)),flush=True)

if __name__=='__main__': main()
