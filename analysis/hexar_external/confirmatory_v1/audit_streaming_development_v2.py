"""Terminal, read-only V2 development reproduction. Never dispatches or infers."""
import hashlib
from pathlib import Path

from .audit_development_episode_stage_v1 import audit_stage
from .blinded_scoring_workflow import select_C
from .episode_scoring_archives_v1 import read_episode, close_episode, cohort_index
from .journal import fingerprint
from .registered_attempt_executor_v2 import load_artifact
from .rich_evaluator_v4 import PROMPT
from ..acquisition.raw_archive_v1 import digest
from ..acquisition.verify_integrated_raw_v3 import check as check_raw

BASE = 'manifests/hexar_external/confirmatory_v1/development_streaming_episode_pipeline_v2'


def check(root, base=BASE):
    root = Path(root).resolve()
    folder = root / base
    # No recovery/redispatch, or qualification of a partially observed run.
    if not (folder / 'report.json').is_file():
        raise ValueError('terminal development report required; live run untouched')
    report = load_artifact(folder / 'report.json')
    declaration = load_artifact(folder / 'declaration.json')
    if (declaration.get('phase') != 'development_only'
            or declaration.get('confirmatory_N') != 0
            or declaration.get('confirmation_authorized') is not False
            or report.get('phase') != 'development_only'
            or report.get('confirmatory_N') != 0
            or report.get('alpha_consumed') != 0
            or report.get('confirmation_authorized') is not False
            or report.get('significance_test_performed') is not False
            or report.get('declaration_sha256') != digest(folder / 'declaration.json')):
        raise ValueError('explicit hash-bound development-only terminal run required')
    for path, sha in declaration['source_hashes'].items():
        if digest(root / path) != sha or digest(folder / 'source_archive' / path) != sha:
            raise ValueError('declared current or retained source changed: ' + path)
    records = declaration['records']
    if (len(records) != 6 or len({r['episode_id'] for r in records}) != 6
            or {r['family'] for r in records} != {
                'charging', 'dynamic_env', 'localization', 'manual_joystick', 'obstacle', 'success'}):
        raise ValueError('exact six-family development membership required')
    binding = fingerprint(declaration)
    if digest(folder / 'raw_archive_reverification.json') != declaration['raw_reverification_sha256']:
        raise ValueError('original raw archive pre-generation proof changed')
    if check_raw() != load_artifact(folder / 'raw_archive_reverification.json'):
        raise ValueError('original raw acquisition proof no longer reproduces')
    claim = load_artifact(folder / 'execution_claim.json')
    if claim != dict(binding_sha256=binding, phase='development_only', attempt_limit=1,
                     confirmation_authorized=False):
        raise ValueError('original single-execution declaration changed')
    rows, stages, pointers, completions = [], [], [], []
    paired, methods, judges, valid_methods, valid_judges, unresolved = [0]*4, 0, 0, 0, 0, 0
    for r in records:
        episode = folder / r['relative_path']
        for name, sha_key in (('neutral_reference_registry.json', 'neutral_sha256'),
                              ('unique_method_plan.json', 'plan_sha256')):
            if digest(episode / name) != r[sha_key]:
                raise ValueError('pre-generation episode plan changed')
        checked = {stage: audit_stage(episode / stage, binding, stage)
                   for stage in ('methods', 'initial_judges', 'adjudication_judges')}
        stages.extend(dict(episode_id=r['episode_id'], **value) for value in checked.values())
        completions.extend(load_artifact(episode / stage / 'completion_receipt.json')
                           for stage in ('methods', 'initial_judges', 'adjudication_judges'))
        index = load_artifact(episode / 'scoring/episode_index.json')
        _, artifacts = read_episode(episode / 'scoring', fingerprint(index), binding, 'development_qualification')
        for name in ('neutral_reference_registry.json', 'unique_method_plan.json'):
            if artifacts[name] != load_artifact(episode / name):
                raise ValueError('scoring archive changed a pre-generation input')
        method_outcomes = load_artifact(episode / 'methods/closed_outcomes.json')
        expected_outputs = []
        for request in artifacts['unique_method_plan.json']['requests']:
            outcome = method_outcomes[request['unique_request_id']]
            answer = outcome['parsed']['answer'] if outcome['status'] == 'VALID' else None
            expected_outputs.append(dict(unique_request_id=request['unique_request_id'],
                episode_id=r['episode_id'], method=request['method'], request_sha256=request['request_sha256'],
                packet_sha256=request['packet_sha256'], status=outcome['status'], answer=answer,
                answer_sha256=hashlib.sha256(answer.encode()).hexdigest() if answer is not None else None,
                error=outcome['error'], model_calls=int(request['method'] == 'HX-PROMPT'),
                raw_sha256=outcome['raw_sha256']))
        if artifacts['method_outputs.json'] != expected_outputs:
            raise ValueError('scored answers do not equal original single-attempt method outputs')
        initial = load_artifact(episode / 'initial_judges/closed_outcomes.json')
        selected = select_C(artifacts['public_scoring_plan.json'], initial)
        if selected != load_artifact(episode / 'selected_C_jobs.json'):
            raise ValueError('disagreement-only C selection changed')
        public = artifacts['public_scoring_plan.json']
        for stage, jobs in (('initial_judges', public['initial_jobs']), ('adjudication_judges', selected)):
            scheduled = [dict(job_id=j['opaque_job'], request=dict(role='judge', maximum_response_bytes=1048576,
                development_only=True, payload=j['payload'], prompt=PROMPT, model='gpt-6-astra',
                reasoning_effort='high', timeout_seconds=360)) for j in jobs]
            stage_declaration = load_artifact(episode / stage / 'stage_declaration.json')
            if stage_declaration['exact_jobs_sha256'] != fingerprint(sorted(scheduled, key=lambda j: j['job_id'])):
                raise ValueError('judge requests differ from blinded evidence and declared scoring policy')
        C = load_artifact(episode / 'adjudication_judges/closed_outcomes.json')
        closed = close_episode(artifacts, initial, C)
        if closed != load_artifact(episode / 'closed_dispositions.json'):
            raise ValueError('whole-episode labels, aliases or missingness mapping changed')
        paired = [a+b for a, b in zip(paired, closed['paired_counts'])]
        methods += checked['methods']['attempts']
        valid_methods += checked['methods']['valid']
        judges += checked['initial_judges']['attempts'] + checked['adjudication_judges']['attempts']
        valid_judges += checked['initial_judges']['valid'] + checked['adjudication_judges']['valid']
        unresolved += sum(v['status'] == 'UNRESOLVED' for v in closed['labels'].values())
        rows.append(dict(episode_id=r['episode_id'], family=r['family'],
                         initial_judge_calls=len(initial), C_calls=len(C), paired_counts=closed['paired_counts']))
        pointers.append(dict(episode_id=r['episode_id'], relative_path=r['relative_path']+'/scoring',
                             episode_index_sha256=fingerprint(index)))
    if cohort_index(pointers, binding, 'development_qualification') != load_artifact(folder / 'cohort_index.json'):
        raise ValueError('terminal cohort membership changed')
    expected = dict(rows=rows, paired_counts=paired, method_attempts=methods,
                    valid_method_attempts=valid_methods, judge_attempts=judges,
                    valid_judge_attempts=valid_judges, unresolved_unique_labels=unresolved,
                    model_calls=36+judges, episodes=6)
    if (any(report.get(k) != v for k, v in expected.items()) or methods != 72 or sum(paired) != 6
            or report['stage_completions'] != completions):
        raise ValueError('terminal report does not reproduce complete retained episodes')
    passed = valid_methods == 72 and valid_judges == judges and unresolved == 0
    status = 'DEVELOPMENT_STAGE_INTEGRATION_PASSED_NOT_PRODUCTION_ADMISSION' if passed else 'FAILED_DEVELOPMENT_SCREEN_RETAINED'
    if report['status'] != status:
        raise ValueError('terminal qualification criterion or disposition changed')
    return dict(schema='hexar-development-streaming-v2-read-only-audit/v1',
                retained_report_reproduced=True, development_screen_passed=passed,
                source_report_sha256=digest(folder / 'report.json'),
                source_declaration_sha256=digest(folder / 'declaration.json'),
                stages=stages, raw_attempts_verified=methods+judges, **expected,
                agent_assessed=True, human_validated=False, confirmatory_N=0,
                alpha_consumed=0, provider_calls=0, significance_test_performed=False,
                confirmation_authorized=False, production_admission=False)
