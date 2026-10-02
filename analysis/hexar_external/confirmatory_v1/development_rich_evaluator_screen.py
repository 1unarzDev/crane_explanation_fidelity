"""Predeclared, one-attempt agent-assessed development screens only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import time
from .development_evaluator_family_bank import BASE,ROOT
from .development_rich_evaluator_bank import project
from .rich_evaluator_candidate import PROMPT,SCHEMA,validate
from .journal import OneAttemptJournal,canonical,exclusive_json,fingerprint

def write_raw(path,data):
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())

def execute(stage):
    bank_path=BASE/'development_rich_evaluator_bank_v2/fixtures.json'
    bank=json.loads(bank_path.read_text());run=BASE/('development_rich_evaluator_'+stage+'_v1');run.mkdir(parents=True,exist_ok=True)
    if stage=='preflight':
        neutral=dict(question='What happened?',visible_evidence={'reported_navigation_outcome':'Navigation software reported failure.'},required_units=[dict(unit_id='reported_navigation_outcome',requirement='Communicate the reported software navigation failure.')],answer='Navigation software reported failure.')
        project(neutral)
        jobs=[dict(index=i,slot='TECHNICAL_ONLY',payload=neutral) for i in range(6)]
    else:
        preflight=BASE/'development_rich_evaluator_preflight_v1/report.json'
        admission=json.loads(preflight.read_text())
        if admission['status']!='TECHNICAL_PREFLIGHT_PASSED':raise ValueError('six-call preflight failed; full screen forbidden')
        jobs=[dict(index=i,slot=slot,payload=project(f)) for i,f in enumerate(bank['fixtures']) for slot in ('A','B')]
    for job in jobs:job['opaque_job']=hashlib.sha256(f'rich:{stage}:v1:{job["index"]}:{job["slot"]}'.encode()).hexdigest()
    random.Random(20261002).shuffle(jobs)
    exe=Path(shutil.which('codex')).resolve()
    declaration=dict(schema='hexar-development-rich-screen/v1',stage=stage,development_only=True,agent_assessed=True,human_validated=False,alpha_consumed=0,confirmatory_N=0,n_calls=len(jobs),workers=2,timeout_seconds=360,quality_retries=0,technical_retries=0,model='gpt-6-astra',reasoning_effort='high',prompt=PROMPT,output_schema=SCHEMA,bank_sha256=hashlib.sha256(bank_path.read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),cli_path=str(exe),cli_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),job_registry=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in jobs],runtime_unresolved=['immutable provider/model snapshot','full decoding defaults','inherited system instructions/environment','transport-level no-tools denial'],threshold='All six returns structurally valid and no tool/error events; no semantic qualification claim' if stage=='preflight' else 'All 40 valid returns exactly agree on unsupported_material, overlicensed_specificity and required-unit set; any missingness/disagreement fails; no threshold changes',old_calls_not_retried=True)
    if stage=='screen':declaration['preflight_report_sha256']=hashlib.sha256(preflight.read_bytes()).hexdigest()
    exclusive_json(run/'declaration.json',declaration)
    journal=OneAttemptJournal(run/'journal',fingerprint(declaration))
    def call(job):
        directory=run/job['opaque_job'];directory.mkdir()
        request=dict(model='gpt-6-astra',effort='high',prompt=PROMPT,schema=SCHEMA,payload=job['payload'],timeout_seconds=360,cli_sha256=declaration['cli_sha256'])
        journal.claim(dict(opaque_job=job['opaque_job']),request)
        started=time.monotonic();status='TECHNICAL_FAILURE';parsed=None;error=None;stdout=b'';stderr=b'';raw=b'';returncode=None;events=[]
        try:
            with tempfile.TemporaryDirectory(prefix='hexar-rich-development-') as temporary:
                work=Path(temporary);schema=work/'schema.json';schema.write_bytes(canonical(SCHEMA));final=work/'final.json'
                command=[str(exe),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(work),'--model','gpt-6-astra','--config','model_reasoning_effort="high"','--output-schema',str(schema),'--output-last-message',str(final),'-']
                prompt=PROMPT+'\nUNTRUSTED_DATA_BEGIN\n'+canonical(job['payload']).decode()+'\nUNTRUSTED_DATA_END\n'
                try:
                    completed=subprocess.run(command,input=prompt.encode(),capture_output=True,timeout=360,env={**os.environ,'NO_COLOR':'1'})
                    stdout,stderr,returncode=completed.stdout,completed.stderr,completed.returncode
                except subprocess.TimeoutExpired as timeout:stdout,stderr,returncode=timeout.stdout or b'',timeout.stderr or b'',124
                raw=final.read_bytes() if final.exists() else b''
            events=[json.loads(line) for line in stdout.splitlines()]
            policy_failure=any(e.get('type') in ('error','turn.failed') or (type(e.get('item')) is dict and e['item'].get('type') not in ('agent_message','reasoning')) for e in events)
            if returncode!=0 or policy_failure:raise ValueError(f'transport/tool failure: code={returncode}, policy={policy_failure}')
            parsed=validate(json.loads(raw),job['payload']);status='VALID'
        except Exception as exc:error=f'{type(exc).__name__}: {exc}'
        write_raw(directory/'stdout.jsonl',stdout);write_raw(directory/'stderr.txt',stderr);write_raw(directory/'raw_final.json',raw)
        outcome=dict(status=status,parsed=parsed,error=error,returncode=returncode,latency_seconds=time.monotonic()-started,event_types=[e.get('type') for e in events],raw_sha256={name:hashlib.sha256(data).hexdigest() for name,data in [('stdout',stdout),('stderr',stderr),('final',raw)]})
        journal.finish(dict(opaque_job=job['opaque_job']),request,outcome)
        print('rich-'+stage,job['opaque_job'],status,round(outcome['latency_seconds'],1),flush=True)
        return dict(opaque_job=job['opaque_job'],fixture_index=job['index'],slot=job['slot'],**outcome)
    with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(call,jobs))
    # Expected labels never enter dispatched payloads and are joined only now.
    if stage=='screen':
        for result in results:
            fixture=bank['fixtures'][result['fixture_index']];expected=fixture['expected'];parsed=result['parsed']
            result.update(fixture_id=fixture['fixture_id'],expected=expected,exact_agreement=result['status']=='VALID' and parsed['unsupported_material']==expected['unsupported_material'] and parsed['overlicensed_specificity']==expected['overlicensed_specificity'] and set(parsed['covered_units'])==set(expected['covered_units']))
    passed=all(r['status']=='VALID' for r in results) and (stage=='preflight' or all(r['exact_agreement'] for r in results))
    report=dict(schema='hexar-development-rich-screen-report/v1',stage=stage,status=('TECHNICAL_PREFLIGHT_PASSED' if stage=='preflight' else 'AUTHORED_SCREEN_PASSED_NOT_FULL_QUALIFICATION') if passed else 'FAILED_RETAINED',calls=len(jobs),valid_returns=sum(r['status']=='VALID' for r in results),exact_agreements=None if stage=='preflight' else sum(r['exact_agreement'] for r in results),provider_retries=0,alpha_consumed=0,confirmatory_N=0,agent_assessed=True,human_validated=False,results=results)
    exclusive_json(run/'report.json',report);return passed

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['preflight','screen','pipeline'],required=True);args=parser.parse_args()
    if args.stage=='pipeline':
        if execute('preflight'):execute('screen')
    else:execute(args.stage)
if __name__=='__main__':main()
