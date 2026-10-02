"""Frozen raw-confirmation container capture; no explanation/judge backend.

Requires independent committed admission at each operation. The durable host
claim prevents relaunch even if invoked separately from the schedule controller.
"""
import json
import os
import re
from pathlib import Path
import subprocess
import time

from .raw_acquisition_admission_v1 import load_context,BASE
from .raw_archive_v1 import digest,rooted
from ..confirmatory_v1.journal import exclusive_json
from ..confirmatory_v1.registered_attempt_executor_v2 import raw_file


def command(config,record,freeze_sha256,root,phase="raw_confirmation"):
    if phase not in ('raw_confirmation','development_adapter_qualification'):
        raise ValueError('explicit bound acquisition phase required')
    scope='hexar-raw-confirmation' if phase=='raw_confirmation' else 'hexar-development'
    return ['docker','run','--name','crane-'+record['episode_id'],'--label','org.crane.scope='+scope,
        '--cidfile',str(rooted(root,config['execution_root'])/'attempts'/record['acquisition_id']/'container_id.txt'),
        '--network','none','--cpus',config['cpus'],'--memory',config['memory'],
        '--memory-swap',config['memory_swap'],'--shm-size',config['shared_memory'],
        '-e','ROS_DOMAIN_ID='+str(config['ros_domain_id']),
        '-v',str(rooted(root,config['source_bank_path']))+':/acquisition:ro',
        '-v',str(rooted(root,config['capture_root']))+':/provenance',
        '--entrypoint','/bin/bash',config['image_id'],'/acquisition/run_bound_episode_v1.sh',
        record['family'],str(record['seed']),record['episode_id'],phase,freeze_sha256]


class Runtime:
    def __init__(self,root,base=BASE,phase='raw_confirmation'):
        if phase not in ('raw_confirmation','development_adapter_qualification'):
            raise ValueError('explicit bound acquisition phase required')
        self.root,self.base,self.phase=Path(root).resolve(),base,phase

    def context(self,record,attempt_folder):
        if self.phase!='raw_confirmation':
            raise ValueError('development adapter requires separate committed development admission')
        ctx=load_context(self.root,self.base)
        if record not in ctx['plan']['records']:raise ValueError('unfrozen raw episode allocation')
        expected=rooted(self.root,ctx['config']['execution_root'])/'attempts'/record['acquisition_id']
        if Path(attempt_folder).resolve()!=expected:raise ValueError('unfrozen raw execution root')
        claim=json.loads((expected/'claim.json').read_text())
        if (claim.get('planned')!=record or claim.get('binding_sha256')!=ctx['freeze_sha256']
                or claim.get('launch_limit')!=1 or claim.get('method_or_judge_calls_permitted') is not False):
            raise ValueError('durable admitted raw attempt claim required')
        return ctx

    def capture(self,record,attempt_folder):
        ctx=self.context(record,attempt_folder);config=ctx['config'];attempt_folder=Path(attempt_folder)
        cap_root=rooted(self.root,config['capture_root']);cap_root.mkdir(parents=True,exist_ok=True)
        folder=cap_root/record['episode_id']
        if folder.exists():raise ValueError('raw capture identity exists; never reuse or overwrite')
        launch=command(config,record,ctx['freeze_sha256'],self.root,self.phase)
        claim_path=attempt_folder/'host_launch_claim.json'
        exclusive_json(claim_path,dict(schema='hexar-bound-raw-launch-claim/v1',phase=self.phase,
            acquisition_binding_sha256=ctx['freeze_sha256'],allocated=record,command=launch,
            launch_limit=1,method_or_judge_calls_permitted=False))
        name='crane-'+record['episode_id'];start=time.monotonic();code=-1;error=None
        stdout,stderr=b'',b'';info={};fresh=False
        try:
            prior=subprocess.run(['docker','inspect',name],capture_output=True)
            if prior.returncode==0:raise ValueError('prior container identity exists; never relaunch or delete it')
            observed_image=subprocess.check_output(['docker','inspect','--format','{{.Id}}',config['image_id']],text=True).strip()
            if observed_image!=config['image_id']:raise ValueError('qualified immutable image ID unavailable or changed')
            try:
                result=subprocess.run(launch,capture_output=True,timeout=config['episode_wall_timeout_seconds'])
                code,stdout,stderr=result.returncode,result.stdout,result.stderr
            except subprocess.TimeoutExpired as exc:
                code,stdout,stderr=124,exc.stdout or b'',exc.stderr or b''
                error='container wall-clock limit'
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc)
        finally:
            # On host interruption stop the physics process without replaying it.
            # A durable scheduler claim remains indeterminate and cannot rerun.
            cid_path=attempt_folder/'container_id.txt'
            cid=cid_path.read_text().strip() if cid_path.exists() else None
            if cid is not None and re.fullmatch('[0-9a-f]{64}',cid):
                stopped=subprocess.run(['docker','inspect',cid],capture_output=True)
                if stopped.returncode==0:
                    try:
                        info=json.loads(stopped.stdout)[0]
                        fresh=info.get('Id')==cid
                        if info.get('State',{}).get('Running'):
                            subprocess.run(['docker','kill',cid],capture_output=True)
                            stopped=subprocess.run(['docker','inspect',cid],capture_output=True)
                            if stopped.returncode==0:info=json.loads(stopped.stdout)[0]
                    except (ValueError,KeyError,TypeError):info={};fresh=False
            if folder.exists():
                subprocess.run(['docker','run','--rm','--network','none','-v',str(cap_root)+':/provenance',
                    '--entrypoint','chown',config['image_id'],'-R',f'{os.getuid()}:{os.getgid()}',
                    '/provenance/'+record['episode_id']],capture_output=True)
            folder.mkdir(exist_ok=True)
            raw_file(attempt_folder/'stdout.bin',stdout);raw_file(attempt_folder/'stderr.bin',stderr)
            with (folder/'host_execution.log').open('x') as stream:
                stream.write((stdout+stderr).decode('utf-8',errors='replace'))
            metadata=dict(schema='hexar-frozen-raw-capture/v1',episode_id=record['episode_id'],
                family_hidden=record['family'],seed_hidden=record['seed'],
                acquisition_phase=self.phase,acquisition_binding_sha256=ctx['freeze_sha256'],
                container_id=info.get('Id'),image_id=config['image_id'],observed_image_id=info.get('Image'),
                fresh_container=fresh,launch_claim_path=str(claim_path.relative_to(self.root)),
                launch_claim_sha256=digest(claim_path),requested_network_mode='none',
                observed_network_mode=info.get('HostConfig',{}).get('NetworkMode'),
                requested_ros_domain_id=config['ros_domain_id'],
                observed_ros_domain_id=next((e.split('=',1)[1] for e in info.get('Config',{}).get('Env',[])
                    if e.startswith('ROS_DOMAIN_ID=')),None),
                exit_code=code,wall_seconds=time.monotonic()-start,error=error,
                source_hashes=config['source_hashes'],execution_source_bank_sha256=config['execution_source_bank_sha256'],
                method_outputs_generated=False,judge_labels_generated=False,raw_files=[],
                transport_raw_sha256={name:digest(attempt_folder/name) for name in ('stdout.bin','stderr.bin')})
            for path in sorted(folder.rglob('*')):
                if path.is_file():metadata['raw_files'].append(dict(path=str(path.relative_to(self.root)),
                    sha256=digest(path),size=path.stat().st_size))
            exclusive_json(folder/'provenance.json',metadata)
        return metadata
