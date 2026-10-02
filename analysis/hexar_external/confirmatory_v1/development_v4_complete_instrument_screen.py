"""Fixed complete authored v4 screen; no prospective confirmation admission."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import hmac
import json
from pathlib import Path
import random
import secrets
import shutil
import subprocess

from .development_judge_call_v4 import call
from .development_rich_evaluator_bank_v4 import project
from .journal import canonical, exclusive_json, fingerprint, OneAttemptJournal
from .rich_evaluator_v4 import PROMPT, SCHEMA
from .rich_adjudication import needs_c, resolve

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'manifests/hexar_external/confirmatory_v1'
DEST = BASE / 'development_v4_complete_instrument_screen_v1'
BANKS = ('development_motion_fixture_bank_v1.json', 'development_controller_fixture_bank_v1.json',
         'development_rich_evaluator_bank_v4/fixtures.json')


def fixtures():
    rows = []
    for index, name in enumerate(BANKS):
        bank = json.loads((BASE / name).read_text())
        if bank.get('phase') != 'development_only':
            raise ValueError('development-only authored fixture bank required')
        for fixture in bank['fixtures']:
            if fixture.get('eligible_for_confirmatory_n') is not False:
                raise ValueError('authored fixture must be excluded from confirmation')
            payload = fixture['payload'] if 'payload' in fixture else project(fixture)
            if set(payload) != {'question', 'visible_evidence', 'required_units', 'answer'}:
                raise ValueError('method-neutral four-field judge payload required')
            rows.append(dict(fixture_id=f'{index}:{fixture["fixture_id"]}',
                             payload=copy.deepcopy(payload), expected=copy.deepcopy(fixture['expected'])))
    if len(rows) != 128 or len({r['fixture_id'] for r in rows}) != 128:
        raise ValueError('complete fixed 128-fixture screen required')
    return rows


def execute():
    rows = fixtures()
    DEST.mkdir(exist_ok=False)
    key = secrets.token_bytes(32)
    jobs, mapping = [], []
    for fixture in rows:
        slots = {}
        for slot in ('A', 'B', 'C'):
            uid = hmac.new(key, canonical([fixture['fixture_id'], slot, 'complete-v4-screen-v1']), hashlib.sha256).hexdigest()
            jobs.append(dict(opaque_job=uid, slot=slot, payload=fixture['payload']))
            slots[slot] = uid
        mapping.append(dict(fixture_id=fixture['fixture_id'], expected=fixture['expected'], slots=slots))
    random.SystemRandom().shuffle(jobs)
    exe = Path(shutil.which('codex')).resolve()
    source_paths = [Path(__file__), ROOT / 'docs/hexar_external/confirmatory_v1/DEVELOPMENT_V4_COMPLETE_INSTRUMENT_SCREEN.md']
    source_paths.extend(BASE / name for name in BANKS)
    source_paths.extend(Path(__file__).with_name(name) for name in
                        ('development_judge_call_v4.py', 'rich_evaluator_v4.py', 'rich_evaluator_v3.py',
                         'rich_evaluator_v2.py', 'rich_evaluator_candidate.py', 'rich_adjudication.py',
                         'rich_blind_projection.py', 'motion_usefulness.py', 'measurement_rounding.py', 'journal.py'))
    archive = DEST / 'source_archive'; archive.mkdir()
    for path in source_paths:
        target = archive / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    declaration = dict(schema='hexar-development-complete-v4-screen/v1', phase='development_only',
        confirmatory_N=0, alpha_consumed=0, fixture_n=128, initial_calls=256, maximum_C_calls=128,
        model='gpt-6-astra', reasoning_effort='high', prompt=PROMPT, output_schema=SCHEMA,
        workers=2, timeout_seconds=360, technical_retries=0, quality_retries=0,
        cli_path=str(exe), cli_version=subprocess.check_output([str(exe), '--version'], text=True).strip(),
        cli_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(), provider_binding_qualified=False,
        agent_assessed=True, human_validated=False,
        criterion='All 256 initial valid labels exactly match all four authored components; C does not rescue a failure.',
        source_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        job_registry=[dict(opaque_job=j['opaque_job'], slot=j['slot'], payload_sha256=fingerprint(j['payload'])) for j in jobs])
    exclusive_json(DEST / 'declaration.json', declaration)
    exclusive_json(DEST / 'public_jobs.json', jobs)
    exclusive_json(DEST / 'private_fixture_map.json', mapping)
    journal = OneAttemptJournal(DEST / 'journal', fingerprint(declaration))
    lookup = {j['opaque_job']: j for j in jobs}
    initial_jobs = [j for j in jobs if j['slot'] != 'C']
    with ThreadPoolExecutor(max_workers=2) as pool:
        initial = list(pool.map(lambda job: call(job, DEST, declaration, journal), initial_jobs))
    attempts = {r['opaque_job']: r for r in initial}
    selected = []
    for fixture in mapping:
        a, b = (attempts[fixture['slots'][slot]] for slot in ('A', 'B'))
        c = lookup[fixture['slots']['C']]
        if needs_c(a, b, c['payload']):
            selected.append(c)
    with ThreadPoolExecutor(max_workers=2) as pool:
        adjudication = list(pool.map(lambda job: call(job, DEST, declaration, journal), selected))
    C_attempts = {r['opaque_job']: r for r in adjudication}
    results, dispositions = [], []
    for fixture in mapping:
        expected = fixture['expected']
        for slot in ('A', 'B'):
            attempt = attempts[fixture['slots'][slot]]
            parsed = attempt.get('parsed')
            match = (attempt['status'] == 'VALID' and parsed['unsupported_material'] == expected['unsupported_material']
                     and parsed['overlicensed_specificity'] == expected['overlicensed_specificity']
                     and set(parsed['covered_units']) == set(expected['covered_units'])
                     and bool(parsed['ambiguous_spans']) == expected['material_ambiguity'])
            results.append(dict(attempt, fixture_id=fixture['fixture_id'], expected=expected, exact_agreement=match))
        a, b = (attempts[fixture['slots'][slot]] for slot in ('A', 'B'))
        c = C_attempts.get(fixture['slots']['C'])
        result = resolve(a, b, lookup[fixture['slots']['A']]['payload'], c)
        if result['status'] == 'NEEDS_C':
            raise ValueError('all authorized adjudications must close explicitly')
        dispositions.append(dict(fixture_id=fixture['fixture_id'], disposition=result))
    passed = all(r['exact_agreement'] for r in results)
    report = dict(schema='hexar-development-complete-v4-screen-report/v1', phase='development_only',
        status='COMPLETE_AUTHORED_V4_SCREEN_PASSED_NOT_FINAL_ENDPOINT_QUALIFICATION' if passed else 'FAILED_SCREEN_RETAINED',
        fixture_n=128, initial_calls=256, C_calls=len(adjudication), total_calls=256+len(adjudication),
        valid_initial_returns=sum(r['status'] == 'VALID' for r in results),
        exact_initial_agreements=sum(r['exact_agreement'] for r in results),
        unresolved_dispositions=sum(r['disposition']['status'] == 'UNRESOLVED' for r in dispositions),
        results=results, C_attempts=adjudication, dispositions=dispositions,
        declaration_sha256=fingerprint(declaration), agent_assessed=True, human_validated=False,
        provider_binding_qualified=False, whole_recording_endpoint_qualified=False,
        confirmatory_N=0, alpha_consumed=0, no_method_outputs_generated=True)
    exclusive_json(DEST / 'report.json', report)
    print(report['status'], report['exact_initial_agreements'], '/256', flush=True)


if __name__ == '__main__':
    execute()
