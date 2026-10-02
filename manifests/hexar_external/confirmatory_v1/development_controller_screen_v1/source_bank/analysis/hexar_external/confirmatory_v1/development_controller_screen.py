"""Predeclared two-pass authored controller screen, DEVELOPMENT only."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess

from .development_judge_call import call
from .journal import exclusive_json, fingerprint, OneAttemptJournal
from .rich_evaluator_v3 import PROMPT, SCHEMA

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'
DEST=BASE/'development_controller_screen_v1'


def agrees(value, expected):
    return (value['unsupported_material']==expected['unsupported_material']
        and value['overlicensed_specificity']==expected['overlicensed_specificity']
        and set(value['covered_units'])==set(expected['covered_units'])
        and bool(value['ambiguous_spans'])==expected['material_ambiguity'])


def execute():
    bank_path=BASE/'development_controller_fixture_bank_v1.json'
    bank=json.loads(bank_path.read_text());fixtures=bank['fixtures']
    if bank['phase']!='development_only' or bank['confirmatory_N']!=0 or len(fixtures)!=48:
        raise ValueError('48 declared authored development fixtures required')
    jobs=[dict(opaque_job=hashlib.sha256(f'controller-screen-v1:{i}:{slot}'.encode()).hexdigest(),
               slot=slot,payload=f['payload']) for i,f in enumerate(fixtures) for slot in ('A','B')]
    lookup={j['opaque_job']:f for i,f in enumerate(fixtures) for j in jobs[2*i:2*i+2]}
    random.Random(2026100504).shuffle(jobs)
    prerequisite=BASE/'development_unique_scoring_v1/report.json'
    if json.loads(prerequisite.read_text())['status']!='WORKFLOW_COMPLETE_NOT_ACCURACY_QUALIFIED':
        raise ValueError('completed runtime workflow prerequisite required')
    sources=[Path(__file__),bank_path,prerequisite]
    for name in ('development_judge_call.py','rich_evaluator_v3.py','rich_evaluator_v2.py','rich_evaluator_candidate.py'):
        sources.append(Path(__file__).with_name(name))
    exe=Path(shutil.which('codex')).resolve()
    declaration=dict(schema='hexar-development-controller-screen/v1',phase='development_only',
        n_calls=len(jobs),workers=2,timeout_seconds=360,technical_retries=0,quality_retries=0,
        model='gpt-6-astra',reasoning_effort='high',prompt=PROMPT,output_schema=SCHEMA,
        cli_path=str(exe),cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),
        cli_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),provider_runtime_qualified=False,
        threshold='All 96 returns valid and exactly match authored support/specificity/required-unit set/ambiguity presence. Any missingness or disagreement fails; no retries or adjudication.',
        agent_assessed=True,human_validated=False,whole_recording_endpoint_qualified=False,
        confirmatory_N=0,alpha_consumed=0,
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        job_registry=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in jobs])
    DEST.mkdir(exist_ok=True);exclusive_json(DEST/'declaration.json',declaration)
    for path in sources:
        archive=DEST/'source_bank'/path.relative_to(ROOT);archive.parent.mkdir(parents=True,exist_ok=True)
        with archive.open('xb') as stream:stream.write(path.read_bytes())
    journal=OneAttemptJournal(DEST/'journal',fingerprint(declaration))
    def dispatch(job):
        if hashlib.sha256(exe.read_bytes()).hexdigest()!=declaration['cli_sha256']:
            raise ValueError('CLI changed during declared screen; do not issue a call')
        for path in sources:
            if hashlib.sha256(path.read_bytes()).hexdigest()!=declaration['source_hashes'][str(path.relative_to(ROOT))]:
                raise ValueError('screen source changed during execution; do not issue a call')
        return call(job,DEST,declaration,journal)
    with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(dispatch,jobs))
    for result in results:
        fixture=lookup[result['opaque_job']]
        result.update(fixture_id=fixture['fixture_id'],expected=fixture['expected'],
                      exact_agreement=result['status']=='VALID' and agrees(result['parsed'],fixture['expected']))
    passed=all(r['exact_agreement'] for r in results)
    report=dict(schema='hexar-development-controller-screen-report/v1',phase='development_only',
        status='AUTHORED_SCREEN_PASSED_NOT_FULL_QUALIFICATION' if passed else 'FAILED_RETAINED',
        calls=len(results),valid_returns=sum(r['status']=='VALID' for r in results),
        exact_agreements=sum(r['exact_agreement'] for r in results),results=results,
        agent_assessed=True,human_validated=False,whole_recording_endpoint_qualified=False,
        confirmatory_N=0,alpha_consumed=0,provider_retries=0)
    exclusive_json(DEST/'report.json',report)
    print(report['status'],report['valid_returns'],report['exact_agreements'])


if __name__=='__main__':execute()
