"""Unchanged marine CLI isolation with credential-safe failure and partial traces.

Versioned additive transport; historical v1 requests and source bytes stay intact.
"""
import hashlib,json,os,shutil,subprocess,tempfile,time,tomllib
from pathlib import Path


from roboboat_writable_isolation_v2 import isolated_run


def provider_secret_values():
    """Known environment credential values, used only for output redaction."""
    host=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
    config=tomllib.loads((host/'config.toml').read_text())
    key=config['model_providers'][config['model_provider']].get('env_key')
    return tuple([os.environ[key]]) if key and os.environ.get(key) else ()


def redact(value, secrets):
    if isinstance(value, str):
        for secret in secrets:
            value=value.replace(secret,'[PROVIDER_CREDENTIAL_REDACTED]')
        return value
    if isinstance(value, dict):return {redact(k,secrets):redact(v,secrets) for k,v in value.items()}
    if isinstance(value, list):return [redact(v,secrets) for v in value]
    return value


def safe_events(stdout, secrets):
    if isinstance(stdout,bytes):stdout=stdout.decode('utf-8',errors='replace')
    events=[]
    for line in (stdout or '').splitlines():
        line=redact(line,secrets)
        try:events.append(redact(json.loads(line),secrets))
        except ValueError:events.append({'unparsed':line})
    return events


def call(cache, role, packet_dir, prompt, model, effort, schema, allow_tools=True, timeout=300):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    identity={'transport':'marine-isolated-login-cli/v5-public-ro-narrow-staging','role':role,'model':model,'effort':effort,
              'prompt':prompt,'schema':schema,'allow_tools':allow_tools,'timeout_s':timeout,
              'workspace_files':{str(p.relative_to(packet_dir)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(packet_dir.rglob('*')) if p.is_file()},
              'sandbox':'workspace-write','public_mounts':'packet files and return-schema read-only; cwd/scratch caller-owned writable; outer /tmp read-only except caller-owned CLI daemon and synthetic mount registry overlays; shell network disabled',
              'transport_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'isolation_source_sha256':hashlib.sha256(Path(isolated_run.__code__.co_filename).read_bytes()).hexdigest()}
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();out=cache/f'{key}.json'
    if out.exists():
        result=json.loads(out.read_text())
        if result['status']!='valid':raise RuntimeError(f'retained failure: {out}')
        return result
    started=time.time()
    secrets=provider_secret_values()
    stderr='';partial_trace=False;error_kind=None
    with tempfile.TemporaryDirectory(prefix='boat-method-') as tmp:
        work=Path(tmp);shutil.copytree(packet_dir,work,dirs_exist_ok=True)
        (work/'scratch').mkdir()
        public_files={p:p.relative_to(packet_dir).as_posix() for p in packet_dir.rglob('*') if p.is_file()}
        schema_file=work/'return-schema.json';schema_file.write_text(json.dumps(schema));output=work/'answer.json'
        cmd=['codex','exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','workspace-write','--cd',str(work),
             '--model',model,'--config',f'model_reasoning_effort="{effort}"','--output-schema',str(schema_file),
             '--output-last-message',str(output),'-']
        public_files[schema_file]='return-schema.json'
        try:
            result=isolated_run(cmd,public_files=public_files,input=prompt,text=True,capture_output=True,check=False,timeout=timeout)
            returncode=result.returncode;events=safe_events(result.stdout,secrets)
            stderr=redact(result.stderr or '',secrets)
            raw=output.read_text() if output.exists() else ''
            value=json.loads(raw) if raw else None
            bad_tools=not allow_tools and any(e.get('item',{}).get('type') not in (None,'reasoning','agent_message') for e in events)
            credential_in_answer=bool(value is not None and any(s in json.dumps(value,ensure_ascii=False) for s in secrets))
            status='valid' if returncode==0 and value is not None and not bad_tools and not credential_in_answer else 'failed'
            value=redact(value,secrets)
            error=None
            if credential_in_answer:error='Provider credential appeared in answer; redacted and excluded.'
        except subprocess.TimeoutExpired as exc:
            # Never stringify this exception: cmd can contain --setenv secrets.
            status='failed';value=None;returncode=124
            events=safe_events(exc.output,secrets);partial_trace=True
            raw_stderr=exc.stderr or ''
            if isinstance(raw_stderr,bytes):raw_stderr=raw_stderr.decode('utf-8',errors='replace')
            stderr=redact(raw_stderr,secrets)
            error='Provider process exceeded declared timeout.';error_kind='TimeoutExpired'
        except ValueError:
            status='failed';value=None;events=[];returncode=124
            error='Provider output could not be parsed.';error_kind='ValueError'
        except OSError:
            status='failed';value=None;events=[];returncode=125
            error='Provider process could not start or access declared files.';error_kind='OSError'
    record={'request':identity,'cache_key':key,'status':status,'parsed_final':value,'return_code':returncode,
            'events':events,'stderr':stderr,'partial_trace':partial_trace,
            'latency_s':time.time()-started,'error':error,'error_kind':error_kind,
            'timeout_s':timeout,'attempt_count':1,'cost_usd':None}
    temp=out.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(out)
    if status!='valid':raise RuntimeError(f'retained failure: {out}')
    return record
