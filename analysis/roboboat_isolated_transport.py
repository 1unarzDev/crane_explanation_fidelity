"""Marine isolation wrapper around the existing login-backed CLI invocation protocol."""
import hashlib,json,os,shutil,subprocess,tempfile,time,tomllib
from pathlib import Path


def isolated_run(command, **kwargs):
    """Injectable subprocess runner for the qualified annotation caller.

    System runtime + ephemeral call workspace only. No research/home/source mounts.
    """
    command=list(command);cwd=Path(command[command.index('--cd')+1]).resolve()
    binary=Path(shutil.which(command[0])).resolve()
    with tempfile.TemporaryDirectory(prefix='boat-cli-home-') as tmp:
        home=Path(tmp); host=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
        # Copy credentials only to an ephemeral isolated provider home, never output artifacts.
        for name in ('auth.json','models_cache.json'):
            if (host/name).is_file():shutil.copyfile(host/name,home/name)
        config=tomllib.loads((host/'config.toml').read_text())
        provider=config['model_provider'];p=config['model_providers'][provider]
        lines=[f'model_provider = {json.dumps(provider)}','[shell_environment_policy]','inherit = "none"',
               '[features]','apps = false','plugins = false','browser_use = false','computer_use = false',
               'image_generation = false','code_mode_host = true',f'[model_providers.{provider}]']
        for key in ('name','base_url','wire_api','env_key','requires_openai_auth','supports_websockets'):
            if key in p:lines.append(f'{key} = {json.dumps(p[key])}')
        (home/'config.toml').write_text('\n'.join(lines)+'\n')
        # The entire caller-owned temporary directory includes schema and output files.
        mounts=['bwrap','--unshare-all','--share-net','--die-with-parent','--ro-bind',str(binary),'/codex',
                '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc',
                '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--bind',str(cwd),str(cwd),
                '--bind',str(home),'/provider-home','--chdir',str(cwd),'--clearenv',
                '--setenv','HOME','/provider-home','--setenv','CODEX_HOME','/provider-home',
                '--setenv','PATH','/usr/bin:/bin','--setenv','NO_COLOR','1']
        key=p.get('env_key')
        if key and os.environ.get(key):mounts+=['--setenv',key,os.environ[key]]
        companion=binary.parent/'codex-code-mode-host'
        if not companion.is_file(): raise RuntimeError('CLI companion host missing')
        mounts+=['--ro-bind',str(companion),'/codex-code-mode-host',
                 '--ro-bind',str(binary.parent.parent/'codex-resources'),'/codex-resources',
                 '--setenv','CODEX_BWRAP_PATH','/codex-resources/bwrap']
        command[0]='/codex'
        kwargs.pop('env',None)
        return subprocess.run(mounts+command,**kwargs)


def call(cache, role, packet_dir, prompt, model, effort, schema, allow_tools=True, timeout=300):
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    identity={'transport':'marine-isolated-login-cli/v1','role':role,'model':model,'effort':effort,
              'prompt':prompt,'schema':schema,'allow_tools':allow_tools,
              'workspace_files':{str(p.relative_to(packet_dir)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in sorted(packet_dir.rglob('*')) if p.is_file()},
              'transport_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    key=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();out=cache/f'{key}.json'
    if out.exists():
        result=json.loads(out.read_text())
        if result['status']!='valid':raise RuntimeError(f'retained failure: {out}')
        return result
    started=time.time()
    with tempfile.TemporaryDirectory(prefix='boat-method-') as tmp:
        work=Path(tmp);shutil.copytree(packet_dir,work,dirs_exist_ok=True)
        schema_file=work/'return-schema.json';schema_file.write_text(json.dumps(schema));output=work/'answer.json'
        cmd=['codex','exec','--json','--ephemeral','--skip-git-repo-check','--sandbox','read-only','--cd',str(work),
             '--model',model,'--config',f'model_reasoning_effort="{effort}"','--output-schema',str(schema_file),
             '--output-last-message',str(output),'-']
        try:
            result=isolated_run(cmd,input=prompt,text=True,capture_output=True,check=False,timeout=timeout)
            returncode=result.returncode;events=[]
            for line in result.stdout.splitlines():
                try:events.append(json.loads(line))
                except ValueError:events.append({'unparsed':line})
            raw=output.read_text() if output.exists() else ''
            value=json.loads(raw) if raw else None
            bad_tools=not allow_tools and any(e.get('item',{}).get('type') not in (None,'reasoning','agent_message') for e in events)
            status='valid' if returncode==0 and value is not None and not bad_tools else 'failed'
            error=None
        except (subprocess.TimeoutExpired,ValueError) as exc:
            status='failed';value=None;events=[];returncode=124;error=str(exc)
    record={'request':identity,'cache_key':key,'status':status,'parsed_final':value,'return_code':returncode,
            'events':events,'latency_s':time.time()-started,'error':error,'attempt_count':1,'cost_usd':None}
    temp=out.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(out)
    if status!='valid':raise RuntimeError(f'retained failure: {out}')
    return record
