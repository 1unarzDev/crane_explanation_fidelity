"""One declared nonsemantic CLI transport probe; never study admission."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from .journal import OneAttemptJournal,canonical,exclusive_json,fingerprint

ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'manifests/hexar_external/confirmatory_v1/development_provider_probe_v1'


def main():
    exe=Path(shutil.which('codex')).resolve();RUN.mkdir(parents=True,exist_ok=True)
    schema={'type':'object','properties':{'status':{'type':'string','enum':['ready']}},'required':['status'],'additionalProperties':False}
    declaration=dict(schema='hexar-development-provider-probe/v1',phase='development_only',calls=1,
        model_alias='gpt-6-astra',effort='high',timeout_seconds=60,retries=0,
        cli_version=subprocess.check_output([str(exe),'--version'],text=True).strip(),
        executable_sha256=hashlib.sha256(exe.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),output_schema=schema,
        purpose='nonsemantic transport availability after usage-limit notification; not support scoring',
        confirmatory_n=0,alpha_consumed=0,immutable_model_and_environment_bound=False)
    exclusive_json(RUN/'declaration.json',declaration)
    journal=OneAttemptJournal(RUN/'journal',fingerprint(declaration));job={'probe':'nonsemantic-availability'}
    prompt='Do not use tools. Return only the JSON object {"status":"ready"}.'
    request=dict(prompt=prompt,model_alias=declaration['model_alias'],output_schema=schema)
    journal.claim(job,request);stdout=b'';stderr=b'';raw=b'';code=None;error=None;status='TECHNICAL_FAILURE'
    with tempfile.TemporaryDirectory(prefix='hexar-provider-probe-') as temp:
        work=Path(temp);spec=work/'schema.json';spec.write_bytes(canonical(schema));final=work/'final.json'
        command=[str(exe),'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(work),
            '--model','gpt-6-astra','--config','model_reasoning_effort="high"','--output-schema',str(spec),'--output-last-message',str(final),'-']
        try:
            r=subprocess.run(command,input=prompt.encode(),capture_output=True,timeout=60,env={**os.environ,'NO_COLOR':'1'})
            stdout,stderr,code=r.stdout,r.stderr,r.returncode
        except subprocess.TimeoutExpired as exc:stdout,stderr,code=exc.stdout or b'',exc.stderr or b'',124
        raw=final.read_bytes() if final.exists() else b''
    for name,data in [('stdout.jsonl',stdout),('stderr.txt',stderr),('raw_final.json',raw)]:
        with (RUN/name).open('xb') as f:f.write(data)
    try:
        events=[json.loads(line) for line in stdout.splitlines()]
        if code or any(e.get('type') in ('error','turn.failed') or (type(e.get('item')) is dict and e['item'].get('type') not in ('agent_message','reasoning')) for e in events):
            raise ValueError('transport or observed tool/error event failure')
        if json.loads(raw)!={'status':'ready'}:raise ValueError('unexpected probe output')
        status='VALID'
    except Exception as exc:error=type(exc).__name__+': '+str(exc)
    outcome=dict(status=status,returncode=code,error=error,confirmatory_n=0,alpha_consumed=0,
        semantic_qualification=False,raw_sha256={n:hashlib.sha256(b).hexdigest() for n,b in [('stdout',stdout),('stderr',stderr),('final',raw)]})
    journal.finish(job,request,outcome);exclusive_json(RUN/'report.json',outcome);print(json.dumps(outcome))


if __name__=='__main__':main()
