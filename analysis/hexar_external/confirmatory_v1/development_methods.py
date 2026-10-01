"""Six-family q1/all-mask development interface pilot, not confirmation."""
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from .journal import OneAttemptJournal,exclusive_json,canonical,fingerprint
from .request_binding import parse_answer

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'analysis/hexar_external'))
from study_v2 import contract
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'
RUN=BASE/'development_method_interface_v1'
SCHEMA={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    interface=ROOT/'manifests/hexar_external/acquisition/interface_audit_v3.json'
    audit=json.loads(interface.read_text())
    if audit['phase']!='development_only' or audit['status']!='INTERFACE_COMPATIBLE_NOT_FULL_ACQUISITION_QUALIFICATION':
        raise ValueError('complete development interface audit required')
    packets=[p for p in audit['packet_records'] if p['question_id']=='q1']
    if len(packets)!=18:raise ValueError('exact six-family/three-mask development slice required')
    prompt=(ROOT/'docs/hexar_external/prompt_calibration_v1.txt').read_text()
    executable=Path(shutil.which('codex')).resolve()
    RUN.mkdir(parents=True,exist_ok=True)
    declaration=dict(schema='hexar-development-method-interface/v1',phase='development_only',confirmatory_N=0,
                     alpha_consumed=0,methods=['HX-PROMPT','HX-CONTRACT'],baseline_model='gpt-6-sol',effort='high',
                     workers=2,quality_retries=0,technical_retries=0,baseline_calls=18,contract_model_calls=0,
                     packet_audit_sha256=sha(interface),prompt_sha256=sha(ROOT/'docs/hexar_external/prompt_calibration_v1.txt'),
                     contract_sha256=sha(ROOT/'analysis/hexar_external/study_v2.py'),script_sha256=sha(__file__),
                     cli_version=subprocess.check_output([str(executable),'--version'],text=True).strip(),cli_sha256=sha(executable),
                     immutable_backend_and_decoding_bound=False,all_family_q1_slice_only=True,
                     semantic_superiority_scoring_authorized=False,
                     purpose='qualify strong baseline/contract transport and equal packet evidence; not empirical power or full whole-recording scoring')
    exclusive_json(RUN/'declaration.json',declaration)
    journal=OneAttemptJournal(RUN/'journal',fingerprint(declaration))
    def run(packet):
        opaque=hashlib.sha256(packet['job_id'].encode()).hexdigest()
        entries=[]
        for method in ('HX-CONTRACT','HX-PROMPT'):
            output=RUN/(opaque+'-'+method);output.mkdir()
            request=dict(method=method,packet_sha256=packet['packet_sha256'],prompt_sha256=declaration['prompt_sha256'] if method=='HX-PROMPT' else None)
            job={'packet_handle':opaque,'method':method};journal.claim(job,request)
            outcome={'status':'TECHNICAL_FAILURE','method':method,'job_id':packet['job_id'],'packet_sha256':packet['packet_sha256']}
            try:
                if fingerprint(packet['method_packet'])!=packet['packet_sha256']:
                    # Existing canonical packet utility uses the same sorted
                    # serialization? Verify its actual canonical digest instead.
                    from evidence_calibration_io import canonical_sha256
                    if canonical_sha256(packet['method_packet'])!=packet['packet_sha256']:raise ValueError('packet hash changed')
                if method=='HX-CONTRACT':
                    value=contract(packet['method_packet'],opaque,packet['recording_id'])
                    exclusive_json(output/'contract.json',value);answer=value['answer']
                else:
                    with tempfile.TemporaryDirectory(prefix='hexar-development-method-') as temp:
                        cwd=Path(temp);schema=cwd/'schema.json';schema.write_bytes(canonical(SCHEMA));final=cwd/'final.json'
                        cmd=[str(executable),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(cwd),'--model','gpt-6-sol','--config','model_reasoning_effort="high"','--output-schema',str(schema),'--output-last-message',str(final),'-']
                        input_text=prompt+'\nUNTRUSTED_EXECUTION_PACKET_BEGIN\n'+canonical(packet['method_packet']).decode()+'\nUNTRUSTED_EXECUTION_PACKET_END\nReturn only the JSON answer object. Do not use tools.'
                        try:
                            result=subprocess.run(cmd,input=input_text.encode(),capture_output=True,timeout=180,env={**os.environ,'NO_COLOR':'1'})
                            stdout,stderr,code=result.stdout,result.stderr,result.returncode
                        except subprocess.TimeoutExpired as exc:
                            stdout,stderr,code=exc.stdout or b'',exc.stderr or b'',124
                        raw=final.read_bytes() if final.exists() else b''
                        for name,data in (('stdout.jsonl',stdout),('stderr.txt',stderr),('raw_final.json',raw)):
                            with (output/name).open('xb') as stream:stream.write(data)
                        events=[json.loads(line) for line in stdout.splitlines()]
                        violation=any(e.get('type') in ('error','turn.failed') or (isinstance(e.get('item'),dict) and e['item'].get('type') not in ('agent_message','reasoning')) for e in events)
                        if code or violation:raise ValueError('CLI/tool policy failure')
                        answer=parse_answer(json.loads(raw))
                outcome.update(status='VALID',answer=answer,answer_sha256=hashlib.sha256(answer.encode()).hexdigest(),model_calls=int(method=='HX-PROMPT'))
            except Exception as exc:outcome['error']=f'{type(exc).__name__}: {exc}'
            journal.finish(job,request,outcome);exclusive_json(output/'outcome.json',outcome)
            print(opaque,method,outcome['status'],flush=True);entries.append(outcome)
        return entries
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        results=[r for pair in pool.map(run,packets) for r in pair]
    exclusive_json(RUN/'report.json',dict(schema='hexar-development-method-interface-report/v1',phase='development_only',
                                         confirmatory_N=0,alpha_consumed=0,method_packets_equal=True,
                                         answers=results,valid=sum(r['status']=='VALID' for r in results),expected=36,
                                         whole_recording_semantic_qualification=False,semantic_superiority_test_performed=False))

if __name__=='__main__':main()
