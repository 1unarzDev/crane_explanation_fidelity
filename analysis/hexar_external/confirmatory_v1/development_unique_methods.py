"""One generation per distinct v12 DEVELOPMENT method request, with aliases.

Untouched strengthened prompt and richer actual controller evidence for both
methods. This never admits or generates confirmatory outputs.
"""
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
from .journal import canonical,exclusive_json,fingerprint,OneAttemptJournal
from .unique_request_plan import build
from .strict_json import load
from .request_binding import parse_answer
from ..acquisition.navigation_contract import contract

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'manifests/hexar_external/confirmatory_v1'
DEST=BASE/'development_unique_methods_v1'
SCHEMA={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(cli_binding=None):
    source=ROOT/'manifests/hexar_external/acquisition/controller_boundary_qualification_v12_v2.json'
    audit=json.loads(source.read_text())
    if audit['phase']!='development_only' or audit['confirmatory_N']!=0 or audit['status']!='CANDIDATE_INTEGRITY_PASSED_NOT_FULL_QUALIFICATION':
        raise ValueError('retained development controller-boundary packet audit required')
    if len(audit['packets'])!=54:raise ValueError('complete six-episode battery required')
    prompt_path=ROOT/'docs/hexar_external/prompt_calibration_v1.txt'
    dependencies=[ROOT/'analysis/hexar_external/acquisition/navigation_contract.py',ROOT/'analysis/hexar_external/study_v2.py',
                  ROOT/'analysis/hexar_external/contract_adapter.py',ROOT/'analysis/maximal_supported_diagnosis.py',
                  ROOT/'analysis/realize_evidence_calibrated_explanation.py',ROOT/'analysis/evidence_calibration_io.py',
                  Path(__file__).with_name('strict_json.py'),Path(__file__).with_name('unique_request_plan.py'),Path(__file__).with_name('request_binding.py')]
    bindings={method:dict(development_only=True,provider_runtime_qualified=False,model='gpt-6-sol' if method=='HX-PROMPT' else 'none',
                         model_version=None,decoding_defaults_unresolved=True,reasoning_effort='high' if method=='HX-PROMPT' else None,
                         prompt_sha256=sha(prompt_path) if method=='HX-PROMPT' else None,quality_retries=0,technical_retries=0,
                         timeout_seconds=360,output_schema=SCHEMA,
                         source_hashes={str(p.relative_to(ROOT)):sha(p) for p in dependencies},cli_binding=cli_binding) for method in ('HX-PROMPT','HX-CONTRACT')}
    entries=[dict(episode_id=r['development_id'],method=method,job_id=f'{r["question_id"]}-{r["condition"]}',packet=r['method_packet'],implementation_binding=bindings[method])
             for r in audit['packets'] for method in ('HX-CONTRACT','HX-PROMPT')]
    plan=build(entries)
    if plan['battery_cells']!=108 or plan['unique_requests']!=72:raise ValueError('expected six distinct requests per method/episode')
    by_request={}
    for alias,entry in zip(plan['aliases'],sorted(entries,key=lambda e:(e['episode_id'],e['method'],e['job_id']))):
        # Explicit identity join rather than relying on incoming packet order.
        if (alias['episode_id'],alias['method'],alias['job_id'])!=(entry['episode_id'],entry['method'],entry['job_id']):raise ValueError('alias identity mismatch')
        by_request.setdefault(alias['unique_request_id'],entry)
    return source,prompt_path,plan,by_request


def write_raw(path,data):
    with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())


def execute():
    exe=Path(shutil.which('codex')).resolve()
    cli_binding=dict(executable_sha256=sha(exe),version=subprocess.check_output([str(exe),'--version'],text=True).strip())
    source,prompt_path,plan,lookup=prepare(cli_binding);prompt=prompt_path.read_text()
    DEST.mkdir(exist_ok=True)
    declaration=dict(schema='hexar-development-unique-methods/v1',phase='development_only',confirmatory_N=0,alpha_consumed=0,
        n_episodes=6,battery_cells=108,unique_requests=72,baseline_calls=36,contract_model_calls=0,
        provider_runtime_qualified=False,workers=2,timeout_seconds=360,quality_retries=0,technical_retries=0,
        baseline_model='gpt-6-sol',effort='high',prompt_sha256=sha(prompt_path),source_packet_manifest_sha256=sha(source),
        script_sha256=sha(__file__),cli_path=str(exe),cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),
        cli_sha256=sha(exe),request_plan_sha256=fingerprint(plan),
        purpose='strong equal-evidence method qualification on observed controller contexts and unique requests; no superiority test',
        strengthened_prompt_unchanged=True,word_limit_excess_retained_without_retry=True,criterion='All 72 unique attempts retained; both methods use identical permitted packet bytes; no alias-triggered retries; 72 valid required for complete transport qualification.')
    exclusive_json(DEST/'declaration.json',declaration);exclusive_json(DEST/'unique_request_plan.json',plan)
    journal=OneAttemptJournal(DEST/'journal',fingerprint(declaration))
    requests=list(plan['requests']);random.Random(2026100501).shuffle(requests)
    def call(request):
        uid=request['unique_request_id'];entry=lookup[uid];method=entry['method'];packet=entry['packet']
        if fingerprint(dict(packet=packet,implementation_binding=entry['implementation_binding']))!=request['request_sha256']:
            raise ValueError('sealed unique request binding changed before dispatch')
        folder=DEST/uid;folder.mkdir();identity=dict(unique_request_id=uid)
        dispatch=dict(request_sha256=request['request_sha256'],declaration_sha256=fingerprint(declaration))
        journal.claim(identity,dispatch)
        started=time.monotonic();outcome=dict(unique_request_id=uid,method=method,episode_id=entry['episode_id'],request_sha256=request['request_sha256'],packet_sha256=fingerprint(packet),status='TECHNICAL_FAILURE',answer=None,error=None,model_calls=int(method=='HX-PROMPT'))
        try:
            if sha(exe)!=declaration['cli_sha256']:raise ValueError('declared CLI executable changed')
            if method=='HX-CONTRACT':
                value=contract(packet,uid,entry['episode_id']);exclusive_json(folder/'contract.json',value);answer=value['answer']
            else:
                stdout=b'';stderr=b'';raw=b''
                with tempfile.TemporaryDirectory(prefix='hexar-unique-development-method-') as temporary:
                    cwd=Path(temporary);schema=cwd/'schema.json';schema.write_bytes(canonical(SCHEMA));final=cwd/'final.json'
                    command=[str(exe),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(cwd),'--model','gpt-6-sol','--config','model_reasoning_effort="high"','--output-schema',str(schema),'--output-last-message',str(final),'-']
                    text=prompt+'\nUNTRUSTED_DATA_BEGIN\n'+canonical(packet).decode()+'\nUNTRUSTED_DATA_END\n'
                    try:
                        completed=subprocess.run(command,input=text.encode(),capture_output=True,timeout=360,env={**os.environ,'NO_COLOR':'1'})
                        stdout,stderr,code=completed.stdout,completed.stderr,completed.returncode
                    except subprocess.TimeoutExpired as failure:stdout,stderr,code=failure.stdout or b'',failure.stderr or b'',124
                    raw=final.read_bytes() if final.exists() else b''
                for name,data in [('stdout.jsonl',stdout),('stderr.txt',stderr),('raw_final.json',raw)]:write_raw(folder/name,data)
                outcome['raw_sha256']={name:hashlib.sha256(data).hexdigest() for name,data in [('stdout',stdout),('stderr',stderr),('final',raw)]}
                events=[load(line) for line in stdout.splitlines()]
                if code!=0 or any(e.get('type') in ('error','turn.failed') or (type(e.get('item')) is dict and e['item'].get('type') not in ('agent_message','reasoning')) for e in events):raise ValueError('CLI/tool policy failure')
                answer=parse_answer(load(raw))
            outcome.update(status='VALID',answer=answer,answer_sha256=hashlib.sha256(answer.encode()).hexdigest(),word_count=len(answer.split()),output_word_allowance_met=len(answer.split())<=60)
        except Exception as failure:outcome['error']=f'{type(failure).__name__}: {failure}'
        outcome['latency_seconds']=time.monotonic()-started;journal.finish(identity,dispatch,outcome);exclusive_json(folder/'outcome.json',outcome)
        return outcome
    with ThreadPoolExecutor(max_workers=2) as executor:outcomes=list(executor.map(call,requests))
    status='UNIQUE_TRANSPORT_PASSED_NOT_SEMANTIC_QUALIFICATION' if all(r['status']=='VALID' for r in outcomes) else 'FAILED_RETAINED'
    exclusive_json(DEST/'report.json',dict(schema='hexar-development-unique-method-report/v1',phase='development_only',status=status,
        answers=outcomes,aliases=plan['aliases'],unique_attempts=72,valid=sum(r['status']=='VALID' for r in outcomes),
        baseline_calls=36,battery_cells=108,independent_development_episodes=6,confirmatory_N=0,alpha_consumed=0,
        same_evidence_for_both_methods=True,alias_failures_do_not_trigger_retry=True,semantic_superiority_test_performed=False))
    print(status,len(outcomes))


if __name__=='__main__':execute()
