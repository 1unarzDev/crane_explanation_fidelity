"""Bounded exploratory comparison on an outcome-independent V16 subset."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import secrets
import shutil
import subprocess
import time
from datetime import datetime, timezone

from .inventory import inventory, ROOT, BANK, FAMILIES
from .dispatch import dispatch
from ..confirmatory_v1.journal import exclusive_json, fingerprint
from ..confirmatory_v1.registered_attempt_executor_v2 import load_artifact
from ..confirmatory_v1.development_registered_backend import DevelopmentBackend
from ..confirmatory_v1.development_unique_methods_v2 import prepare as legacy_bindings
from ..confirmatory_v1.episode_scoring_archives_v1 import episode_plan, scoring_artifacts, write_episode, read_episode, close_episode, cohort_index
from ..confirmatory_v1.blinded_scoring_workflow import select_C
from ..confirmatory_v1.rich_evaluator_v4 import PROMPT
from ..confirmatory_v1.seal_cohort import committed
from ..acquisition.raw_archive_v1 import digest
from ..acquisition.navigation_usefulness_v2 import public_packet, reference

BASE=ROOT/'manifests/hexar_external/existing_v16_exploratory_v1'
DOC=ROOT/'docs/hexar_external/existing_v16_exploratory_v1/PLAN.md'
check_raw=inventory


def prepare():
    if BASE.exists() and any(p.name!='preparation_failure_001' for p in BASE.iterdir()):
        raise ValueError('existing exploratory declaration cannot be replaced')
    inv=inventory()
    if inv['eligible']!=144:raise ValueError('answer-blind inventory requires review before subset declaration')
    selection_seed=secrets.token_hex(32);rng=random.Random(int(selection_seed,16))
    selected={}
    for family in FAMILIES:
        bank=sorted(r['episode_id'] for r in inv['episodes'] if r['family']==family and r['eligible'])
        rng.shuffle(bank);selected[family]=bank[:6]
    schedule=[selected[f][i] for i in range(6) for f in FAMILIES]
    cli=Path(shutil.which('codex')).resolve()
    cli_binding=dict(executable_sha256=digest(cli),version=subprocess.check_output([str(cli),'--version'],text=True).strip())
    _,prompt_path,_,lookup=legacy_bindings(cli_binding)
    bindings={m:copy.deepcopy(next(r['implementation_binding'] for r in lookup.values() if r['method']==m)) for m in ('HX-CONTRACT','HX-PROMPT')}
    # Pin the unchanged already operational method/instrument/transport sources;
    # avoid importing a new confirmation-admission gate into this analysis.
    old=load_artifact(ROOT/'manifests/hexar_external/confirmatory_v1/development_streaming_episode_pipeline_v2/declaration.json')
    sources={ROOT/p for p in old['source_hashes'] if p.startswith('analysis/')}
    sources.update((Path(__file__),Path(__file__).with_name('inventory.py'),Path(__file__).with_name('dispatch.py'),DOC,prompt_path))
    sources.update(ROOT/'analysis/hexar_external/confirmatory_v1'/name for name in
        ('mixture_interval_v3.py','mixture_interval_v2.py','mixture_statistics.py'))
    hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(sources)}
    for value in bindings.values():value['source_hashes']=hashes;value['registered_backend_development_only']=True
    BASE.mkdir(parents=True,exist_ok=True)
    exclusive_json(BASE/'inventory.json',inv);exclusive_json(BASE/'raw_archive_reverification.json',inv)
    # This authenticated input is an 83 MB acquisition review, not a bounded
    # provider return. Do not apply the provider-response size limit to it.
    packet_rows=json.loads((BANK/'interface_review.json').read_text())['packets']
    by_episode={uid:[] for uid in schedule}
    for r in packet_rows:
        if r['development_id'] in by_episode:by_episode[r['development_id']].append(r)
    inventory_rows={r['episode_id']:r for r in inv['episodes']};rows=[]
    for uid in schedule:
        folder=BASE/fingerprint(['exploratory-v16-episode',uid]);folder.mkdir()
        entries=[]
        for row in by_episode[uid]:
            packet=public_packet(row['method_packet'])
            entries.append(dict(episode_id=uid,job_id=row['question_id']+'-'+row['condition'],packet=packet,reference=reference(packet)))
        neutral,plan=episode_plan(entries,bindings)
        exclusive_json(folder/'neutral_reference_registry.json',neutral);exclusive_json(folder/'unique_method_plan.json',plan)
        rows.append(dict(episode_id=uid,family=inventory_rows[uid]['family'],relative_path=folder.name,
            neutral_sha256=digest(folder/'neutral_reference_registry.json'),plan_sha256=digest(folder/'unique_method_plan.json')))
    declaration=dict(schema='hexar-existing-v16-exploratory-plan/v1',phase='development_only',analysis_status='EXPLORATORY_NOT_CONFIRMATORY',
        source_hashes=hashes,cli_path=str(cli),cli_binding=cli_binding,records=rows,selection_seed_hex=selection_seed,
        selection='Uniform pseudorandom shuffle within each eligible family; first six; rank-interleaved family order fixed before outputs.',
        acquired_episodes=144,eligible_episodes=144,scheduled_episodes=36,valid_target_per_family=6,
        prompt_path=str(prompt_path.relative_to(ROOT)),prompt_sha256=digest(prompt_path),baseline_model='gpt-6-sol',judge_model='gpt-6-astra',
        reasoning_effort='high',workers=8,timeout_seconds=360,quality_retries=0,technical_retries=0,
        maximum_baseline_calls=216,maximum_initial_judge_calls=864,maximum_C_calls=432,maximum_provider_calls=1512,
        elapsed_dispatch_deadline_seconds=10800,deadline_policy='Start no new episode after 3 elapsed hours; finish an already started episode. Preserve unscheduled/unresolved attempts as missing, no replacement.',
        development_blinding_key_hex=secrets.token_hex(32),shuffle_seed=2026100201,
        raw_reverification_sha256=digest(BASE/'raw_archive_reverification.json'),
        criterion='Measured existing cohort, all favorable/null/adverse outcomes and missingness retained; no significance requirement.',
        endpoint='EXPLORATORY_V16_EPISODE_BATTERY_FAILURE: any of nine fixed cells unsupported, overlicensed or missing mandatory useful unit; unresolved remains unknown.',
        reporting='Equal episode weights with six scheduled per family; all four cells; complete-case and all-scheduled bounds; only primary exploratory mixture inference, secondary/family descriptive.',
        confirmatory_N=0,alpha_consumed=0,scientific_freeze=False,provider_qualified=False,confirmation_authorized=False,
        agent_assessed=True,human_validated=False,original_raw_mutated=False,prepared_at=datetime.now(timezone.utc).isoformat())
    exclusive_json(BASE/'declaration.json',declaration)
    for path in sources:
        dest=BASE/'source_archive'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream:stream.write(path.read_bytes())
    print('Prepared 36 V16 episodes, six per family; no semantic calls yet.',flush=True)

def execute():
    declaration=load_artifact(BASE/'declaration.json');binding=fingerprint(declaration)
    if declaration['phase']!='development_only' or declaration['confirmation_authorized'] is not False or declaration['confirmatory_N']!=0:
        raise ValueError('explicit permanently development-only cohort required')
    pins=declaration['source_hashes'];cli=Path(declaration['cli_path'])
    def guard():
        if digest(cli)!=declaration['cli_binding']['executable_sha256'] or any(digest(ROOT/p)!=sha for p,sha in pins.items()):
            raise ValueError('development CLI/source binding changed')
        if digest(BASE/'declaration.json')!=declaration_hash:raise ValueError('development declaration changed')
    declaration_hash=digest(BASE/'declaration.json')
    required=[BASE/'declaration.json',BASE/'raw_archive_reverification.json']
    required.extend(BASE/r['relative_path']/name for r in declaration['records'] for name in
                    ('neutral_reference_registry.json','unique_method_plan.json'))
    if any(not committed(ROOT,p) for p in required) or any(not committed(ROOT,ROOT/p) for p in pins):
        raise ValueError('commit all declared sources and pre-generation plans before development calls')
    guard();exclusive_json(BASE/'execution_claim.json',dict(binding_sha256=binding,phase='development_only',attempt_limit=1,confirmation_authorized=False))
    # Raw proof is rechecked before semantic dispatch and at terminal closure.
    if check_raw()!=load_artifact(BASE/'raw_archive_reverification.json'):
        raise ValueError('raw technical provenance changed before semantic execution')
    paired=[0,0,0,0];rows=[];pointers=[];calls=0;valid_methods=0;valid_judges=0;judge_attempts=0;unresolved=0
    stage_completions=[]
    backend_factory=lambda reg:DevelopmentBackend(reg,cli,declaration['cli_binding']['executable_sha256'])
    started=time.monotonic()
    for r in declaration['records']:
        if time.monotonic()-started>=declaration['elapsed_dispatch_deadline_seconds']:break
        folder=BASE/r['relative_path']
        neutral_path=folder/'neutral_reference_registry.json';plan_path=folder/'unique_method_plan.json'
        if digest(neutral_path)!=r['neutral_sha256'] or digest(plan_path)!=r['plan_sha256']:
            raise ValueError('pre-generation paired episode plan changed')
        neutral=load_artifact(neutral_path);plan=load_artifact(plan_path)
        packet_lookup={entry['packet_sha256']:entry['packet'] for entry in neutral['entries']}
        jobs=[]
        for request in plan['requests']:
            payload=packet_lookup[request['packet_sha256']];method=request['method']
            value=dict(role='contract' if method=='HX-CONTRACT' else 'method',maximum_response_bytes=1048576,
                development_only=True,payload=payload)
            if method=='HX-CONTRACT':value.update(generation_id=request['unique_request_id'],recording_id=r['episode_id'])
            else:value.update(prompt=(ROOT/declaration['prompt_path']).read_text(),model='gpt-6-sol',reasoning_effort='high',timeout_seconds=360)
            jobs.append(dict(job_id=request['unique_request_id'],request=value))
        attempts,completion=dispatch(folder/'methods',binding,'methods',jobs,
            {BASE/'declaration.json':declaration_hash,neutral_path:r['neutral_sha256'],plan_path:r['plan_sha256']},guard,backend_factory)
        stage_completions.append(completion);outputs=[];valid_methods+=completion['valid'];calls+=6
        for request in plan['requests']:
            outcome=attempts[request['unique_request_id']];answer=outcome['parsed']['answer'] if outcome['status']=='VALID' else None
            outputs.append(dict(unique_request_id=request['unique_request_id'],episode_id=r['episode_id'],method=request['method'],
                request_sha256=request['request_sha256'],packet_sha256=request['packet_sha256'],status=outcome['status'],
                answer=answer,answer_sha256=hashlib.sha256(answer.encode()).hexdigest() if answer is not None else None,
                error=outcome['error'],model_calls=int(request['method']=='HX-PROMPT'),raw_sha256=outcome['raw_sha256']))
        artifacts=scoring_artifacts(neutral,plan,outputs,bytes.fromhex(declaration['development_blinding_key_hex']),declaration['shuffle_seed'])
        index=write_episode(folder/'scoring',artifacts,binding,'development_qualification')
        _,retained=read_episode(folder/'scoring',fingerprint(index),binding,'development_qualification')
        public=retained['public_scoring_plan.json']
        def judge_job(job):
            return dict(job_id=job['opaque_job'],request=dict(role='judge',maximum_response_bytes=1048576,
                development_only=True,payload=job['payload'],prompt=PROMPT,model='gpt-6-astra',reasoning_effort='high',timeout_seconds=360))
        prereq={folder/'methods/completion_receipt.json':digest(folder/'methods/completion_receipt.json')}
        prereq.update({folder/'scoring'/name:pin['sha256'] for name,pin in index['files'].items()})
        prereq[folder/'scoring/episode_index.json']=digest(folder/'scoring/episode_index.json')
        initial,completion=dispatch(folder/'initial_judges',binding,'initial_judges',[judge_job(j) for j in public['initial_jobs']],prereq,guard,backend_factory,workers=8)
        stage_completions.append(completion);calls+=completion['attempts'];judge_attempts+=completion['attempts'];valid_judges+=completion['valid']
        selected=select_C(public,initial);exclusive_json(folder/'selected_C_jobs.json',selected)
        prereq.update({folder/'selected_C_jobs.json':digest(folder/'selected_C_jobs.json'),
            folder/'initial_judges/closed_outcomes.json':digest(folder/'initial_judges/closed_outcomes.json'),
            folder/'initial_judges/completion_receipt.json':digest(folder/'initial_judges/completion_receipt.json')})
        C,completion=dispatch(folder/'adjudication_judges',binding,'adjudication_judges',[judge_job(j) for j in selected],prereq,guard,backend_factory,workers=8)
        stage_completions.append(completion);calls+=completion['attempts'];judge_attempts+=completion['attempts'];valid_judges+=completion['valid']
        _,retained=read_episode(folder/'scoring',fingerprint(index),binding,'development_qualification')
        closed=close_episode(retained,initial,C);exclusive_json(folder/'closed_dispositions.json',closed)
        unresolved+=sum(v['status']=='UNRESOLVED' for v in closed['labels'].values())
        paired=[a+b for a,b in zip(paired,closed['paired_counts'])]
        pointers.append(dict(episode_id=r['episode_id'],relative_path=r['relative_path']+'/scoring',episode_index_sha256=fingerprint(index)))
        rows.append(dict(episode_id=r['episode_id'],family=r['family'],initial_judge_calls=len(initial),C_calls=len(C),paired_counts=closed['paired_counts']))
        print('Closed exploratory episode',len(rows),'of 36',r['episode_id'],flush=True)
    if check_raw()!=load_artifact(BASE/'raw_archive_reverification.json'):
        raise ValueError('original raw technical provenance changed during semantic execution')
    guard();exclusive_json(BASE/'cohort_index.json',cohort_index(pointers,binding,'development_qualification'))
    criterion=valid_methods==432 and valid_judges==judge_attempts and unresolved==0
    exclusive_json(BASE/'report.json',dict(schema='hexar-development-streaming-episode-report/v1',phase='development_only',
        status='EXPLORATORY_MEASUREMENT_COMPLETED' if criterion else 'EXPLORATORY_MEASUREMENT_INCOMPLETE_RETAINED',
        rows=rows,stage_completions=stage_completions,paired_counts=paired,method_attempts=sum(c["attempts"] for c in stage_completions if c["stage"]=="methods"),valid_method_attempts=valid_methods,
        judge_attempts=judge_attempts,valid_judge_attempts=valid_judges,unresolved_unique_labels=unresolved,model_calls=calls,
        episodes=36,completed_episodes=len(rows),confirmatory_N=0,alpha_consumed=0,significance_test_performed=False,confirmation_authorized=False,
        agent_assessed=True,human_validated=False,provider_qualified=False,raw_episodes_replayed=0,
        declaration_sha256=declaration_hash))
    print('Exploratory measurement terminal; retain all outcomes for frozen exploratory analysis.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    prepare() if args.prepare else execute()
