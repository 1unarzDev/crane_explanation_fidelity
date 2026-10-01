"""Read-only reproduction of actual development registries/raw/closed scoring."""
import hashlib
from pathlib import Path

from .journal import fingerprint
from .strict_json import load
from .registered_attempt_executor import registry as make_registry
from .request_binding import parse_answer
from .rich_evaluator_v4 import validate
from .development_registered_backend import transcript_policy
from .blinded_scoring_workflow import finalize

ROOT = Path(__file__).resolve().parents[3]


def read(path):
    return load(path.read_bytes(), maximum_bytes=32*1024*1024)


def audit(run):
    run = Path(run)
    declaration = read(run/'declaration.json')
    report = read(run/'report.json')
    if (declaration['phase'] != 'development_only' or declaration['confirmatory_N'] != 0
            or declaration['alpha_consumed'] != 0 or report['declaration_sha256'] != fingerprint(declaration)):
        raise ValueError('development declaration/report binding differs')
    for name, digest in declaration['source_hashes'].items():
        if hashlib.sha256((run/'source_archive'/name).read_bytes()).hexdigest() != digest:
            raise ValueError('preserved execution source changed')
    neutral, plan, outputs, public, private = (read(run/name) for name in
        ('neutral_reference_registry.json', 'unique_method_plan.json', 'method_outputs.json',
         'public_scoring_plan.json', 'sealed_method_linkage.json'))
    if (fingerprint(neutral) != declaration['neutral_reference_registry_sha256']
            or fingerprint(plan) != declaration['unique_plan_sha256']):
        raise ValueError('method-neutral pre-generation registry or unique plan changed')
    phases, registries, raw_count = {}, {}, 0
    for phase in ('methods', 'initial_judges', 'adjudication_judges'):
        path = run/(phase+'_registry.json')
        if not path.exists():
            phases[phase] = {}
            continue
        reg = read(path)
        plain_jobs = [dict(job_id=j['job_id'], request=j['request']) for j in reg['jobs']]
        if (reg != make_registry(fingerprint(declaration), 'development_qualification', plain_jobs)
                or read(run/phase/'registered_jobs.json') != reg):
            raise ValueError('dispatch registry differs from sealed declaration/root')
        if phase == 'methods' and fingerprint(plain_jobs) != declaration['method_jobs_sha256']:
            raise ValueError('method registry differs from pre-dispatch declaration')
        registries[phase] = reg
        attempts = {}
        for job in reg['jobs']:
            identity = dict(opaque_job=job['job_id'])
            handle = fingerprint(dict(freeze_sha256=fingerprint(declaration), job=identity))
            claim = read(run/phase/'journal'/(handle+'.claim.json'))
            closed = read(run/phase/'journal'/(handle+'.outcome.json'))
            expected = dict(schema='hexar-one-attempt/v1', freeze_sha256=fingerprint(declaration),
                job=identity, request_sha256=fingerprint(dict(registry_sha256=fingerprint(reg),
                    request_sha256=job['request_sha256'])), attempt_count=1)
            if claim != expected or closed['attempt'] != expected:
                raise ValueError('durable registered one-attempt identity changed')
            outcome = closed['outcome']
            folder = run/phase/fingerprint(identity)
            raw = {}
            for name, digest in outcome['raw_sha256'].items():
                raw[name] = (folder/name).read_bytes()
                if hashlib.sha256(raw[name]).hexdigest() != digest:
                    raise ValueError('exact retained transport bytes changed')
            if set(raw) != {'raw_response.json', 'stdout.bin', 'stderr.bin'}:
                raise ValueError('all original raw transport artifacts required')
            if outcome['status']=='VALID':
                parsed = load(raw['raw_response.json'], job['request']['maximum_response_bytes'])
                if job['request']['role']=='judge':
                    parsed = validate(parsed, job['request']['payload'])
                else:
                    parse_answer(parsed)
                if parsed != outcome['parsed']:
                    raise ValueError('raw/parsed outcome differs')
                if job['request']['role'] != 'contract' and not transcript_policy(raw['stdout.bin'], 0):
                    raise ValueError('valid CLI output violates retained turn/tool policy')
                if job['request']['role']=='contract' and read(folder/'stdout.bin')['answer'] != parsed['answer']:
                    raise ValueError('contract derivation differs from retained answer')
            attempts[job['job_id']] = outcome
            raw_count += 1
        if (len(list((run/phase/'journal').glob('*.claim.json'))) != len(attempts)
                or len(list((run/phase/'journal').glob('*.outcome.json'))) != len(attempts)):
            raise ValueError('unexpected/pending phase attempt')
        phases[phase] = attempts
    expected_methods = {r['unique_request_id']:r for r in plan['requests']}
    if set(phases['methods']) != set(expected_methods) or len(outputs) != 12:
        raise ValueError('exact twelve unique method dispositions required')
    method_requests = {j['job_id']:j['request'] for j in registries['methods']['jobs']}
    for row in outputs:
        uid = row['unique_request_id']
        source, outcome, request = expected_methods[uid], phases['methods'][uid], method_requests[uid]
        if (row['status'] != outcome['status'] or row['raw_sha256'] != outcome['raw_sha256']
                or row['packet_sha256'] != source['packet_sha256']
                or fingerprint(request['payload']) != source['packet_sha256']
                or row['request_sha256'] != source['request_sha256']
                or row['method'] != source['method'] or row['episode_id'] != source['episode_id']):
            raise ValueError('method output/plan/evidence provenance differs')
        if row['status']=='VALID':
            if row['answer'] != outcome['parsed']['answer'] or hashlib.sha256(row['answer'].encode()).hexdigest() != row['answer_sha256']:
                raise ValueError('method answer changed')
    for phase, jobs in (('initial_judges', public['initial_jobs']), ('adjudication_judges', read(run/'selected_C_jobs.json'))):
        if {j['opaque_job'] for j in jobs} != set(phases[phase]):
            raise ValueError('registered judge dispatches differ from opaque workflow schedule')
        requests = {j['job_id']:j['request'] for j in registries.get(phase, {}).get('jobs', [])}
        for j in jobs:
            if requests[j['opaque_job']]['payload'] != j['payload'] or requests[j['opaque_job']]['role'] != 'judge':
                raise ValueError('judge saw changed evidence or prior labels')
    reproduced = finalize(plan, outputs, neutral, public, private, phases['initial_judges'], phases['adjudication_judges'])
    if reproduced != read(run/'closed_dispositions.json') or reproduced['paired_counts'] != report['paired_counts']:
        raise ValueError('whole-episode scoring reproduction differs')
    if raw_count != 12+report['initial_judge_attempts']+report['C_attempts']:
        raise ValueError('raw attempted-call accounting differs')
    return dict(schema='hexar-development-registered-pipeline-archive-audit/v1',
        status='ACTUAL_DEVELOPMENT_PIPELINE_REPRODUCED_NOT_FINAL_ADAPTER_QUALIFICATION',
        raw_unique_attempts_verified=raw_count, unique_method_attempts=12,
        paired_counts=reproduced['paired_counts'], provider_calls=0, confirmatory_N=0, alpha_consumed=0,
        report_sha256=hashlib.sha256((run/'report.json').read_bytes()).hexdigest())


if __name__=='__main__':
    import json
    print(json.dumps(audit(ROOT/'manifests/hexar_external/confirmatory_v1/development_registered_pipeline_v1'), indent=2))
