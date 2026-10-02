"""Versioned development-only CLI judge dispatch, durable one-attempt archives.

This is not a prospective provider admission or confirmation adapter.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import time
import json
from .journal import canonical,fingerprint
from .rich_evaluator_v4 import PROMPT,SCHEMA,validate


def write_raw(path,data):
    with path.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def call(job,run,declaration,journal):
    folder=run/job['opaque_job'];folder.mkdir()
    request=dict(payload=job['payload'],declaration_sha256=fingerprint(declaration),slot=job['slot'])
    journal.claim(dict(opaque_job=job['opaque_job']),request)
    started=time.monotonic();stdout=b'';stderr=b'';raw=b'';parsed=None;error=None;code=None;status='TECHNICAL_FAILURE'
    try:
        with tempfile.TemporaryDirectory(prefix='hexar-full-battery-development-') as temporary:
            work=Path(temporary);schema=work/'schema.json';schema.write_bytes(canonical(SCHEMA));final=work/'final.json'
            command=[declaration['cli_path'],'exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(work),'--model',declaration['model'],'--config','model_reasoning_effort="high"','--output-schema',str(schema),'--output-last-message',str(final),'-']
            prompt=PROMPT+'\nUNTRUSTED_DATA_BEGIN\n'+canonical(job['payload']).decode()+'\nUNTRUSTED_DATA_END\n'
            try:
                result=subprocess.run(command,input=prompt.encode(),capture_output=True,timeout=declaration['timeout_seconds'],env={**os.environ,'NO_COLOR':'1'})
                stdout,stderr,code=result.stdout,result.stderr,result.returncode
            except subprocess.TimeoutExpired as failure:stdout,stderr,code=failure.stdout or b'',failure.stderr or b'',124
            raw=final.read_bytes() if final.exists() else b''
        events=[json.loads(line) for line in stdout.splitlines()]
        if code!=0 or any(e.get('type') in ('error','turn.failed') or
            (type(e.get('item')) is dict and e['item'].get('type') not in ('agent_message','reasoning')) for e in events):
            raise ValueError('transport/tool/error event')
        parsed=validate(json.loads(raw),job['payload']);status='VALID'
    except Exception as failure:error=f'{type(failure).__name__}: {failure}'
    for name,data in [('stdout.jsonl',stdout),('stderr.txt',stderr),('raw_final.json',raw)]:write_raw(folder/name,data)
    value=dict(opaque_job=job['opaque_job'],status=status,parsed=parsed,error=error,returncode=code,
               latency_seconds=time.monotonic()-started,slot=job['slot'],
               raw_sha256={name:hashlib.sha256(data).hexdigest() for name,data in [('stdout',stdout),('stderr',stderr),('final',raw)]})
    journal.finish(dict(opaque_job=job['opaque_job']),request,value)
    return value
