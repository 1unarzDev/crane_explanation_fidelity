"""One-attempt blinded agent stability screen on retained development answers.

No reference accuracy, human validation, whole-recording effect or test claim.
"""
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

from .journal import OneAttemptJournal, canonical, exclusive_json, fingerprint
from .rich_evaluator_v2 import PROMPT, SCHEMA, validate
from .rich_blind_projection import project
from ..acquisition.navigation_references import build

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'
DEST=BASE/'development_real_packet_screen_v1'


def prepare():
    methods_path=BASE/'development_rich_methods_v1/report.json'
    packets_path=ROOT/'manifests/hexar_external/acquisition/navigation_packet_qualification_v2.json'
    packets=json.loads(packets_path.read_text())['packets']
    lookup={f'{r["development_id"]}-{r["question_id"]}-{r["condition"]}':r for r in packets}
    answers=json.loads(methods_path.read_text())['answers']
    jobs=[]
    for answer in answers:
        row=lookup[answer['job_id']]
        if row['condition']!='intact':continue
        if answer['status']!='VALID' or hashlib.sha256(answer['answer'].encode()).hexdigest()!=answer['answer_sha256']:
            raise ValueError('retained valid raw answer required')
        packet=row['method_packet']
        if fingerprint(packet)!=answer['packet_sha256']:raise ValueError('method evidence binding mismatch')
        payload=project(packet,build(packet),answer['answer'])
        for slot in ('A','B'):
            opaque=hashlib.sha256(canonical([answer['job_id'],answer['method'],slot,'real-packet-screen-v1'])).hexdigest()
            jobs.append(dict(opaque_job=opaque,payload=payload,slot=slot,
                             administrative_join=dict(job_id=answer['job_id'],method=answer['method'])))
    if len(jobs)!=72:raise ValueError('fixed 36-answer / 72-call complete intact-battery screen required')
    random.Random(20261003).shuffle(jobs)
    return jobs, methods_path, packets_path


def raw_write(path,data):
    with path.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def execute():
    jobs,methods_path,packets_path=prepare()
    fixture_admission=BASE/'development_rich_evaluator_screen_v2/report.json'
    if json.loads(fixture_admission.read_text())['status']!='AUTHORED_SCREEN_PASSED_NOT_FULL_QUALIFICATION':
        raise ValueError('authored screen prerequisite missing')
    DEST.mkdir(exist_ok=True)
    exe=Path(shutil.which('codex')).resolve()
    declaration=dict(schema='hexar-development-real-packet-screen/v1',development_only=True,
        purpose='blinded agent repeatability on real retained development answers; not semantic accuracy or superiority',
        confirmatory_N=0,alpha_consumed=0,n_calls=72,n_answers=36,n_episodes=6,agent_assessed=True,human_validated=False,
        condition='intact',question_selection='all three navigation queries in all six v11 episodes, both methods',
        model='gpt-6-astra',reasoning_effort='high',prompt=PROMPT,output_schema=SCHEMA,
        workers=2,timeout_seconds=360,technical_retries=0,quality_retries=0,
        criterion='72 valid returns and exact A/B agreement on support, specificity and required-unit sets for all 36 answers; failure retained',
        immutable_backend_and_decoding_bound=False,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        cli_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),
        input_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (methods_path,packets_path,fixture_admission,
            Path(__file__).with_name('rich_blind_projection.py'), Path(__file__).with_name('rich_evaluator_v2.py'),
            Path(__file__).with_name('rich_evaluator_candidate.py'),ROOT/'analysis/hexar_external/acquisition/navigation_references.py')},
        jobs=[dict(opaque_job=j['opaque_job'],payload_sha256=fingerprint(j['payload'])) for j in jobs])
    exclusive_json(DEST/'declaration.json',declaration)
    journal=OneAttemptJournal(DEST/'journal',fingerprint(declaration))
    def call(job):
        folder=DEST/job['opaque_job'];folder.mkdir()
        journal.claim(dict(opaque_job=job['opaque_job']),dict(payload=job['payload'],declaration_sha256=fingerprint(declaration)))
        started=time.monotonic();stdout=b'';stderr=b'';raw=b'';parsed=None;error=None;code=None;status='TECHNICAL_FAILURE'
        try:
            with tempfile.TemporaryDirectory(prefix='hexar-real-development-') as temporary:
                work=Path(temporary);schema=work/'schema.json';schema.write_bytes(canonical(SCHEMA));final=work/'final.json'
                command=[str(exe),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(work),'--model','gpt-6-astra','--config','model_reasoning_effort="high"','--output-schema',str(schema),'--output-last-message',str(final),'-']
                prompt=PROMPT+'\nUNTRUSTED_DATA_BEGIN\n'+canonical(job['payload']).decode()+'\nUNTRUSTED_DATA_END\n'
                try:
                    result=subprocess.run(command,input=prompt.encode(),capture_output=True,timeout=360,env={**os.environ,'NO_COLOR':'1'})
                    stdout,stderr,code=result.stdout,result.stderr,result.returncode
                except subprocess.TimeoutExpired as failure:stdout,stderr,code=failure.stdout or b'',failure.stderr or b'',124
                raw=final.read_bytes() if final.exists() else b''
            events=[json.loads(line) for line in stdout.splitlines()]
            if code!=0 or any(e.get('type') in ('error','turn.failed') or
                (type(e.get('item')) is dict and e['item'].get('type') not in ('agent_message','reasoning')) for e in events):
                raise ValueError('transport/tool/error event')
            parsed=validate(json.loads(raw),job['payload']);status='VALID'
        except Exception as failure:error=f'{type(failure).__name__}: {failure}'
        for name,data in [('stdout.jsonl',stdout),('stderr.txt',stderr),('raw_final.json',raw)]:raw_write(folder/name,data)
        value=dict(opaque_job=job['opaque_job'],status=status,parsed=parsed,error=error,returncode=code,
                   latency_seconds=time.monotonic()-started,slot=job['slot'],**job['administrative_join'],
                   raw_sha256={name:hashlib.sha256(data).hexdigest() for name,data in [('stdout',stdout),('stderr',stderr),('final',raw)]})
        journal.record(dict(opaque_job=job['opaque_job']),status,value)
        return value
    with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(call,jobs))
    paired={}
    for row in results:paired.setdefault((row['job_id'],row['method']),{})[row['slot']]=row
    agreement=[]
    for (job_id,method),slots in paired.items():
        a,b=slots['A'],slots['B'];exact=a['status']==b['status']=='VALID'
        if exact:
            x,y=a['parsed'],b['parsed'];exact=all(x[k]==y[k] for k in ('unsupported_material','overlicensed_specificity')) and set(x['covered_units'])==set(y['covered_units'])
        agreement.append(dict(job_id=job_id,method=method,exact_component_agreement=exact))
    passed=all(r['status']=='VALID' for r in results) and all(r['exact_component_agreement'] for r in agreement)
    report=dict(schema='hexar-development-real-packet-screen-report/v1',status='REPEATABILITY_PASSED_NOT_ACCURACY_QUALIFIED' if passed else 'FAILED_RETAINED',
                valid_returns=sum(r['status']=='VALID' for r in results),exact_answer_agreements=sum(r['exact_component_agreement'] for r in agreement),
                expected_calls=72,expected_answers=36,results=results,agreements=agreement,agent_assessed=True,human_validated=False,
                alpha_consumed=0,confirmatory_N=0,superiority_test_performed=False,whole_recording_endpoint_qualified=False)
    exclusive_json(DEST/'report.json',report)
    print(report['status'],report['valid_returns'],report['exact_answer_agreements'])


if __name__=='__main__':execute()
