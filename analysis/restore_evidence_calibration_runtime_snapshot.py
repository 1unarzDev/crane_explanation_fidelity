#!/usr/bin/env python3
"""Restore a bound runtime candidate into a fresh local directory; no method adoption."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from build_evidence_calibration_runtime_snapshot import verify_archive
from evidence_calibration_io import canonical_sha256
from observe_evidence_calibration_container_runtime_audit import IMAGE,ROOT,source_closure
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once

CODE="""import json,subprocess,sys
from pathlib import Path
sys.path.insert(0,'/audit')
from verify_evidence_calibration_runtime_restoration import verify
expected=json.loads(Path('/expected.json').read_text())
subprocess.run(['/bin/tar','--extract','--file=/runtime.tar','--directory=/restored',
 '--same-owner','--same-permissions','--numeric-owner','--xattrs','--xattrs-include=*','--delay-directory-restore'],check=True)
result=verify(Path('/restored/usr'),Path('/runtime.tar'),expected)
print(json.dumps(result))
"""


def restore(archive: Path, inventory_path: Path, directory: Path) -> dict:
    expected=json.loads(inventory_path.read_text())
    verified=verify_archive(archive,expected)
    if directory.exists() or (ROOT/'output/infrastructure').resolve() not in directory.resolve().parents:
        raise ValueError('fresh ignored restoration namespace required; no adoption/replay')
    directory.mkdir(parents=True)
    if shutil.disk_usage(directory).free < verified['archive_bytes']+8*1024**3:
        raise ValueError('restoration needs archive size plus 8 GiB free reserve')
    destination=directory/'root';destination.mkdir()
    code=directory/'code';code.mkdir()
    files=source_closure()
    files['verify_evidence_calibration_runtime_restoration.py']=(ROOT/'analysis/verify_evidence_calibration_runtime_restoration.py').read_bytes()
    for name,content in files.items():(code/name).write_bytes(content)
    identity={'schema':'crane-runtime-restoration-request/v1-development','archive_verification':verified,
        'helper_image':IMAGE,'controller_raw_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'command_code_sha256':hashlib.sha256(CODE.encode()).hexdigest(),
        'source_files':{name:hashlib.sha256(value).hexdigest() for name,value in files.items()},
        'capabilities':['DAC_OVERRIDE','DAC_READ_SEARCH','CHOWN','FOWNER','SETFCAP','FSETID'],
        'network':'none','helper_rootfs_read_only':True,'writable_mount':'fresh restoration root only',
        'timeout_seconds':1800,'memory_bytes':2*1024**3,'cpus':2,'pids_limit':32,
        'method_runtime_changed':False,'model_call_attempted':False}
    digest=canonical_sha256(identity);name='crane-runtime-restore-'+uuid.uuid4().hex
    _write_once(directory/'intent.json',{'request':identity,'request_sha256':digest,'container_name':name,'terminal_record_pending':True})
    argv=['docker','run','--rm','--pull=never','--platform','linux/amd64','--name',name,
        '--label','crane.runtime-restore='+digest,'--network','none','--read-only','--cap-drop','ALL',
        '--security-opt','no-new-privileges','--pids-limit','32','--memory','2g','--cpus','2']
    for capability in identity['capabilities']:argv+=['--cap-add',capability]
    for source,target,readonly in [(archive,'/runtime.tar',True),(inventory_path,'/expected.json',True),
                                  (code,'/audit',True),(destination,'/restored',False)]:
        argv+=['--mount','type=bind,source='+str(source.resolve())+',target='+target+(',readonly' if readonly else '')]
    argv += [IMAGE,'python','-I','-S','-B','-c',CODE]
    status,result,error,absent='FAILED_RESTORATION_RETAIN_NO_REPLAY',None,None,False
    try:
        with (directory/'stdout.json').open('xb') as stdout,(directory/'stderr.bin').open('xb') as stderr:
            done=subprocess.run(argv,stdout=stdout,stderr=stderr,check=False,timeout=1800)
        if done.returncode:raise ValueError('restoration failed; retain partial tree and raw error')
        result=json.loads((directory/'stdout.json').read_text())
        if result['inventory_sha256']!=verified['inventory_sha256'] or result['extended_attributes_sha256']!=verified['extended_attributes_sha256']:
            raise ValueError('restoration return differs from archive binding')
        if any((code/n).read_bytes()!=b for n,b in files.items()):raise ValueError('staged verifier source changed')
        status='RESTORED_RUNTIME_IDENTITY_VERIFIED_EXECUTION_AND_ADOPTION_OPEN'
    except BaseException as exception:
        error=type(exception).__name__+': '+str(exception);raise
    finally:
        inspected=subprocess.run(['docker','container','inspect',name],capture_output=True,text=True,check=False,timeout=10)
        if inspected.returncode==0:
            state=json.loads(inspected.stdout)[0]
            if state.get('Config',{}).get('Labels',{}).get('crane.runtime-restore')==digest:
                removed=subprocess.run(['docker','container','rm','--force',name],capture_output=True,check=False,timeout=10)
                absent=removed.returncode==0
        elif any(x in inspected.stderr for x in ('No such container: '+name,'No such object: '+name)):absent=True
        if not absent:status='FAILED_CLEANUP_UNKNOWN'
        terminal={'schema':'crane-runtime-restoration-terminal/v1-development','request_sha256':digest,
            'status':status,'result':result,'error':error,'container_removed_or_absent':absent,
            'restored_tree_is_immutable':False,'execution_parity_verified':False,
            'scientific_runtime_adopted':False,'model_call_attempted':False}
        _write_once(directory/'terminal.json',terminal)
    return terminal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--directory',type=Path,required=True)
    a=p.parse_args();r=restore(a.archive,a.inventory,a.directory);print(json.dumps(r,indent=2))
    return 0 if r['status']=='RESTORED_RUNTIME_IDENTITY_VERIFIED_EXECUTION_AND_ADOPTION_OPEN' else 65


if __name__=='__main__':sys.exit(main())
