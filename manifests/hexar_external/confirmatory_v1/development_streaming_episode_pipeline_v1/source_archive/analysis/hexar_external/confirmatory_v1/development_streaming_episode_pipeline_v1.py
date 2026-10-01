"""Declared V20 DEVELOPMENT integration; never admits confirmation or inference."""
import argparse
import copy
import hashlib
from pathlib import Path
import secrets
import shutil
import subprocess

from .journal import exclusive_json, fingerprint
from .registered_attempt_executor_v2 import load_artifact
from .development_registered_backend import DevelopmentBackend
from .development_unique_methods_v2 import prepare as legacy_bindings
from .episode_scoring_archives_v1 import episode_plan, scoring_artifacts, write_episode, read_episode, close_episode, cohort_index
from .blinded_scoring_workflow import select_C
from .staged_episode_dispatch_v1 import dispatch
from .rich_evaluator_v4 import PROMPT
from .seal_cohort import committed
from ..acquisition.raw_archive_v1 import digest
from ..acquisition.verify_integrated_raw_v2 import check as check_raw
from ..acquisition.navigation_usefulness_v2 import public_packet, reference

ROOT=Path(__file__).resolve().parents[3]
RAW=ROOT/'manifests/hexar_external/acquisition/development_integrated_raw_v20'
BASE=ROOT/'manifests/hexar_external/confirmatory_v1/development_streaming_episode_pipeline_v1'
DOC=ROOT/'docs/hexar_external/confirmatory_v1/DEVELOPMENT_STREAMING_EPISODE_PIPELINE_V1.md'


def prepare():
    if BASE.exists():raise ValueError('existing declaration/run cannot be replaced or reissued')
    raw_check=check_raw()
    cli=Path(shutil.which('codex')).resolve()
    cli_binding=dict(executable_sha256=digest(cli),version=subprocess.check_output([str(cli),'--version'],text=True).strip())
    _,prompt_path,_,lookup=legacy_bindings(cli_binding)
    bindings={m:copy.deepcopy(next(r['implementation_binding'] for r in lookup.values() if r['method']==m))
              for m in ('HX-CONTRACT','HX-PROMPT')}
    sources={Path(__file__),DOC,prompt_path,RAW/'report.json',RAW/'development_archive_seal.json',RAW/'archive_verification.json'}
    sources.update(ROOT/p for value in bindings.values() for p in value['source_hashes'])
    sources.update(Path(__file__).with_name(n) for n in (
        'staged_episode_dispatch_v1.py','streaming_registry_shards_v1.py','registry_shards_v1.py',
        'episode_scoring_archives_v1.py','blinded_scoring_workflow.py','registered_attempt_executor_v2.py',
        'development_registered_backend.py','development_unique_methods_v2.py','rich_evaluator_v4.py',
        'rich_evaluator_v3.py','rich_evaluator_v2.py','rich_evaluator_candidate.py','rich_blind_projection.py',
        'rich_adjudication.py','unique_result_expansion.py','journal.py','seal_cohort.py'))
    sources.add(ROOT/'analysis/hexar_external/acquisition/verify_integrated_raw_v2.py')
    records=load_artifact(RAW/'development_archive_seal.json')['records']
    if len(records)!=6 or len({r['family'] for r in records})!=6:
        raise ValueError('all six development families required; no semantic selection')
    for r in records:sources.add(RAW/'execution/attempts'/r['episode_id']/'derived_interface_review.json')
    hashes={str(p.relative_to(ROOT)):digest(p) for p in sorted(sources)}
    for value in bindings.values():value['source_hashes']=hashes;value['registered_backend_development_only']=True
    BASE.mkdir()
    exclusive_json(BASE/'raw_archive_reverification.json',raw_check)
    rows=[]
    for r in records:
        uid=r['episode_id'];folder=BASE/fingerprint(['development-episode',uid]);folder.mkdir()
        packets=load_artifact(RAW/'execution/attempts'/uid/'derived_interface_review.json')['packets']
        entries=[]
        for row in packets:
            if row['development_id']!=uid:raise ValueError('raw episode identity differs')
            packet=public_packet(row['method_packet'])
            entries.append(dict(episode_id=uid,job_id=row['question_id']+'-'+row['condition'],packet=packet,reference=reference(packet)))
        neutral,plan=episode_plan(entries,bindings)
        exclusive_json(folder/'neutral_reference_registry.json',neutral)
        exclusive_json(folder/'unique_method_plan.json',plan)
        rows.append(dict(episode_id=uid,family=r['family'],relative_path=folder.name,
            neutral_sha256=digest(folder/'neutral_reference_registry.json'),plan_sha256=digest(folder/'unique_method_plan.json')))
    declaration=dict(schema='hexar-development-streaming-episode-pipeline/v1',phase='development_only',
        source_hashes=hashes,cli_path=str(cli),cli_binding=cli_binding,records=rows,
        prompt_path=str(prompt_path.relative_to(ROOT)),prompt_sha256=digest(prompt_path),
        baseline_model='gpt-6-sol',judge_model='gpt-6-astra',reasoning_effort='high',workers=2,
        timeout_seconds=360,quality_retries=0,technical_retries=0,unique_method_attempts=72,
        maximum_baseline_calls=36,maximum_initial_judge_calls=144,maximum_C_calls=72,
        development_blinding_key_hex=secrets.token_bytes(32).hex(),shuffle_seed=2026100111,
        raw_reverification_sha256=digest(BASE/'raw_archive_reverification.json'),
        criterion='All 72 method transports and every scheduled judge transport valid, six whole-episode dispositions closed, no unresolved unique labels, retained byte/chronology reproduction; no expected winner.',
        confirmatory_N=0,alpha_consumed=0,scientific_freeze=False,provider_qualified=False,
        confirmation_authorized=False,agent_assessed=True,human_validated=False,
        development_episode_count=6,raw_episode_replays=0,original_raw_mutated=False)
    exclusive_json(BASE/'declaration.json',declaration)
    for path in sources:
        dest=BASE/'source_archive'/path.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as stream:stream.write(path.read_bytes())
    print('Prepared development declaration; commit declaration, pre-generation plans and exact sources before execution.',flush=True)


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
    for r in declaration['records']:
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
        initial,completion=dispatch(folder/'initial_judges',binding,'initial_judges',[judge_job(j) for j in public['initial_jobs']],prereq,guard,backend_factory)
        stage_completions.append(completion);calls+=completion['attempts'];judge_attempts+=completion['attempts'];valid_judges+=completion['valid']
        selected=select_C(public,initial);exclusive_json(folder/'selected_C_jobs.json',selected)
        prereq.update({folder/'selected_C_jobs.json':digest(folder/'selected_C_jobs.json'),
            folder/'initial_judges/closed_outcomes.json':digest(folder/'initial_judges/closed_outcomes.json'),
            folder/'initial_judges/completion_receipt.json':digest(folder/'initial_judges/completion_receipt.json')})
        C,completion=dispatch(folder/'adjudication_judges',binding,'adjudication_judges',[judge_job(j) for j in selected],prereq,guard,backend_factory)
        stage_completions.append(completion);calls+=completion['attempts'];judge_attempts+=completion['attempts'];valid_judges+=completion['valid']
        _,retained=read_episode(folder/'scoring',fingerprint(index),binding,'development_qualification')
        closed=close_episode(retained,initial,C);exclusive_json(folder/'closed_dispositions.json',closed)
        unresolved+=sum(v['status']=='UNRESOLVED' for v in closed['labels'].values())
        paired=[a+b for a,b in zip(paired,closed['paired_counts'])]
        pointers.append(dict(episode_id=r['episode_id'],relative_path=r['relative_path']+'/scoring',episode_index_sha256=fingerprint(index)))
        rows.append(dict(episode_id=r['episode_id'],family=r['family'],initial_judge_calls=len(initial),C_calls=len(C),paired_counts=closed['paired_counts']))
        print('Closed development episode',r['episode_id'],flush=True)
    if check_raw()!=load_artifact(BASE/'raw_archive_reverification.json'):
        raise ValueError('original raw technical provenance changed during semantic execution')
    guard();exclusive_json(BASE/'cohort_index.json',cohort_index(pointers,binding,'development_qualification'))
    criterion=valid_methods==72 and valid_judges==judge_attempts and unresolved==0
    exclusive_json(BASE/'report.json',dict(schema='hexar-development-streaming-episode-report/v1',phase='development_only',
        status='DEVELOPMENT_STAGE_INTEGRATION_PASSED_NOT_PRODUCTION_ADMISSION' if criterion else 'FAILED_DEVELOPMENT_SCREEN_RETAINED',
        rows=rows,stage_completions=stage_completions,paired_counts=paired,method_attempts=72,valid_method_attempts=valid_methods,
        judge_attempts=judge_attempts,valid_judge_attempts=valid_judges,unresolved_unique_labels=unresolved,model_calls=calls,
        episodes=6,confirmatory_N=0,alpha_consumed=0,significance_test_performed=False,confirmation_authorized=False,
        agent_assessed=True,human_validated=False,provider_qualified=False,raw_episodes_replayed=0,
        declaration_sha256=declaration_hash))
    print('Development stages terminal; all results retained; no confirmation or inference.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    prepare() if args.prepare else execute()
