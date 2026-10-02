"""Actual full-battery DEVELOPMENT workflow on one exposed episode; no inference."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import time

from .journal import exclusive_json, fingerprint
from .unique_request_plan import build
from .unique_result_expansion import expand_outputs
from .registered_attempt_executor import registry, RegisteredExecutor
from .development_registered_backend import DevelopmentBackend
from .development_unique_methods_v2 import prepare as prior_prepare
from .blinded_scoring_workflow import reference_registry, prepare, select_C, finalize
from .rich_evaluator_v4 import PROMPT
from ..acquisition.navigation_usefulness_v2 import public_packet, reference

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'manifests/hexar_external/confirmatory_v1'
DEST = BASE/'development_registered_pipeline_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def execute():
    DEST.mkdir(exist_ok=False)
    cli = Path(shutil.which('codex')).resolve()
    cli_binding = dict(executable_sha256=sha(cli), version=subprocess.check_output([str(cli), '--version'], text=True).strip())
    source, prompt_path, old_plan, lookup = prior_prepare(cli_binding)
    episode = min({r['episode_id'] for r in old_plan['requests']})
    exposed = json.loads(source.read_text())
    packets = [row for row in exposed['packets'] if row['development_id'] == episode]
    if len(packets) != 9 or exposed['phase'] != 'development_only' or exposed['confirmatory_N'] != 0:
        raise ValueError('complete already exposed development battery required')
    sources = {source, prompt_path, Path(__file__), ROOT/'docs/hexar_external/confirmatory_v1/DEVELOPMENT_REGISTERED_PIPELINE.md'}
    sources.update(ROOT/name for entry in lookup.values() for name in entry['implementation_binding']['source_hashes'])
    sources.update(Path(__file__).with_name(name) for name in
        ('development_registered_backend.py', 'registered_attempt_executor.py', 'blinded_scoring_workflow.py',
         'development_unique_methods_v2.py', 'unique_result_expansion.py', 'rich_evaluator_v4.py',
         'rich_evaluator_v3.py', 'rich_evaluator_v2.py', 'rich_evaluator_candidate.py', 'rich_blind_projection.py',
         'rich_adjudication.py', 'journal.py'))
    source_hashes = {str(p.relative_to(ROOT)):sha(p) for p in sorted(sources)}
    binding = {method:copy.deepcopy(next(e['implementation_binding'] for e in lookup.values() if e['method'] == method))
               for method in ('HX-CONTRACT', 'HX-PROMPT')}
    for value in binding.values():
        value['source_hashes'] = source_hashes
        value['registered_backend_development_only'] = True
    neutral = reference_registry([dict(episode_id=episode, job_id=r['question_id']+'-'+r['condition'],
        packet=public_packet(r['method_packet']), reference=reference(public_packet(r['method_packet']))) for r in packets])
    entries = [dict(episode_id=episode, method=method, job_id=r['question_id']+'-'+r['condition'],
                    packet=public_packet(r['method_packet']), implementation_binding=binding[method])
               for r in packets for method in ('HX-CONTRACT', 'HX-PROMPT')]
    plan = build(entries)
    if plan['unique_requests'] != 12 or plan['battery_cells'] != 18:
        raise ValueError('six unique requests per method and nine battery cells required')
    packet_by_hash = {fingerprint(e['packet']):e['packet'] for e in entries}
    method_jobs = []
    for row in plan['requests']:
        request = dict(role='contract' if row['method']=='HX-CONTRACT' else 'method',
                       maximum_response_bytes=1048576, development_only=True,
                       payload=packet_by_hash[row['packet_sha256']])
        if request['role']=='contract':
            request.update(generation_id=row['unique_request_id'], recording_id=episode)
        else:
            request.update(prompt=prompt_path.read_text(), model='gpt-6-sol', reasoning_effort='high', timeout_seconds=360)
        method_jobs.append(dict(job_id=row['unique_request_id'], request=request))
    declaration = dict(schema='hexar-development-registered-pipeline/v1', phase='development_only',
        exposed_episode=episode, confirmatory_N=0, alpha_consumed=0,
        method_jobs_sha256=fingerprint(method_jobs), unique_plan_sha256=fingerprint(plan),
        neutral_reference_registry_sha256=fingerprint(neutral), source_hashes=source_hashes,
        cli_path=str(cli), cli_binding=cli_binding, maximum_initial_model_calls=30,
        maximum_C_calls=12, workers=2, provider_qualified=False,
        scientific_freeze=False, confirmation_authorized=False, agent_assessed=True, human_validated=False)
    archive = DEST/'source_archive'
    for p in sources:
        target = archive/p.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    for name, value in (('declaration.json', declaration), ('neutral_reference_registry.json', neutral),
                        ('unique_method_plan.json', plan)):
        exclusive_json(DEST/name, value)
    approved = set()
    def admit(value):
        if (value['phase'] != 'development_qualification' or value['binding_sha256'] != fingerprint(declaration)
                or fingerprint(value) not in approved or sha(cli) != cli_binding['executable_sha256']
                or any(sha(ROOT/name) != digest for name,digest in source_hashes.items())):
            raise ValueError('registered development source/request binding changed')
        return dict(authorized=True, phase=value['phase'], binding_sha256=value['binding_sha256'],
                    registry_sha256=fingerprint(value))
    def dispatch(phase, jobs):
        if not jobs:
            return {}, 0.
        registered = registry(fingerprint(declaration), 'development_qualification', jobs)
        exclusive_json(DEST/(phase+'_registry.json'), registered)
        approved.add(fingerprint(registered))
        backend = DevelopmentBackend(registered, cli, cli_binding['executable_sha256'])
        engine = RegisteredExecutor(DEST/phase, registered, admit)
        started = time.monotonic()
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda j:engine.execute(j['job_id'], backend), registered['jobs']))
        if any(r['dispatch_performed'] is not True for r in results):
            raise ValueError('new run unexpectedly reused a dispatch')
        return {j['job_id']:r['outcome'] for j,r in zip(registered['jobs'],results)}, time.monotonic()-started
    method_attempts, method_seconds = dispatch('methods', method_jobs)
    outputs = []
    for row in plan['requests']:
        outcome = method_attempts[row['unique_request_id']]
        answer = outcome['parsed']['answer'] if outcome['status']=='VALID' else None
        outputs.append(dict(unique_request_id=row['unique_request_id'], episode_id=episode, method=row['method'],
            request_sha256=row['request_sha256'], packet_sha256=row['packet_sha256'], status=outcome['status'],
            answer=answer, answer_sha256=hashlib.sha256(answer.encode()).hexdigest() if answer is not None else None,
            error=outcome['error'], model_calls=int(row['method']=='HX-PROMPT'), raw_sha256=outcome['raw_sha256']))
    exclusive_json(DEST/'method_outputs.json', outputs)
    public, private = prepare(plan, outputs, neutral, secrets.token_bytes(32), 2026100109)
    exclusive_json(DEST/'public_scoring_plan.json', public)
    exclusive_json(DEST/'sealed_method_linkage.json', private)
    def judge_job(job):
        return dict(job_id=job['opaque_job'], request=dict(role='judge', maximum_response_bytes=1048576,
            development_only=True, payload=job['payload'], prompt=PROMPT, model='gpt-6-astra',
            reasoning_effort='high', timeout_seconds=360))
    initial, initial_seconds = dispatch('initial_judges', [judge_job(j) for j in public['initial_jobs']])
    selected = select_C(public, initial)
    exclusive_json(DEST/'selected_C_jobs.json', selected)
    C, C_seconds = dispatch('adjudication_judges', [judge_job(j) for j in selected])
    result = finalize(plan, outputs, neutral, public, private, initial, C)
    exclusive_json(DEST/'closed_dispositions.json', result)
    expanded = expand_outputs(plan, outputs)
    semantic_unresolved = sum(v['status']=='UNRESOLVED' for v in result['labels'].values())
    valid = sum(v['status']=='VALID' for v in method_attempts.values())
    transports_valid = all(v['status']=='VALID' for v in list(initial.values())+list(C.values()))
    criterion = valid==12 and transports_valid and semantic_unresolved==0
    # Verify closed raw archives again without a second dispatch or backend call.
    for phase in ('methods', 'initial_judges', 'adjudication_judges'):
        path = DEST/(phase+'_registry.json')
        if path.exists():
            registered = json.loads(path.read_text())
            engine = RegisteredExecutor(DEST/phase, registered, admit)
            for j in registered['jobs']:
                result_reuse = engine.execute(j['job_id'], lambda request: (_ for _ in ()).throw(ValueError('verification cannot dispatch')))
                if result_reuse['dispatch_performed']:
                    raise ValueError('raw archive verification performed new dispatch')
    report = dict(schema='hexar-development-registered-pipeline-report/v1', phase='development_only',
        status='DEVELOPMENT_OPERATIONAL_PIPELINE_PASSED_NOT_FINAL_ADAPTER_QUALIFICATION'
            if criterion else 'FAILED_DEVELOPMENT_QUALIFICATION_RETAINED',
        valid_method_attempts=valid, unique_method_attempts=12, initial_judge_attempts=len(initial),
        C_attempts=len(C), judge_transports_all_valid=transports_valid, unresolved_unique_labels=semantic_unresolved,
        actual_model_attempts=6+len(initial)+len(C), contract_model_calls=0,
        method_elapsed_seconds=method_seconds, initial_judge_elapsed_seconds=initial_seconds,
        C_elapsed_seconds=C_seconds, paired_counts=result['paired_counts'], battery_cells=len(expanded),
        mean_words_by_method={m:sum(len(r['answer'].split()) for r in outputs if r['method']==m and r['answer'] is not None)
            /max(1,sum(r['method']==m and r['answer'] is not None for r in outputs)) for m in ('HX-CONTRACT','HX-PROMPT')},
        declaration_sha256=fingerprint(declaration), raw_and_journal_verification_passed=True,
        method_neutral_registry_written_before_generation=True, judge_registry_written_before_calls=True,
        same_legitimate_evidence=True, agent_assessed=True, human_validated=False,
        confirmatory_N=0, alpha_consumed=0, significance_test_performed=False,
        provider_qualified=False, full_transitive_runtime_qualified=False, confirmation_authorized=False)
    exclusive_json(DEST/'report.json', report)
    print(report['status'], report['paired_counts'], flush=True)


if __name__=='__main__':
    execute()
