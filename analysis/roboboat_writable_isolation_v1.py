"""Marine isolation wrapper around the existing login-backed CLI invocation protocol."""
import hashlib,json,os,shutil,subprocess,tempfile,time,tomllib
from pathlib import Path


def isolated_run(command, *, public_files, **kwargs):
    """Injectable subprocess runner for the qualified annotation caller.

    System runtime + ephemeral call workspace only. No research/home/source mounts.
    """
    command=list(command);cwd=Path(command[command.index('--cd')+1]).resolve()
    binary=Path(shutil.which(command[0])).resolve()
    original_cwd=str(cwd)
    command=[arg.replace(original_cwd,'/workspace') for arg in command]
    public_files={str(Path(p).resolve()):relative for p,relative in public_files.items()}
    if any(Path(relative).is_absolute() or '..' in Path(relative).parts for relative in public_files.values()):raise ValueError('unsafe public path')
    with tempfile.TemporaryDirectory(prefix='boat-cli-home-') as tmp:
        home=Path(tmp); host=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))
        # Copy credentials only to an ephemeral isolated provider home, never output artifacts.
        for name in ('auth.json','models_cache.json'):
            if (host/name).is_file():shutil.copyfile(host/name,home/name)
        config=tomllib.loads((host/'config.toml').read_text())
        provider=config['model_provider'];p=config['model_providers'][provider]
        lines=[f'model_provider = {json.dumps(provider)}','[shell_environment_policy]','inherit = "none"','[shell_environment_policy.set]','PATH = "/usr/bin:/bin"','TMPDIR = "/workspace/scratch"','[sandbox_workspace_write]','network_access = false','exclude_tmpdir_env_var = true','exclude_slash_tmp = true',
               '[features]','apps = false','plugins = false','browser_use = false','computer_use = false',
               'image_generation = false','code_mode_host = true',f'[model_providers.{provider}]']
        for key in ('name','base_url','wire_api','env_key','requires_openai_auth','supports_websockets'):
            if key in p:lines.append(f'{key} = {json.dumps(p[key])}')
        (home/'config.toml').write_text('\n'.join(lines)+'\n')
        # The entire caller-owned temporary directory includes schema and output files.
        mounts=['bwrap','--unshare-all','--share-net','--die-with-parent','--ro-bind',str(binary),'/codex',
                '--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib64','/lib64','--ro-bind','/etc','/etc',
                '--proc','/proc','--dev','/dev','--tmpfs','/tmp','--remount-ro','/tmp','--bind',str(cwd),'/workspace',
                '--bind',str(home),'/provider-home','--chdir','/workspace','--clearenv',
                '--setenv','HOME','/provider-home','--setenv','CODEX_HOME','/provider-home',
                '--setenv','TMPDIR','/workspace/scratch','--setenv','PATH','/usr/bin:/bin','--setenv','NO_COLOR','1']
        key=p.get('env_key')
        if key and os.environ.get(key):mounts+=['--setenv',key,os.environ[key]]
        companion=binary.parent/'codex-code-mode-host'
        if not companion.is_file(): raise RuntimeError('CLI companion host missing')
        mounts+=['--ro-bind',str(companion),'/codex-code-mode-host',
                 '--ro-bind',str(binary.parent.parent/'codex-resources'),'/codex-resources',
                 '--setenv','CODEX_BWRAP_PATH','/codex-resources/bwrap']
        for source,relative in public_files.items():mounts+=['--ro-bind',source,'/workspace/'+relative]
        command[0]='/codex'
        kwargs.pop('env',None)
        return subprocess.run(mounts+command,**kwargs)

