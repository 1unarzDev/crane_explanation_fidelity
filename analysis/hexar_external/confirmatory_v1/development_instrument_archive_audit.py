"""Read-only reproduction of the completed authored screen and raw archives.

No calls, repairs, retrospective preregistration, or confirmation authorization.
"""
import hashlib
from pathlib import Path

from .journal import fingerprint
from .strict_json import load
from .rich_evaluator_v4 import validate
from .rich_adjudication import needs_c, resolve

ROOT = Path(__file__).resolve().parents[3]


def read_artifact(path):
    # Registry/source evidence can exceed a single model-response bound.
    return load(path.read_bytes(), maximum_bytes=32 * 1024 * 1024)


def audit(run):
    run = Path(run)
    declaration = read_artifact(run / 'declaration.json')
    public = read_artifact(run / 'public_jobs.json')
    private = read_artifact(run / 'private_fixture_map.json')
    report = read_artifact(run / 'report.json')
    if (declaration['phase'] != 'development_only' or declaration['confirmatory_N'] != 0
            or declaration['alpha_consumed'] != 0 or report['declaration_sha256'] != fingerprint(declaration)):
        raise ValueError('development declaration/report binding differs')
    for name, digest in declaration['source_hashes'].items():
        if hashlib.sha256((run / 'source_archive' / name).read_bytes()).hexdigest() != digest:
            raise ValueError('preserved source archive changed')
    jobs = {j['opaque_job']: j for j in public}
    if len(jobs) != 384 or len(jobs) != len(public) or len(private) != 128:
        raise ValueError('complete fixed authored registry required')
    if declaration['job_registry'] != [dict(opaque_job=j['opaque_job'], slot=j['slot'],
                                          payload_sha256=fingerprint(j['payload'])) for j in public]:
        raise ValueError('declared public registry changed')
    if any(set(j) != {'opaque_job', 'slot', 'payload'} or
           set(j['payload']) != {'question', 'visible_evidence', 'required_units', 'answer'} for j in public):
        raise ValueError('judge payload must remain method neutral')
    used = [handle for f in private for handle in f['slots'].values()]
    if len(set(used)) != 384 or set(used) != set(jobs):
        raise ValueError('private fixture linkage changed')
    attempts = {}
    for row in report['results'] + report['C_attempts']:
        uid = row['opaque_job']
        if uid in attempts or uid not in jobs:
            raise ValueError('unexpected or duplicate closed attempt')
        job = jobs[uid]
        request = dict(payload=job['payload'], declaration_sha256=fingerprint(declaration), slot=job['slot'])
        identity = dict(opaque_job=uid)
        attempt = dict(schema='hexar-one-attempt/v1', freeze_sha256=fingerprint(declaration),
                       job=identity, request_sha256=fingerprint(request), attempt_count=1)
        handle = fingerprint(dict(freeze_sha256=fingerprint(declaration), job=identity))
        claim = load((run / 'journal' / (handle + '.claim.json')).read_bytes())
        closed = load((run / 'journal' / (handle + '.outcome.json')).read_bytes())
        if claim != attempt or closed['attempt'] != attempt:
            raise ValueError('durable single-attempt binding differs')
        outcome = {k: v for k, v in row.items() if k not in ('fixture_id', 'expected', 'exact_agreement')}
        if closed['outcome'] != outcome:
            raise ValueError('report differs from original closed outcome')
        for field, name in (('final', 'raw_final.json'), ('stdout', 'stdout.jsonl'), ('stderr', 'stderr.txt')):
            raw = (run / uid / name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != outcome['raw_sha256'][field]:
                raise ValueError('raw response archive changed')
            if field == 'final' and outcome['status'] == 'VALID':
                if validate(load(raw), job['payload']) != outcome['parsed']:
                    raise ValueError('parsed judgment differs from exact raw return')
        attempts[uid] = outcome
    expected_initial = {j['opaque_job'] for j in public if j['slot'] in ('A', 'B')}
    if {r['opaque_job'] for r in report['results']} != expected_initial:
        raise ValueError('all initial attempts must be retained')
    agreements, dispositions, selected_C = 0, [], set()
    for fixture in private:
        slots = fixture['slots']
        if set(slots) != {'A', 'B', 'C'} or any(jobs[h]['slot'] != s for s, h in slots.items()):
            raise ValueError('fixture slots differ')
        payload = jobs[slots['A']]['payload']
        if any(jobs[h]['payload'] != payload for h in slots.values()):
            raise ValueError('isolated judges did not share identical evidence')
        for slot in ('A', 'B'):
            outcome = attempts[slots[slot]]
            parsed, expected = outcome['parsed'], fixture['expected']
            match = (outcome['status'] == 'VALID' and
                     parsed['unsupported_material'] == expected['unsupported_material'] and
                     parsed['overlicensed_specificity'] == expected['overlicensed_specificity'] and
                     set(parsed['covered_units']) == set(expected['covered_units']) and
                     bool(parsed['ambiguous_spans']) == expected['material_ambiguity'])
            row = next(r for r in report['results'] if r['opaque_job'] == slots[slot])
            if row['expected'] != expected or row['fixture_id'] != fixture['fixture_id'] or row['exact_agreement'] != match:
                raise ValueError('authored expectation/agreement changed')
            agreements += match
        a, b = (attempts[slots[s]] for s in ('A', 'B'))
        if needs_c(a, b, payload):
            selected_C.add(slots['C'])
        result = resolve(a, b, payload, attempts.get(slots['C']))
        dispositions.append(dict(fixture_id=fixture['fixture_id'], disposition=result))
    if selected_C != {r['opaque_job'] for r in report['C_attempts']}:
        raise ValueError('C ran outside the disagreement-only policy')
    claims = list((run / 'journal').glob('*.claim.json'))
    outcomes = list((run / 'journal').glob('*.outcome.json'))
    if len(claims) != len(attempts) or len(outcomes) != len(attempts):
        raise ValueError('unreported or unfinished attempt exists')
    if dispositions != report['dispositions'] or agreements != report['exact_initial_agreements']:
        raise ValueError('screen disposition reproduction differs')
    unresolved = sum(r['disposition']['status'] == 'UNRESOLVED' for r in dispositions)
    valid = sum(r['status'] == 'VALID' for r in report['results'])
    status = ('COMPLETE_AUTHORED_V4_SCREEN_PASSED_NOT_FINAL_ENDPOINT_QUALIFICATION'
              if agreements == 256 else 'FAILED_SCREEN_RETAINED')
    if (report['status'] != status or report['unresolved_dispositions'] != unresolved
            or report['valid_initial_returns'] != valid or report['total_calls'] != len(attempts)):
        raise ValueError('summary differs from retained attempts')
    return dict(status='COMPLETED_DEVELOPMENT_ARCHIVE_REPRODUCED',
                report_status=status, exact_initial_agreements=agreements,
                raw_attempts_verified=len(attempts), C_calls=len(selected_C),
                unresolved_dispositions=unresolved, provider_calls=0, confirmatory_N=0,
                alpha_consumed=0, report_sha256=hashlib.sha256((run / 'report.json').read_bytes()).hexdigest())


if __name__ == '__main__':
    import json
    print(json.dumps(audit(ROOT / 'manifests/hexar_external/confirmatory_v1/development_v4_complete_instrument_screen_v1'), indent=2))
