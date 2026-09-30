#!/usr/bin/env python3
"""Exact runtime archive development candidate; no extraction, execution or P11 adoption."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tarfile
import uuid

from audit_evidence_calibration_runtime_tree import _scan, fingerprint, validate
from evidence_calibration_io import canonical_sha256
from observe_evidence_calibration_container_runtime_audit import IMAGE, ROOT, source_closure
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once


class BoundedWriter:
    def __init__(self, stream, maximum):
        self.stream, self.maximum, self.written = stream, maximum, 0
    def write(self, data):
        if self.written + len(data) > self.maximum:
            raise ValueError('archive byte budget exceeded')
        self.stream.write(data)
        self.written += len(data)
        return len(data)


def maximum_archive_bytes(record):
    validate(record)
    return sum(row.get('bytes', 0) for row in record['entries'].values()) + (len(record['entries']) + 1)*8192 + 64*1024**2


def _mtime(ns):
    absolute = abs(ns)
    return ('-' if ns < 0 else '') + str(absolute // 10**9) + '.' + f'{absolute % 10**9:09d}'


def _open_file(root_fd, path):
    fd = os.dup(root_fd)
    try:
        parts = path.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd); fd = child
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    finally:
        os.close(fd)


def export(root: Path, expected: dict, stream, *, progress=None):
    validate(expected)
    rows, before, metadata = _scan(root, hash_contents=False)
    projected = {path: {k:v for k,v in row.items() if k != 'raw_sha256'} for path,row in expected['entries'].items()}
    if rows != projected or metadata != expected['root_metadata']:
        raise ValueError('runtime metadata/paths differ from bound inventory')
    del rows, projected
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    written = BoundedWriter(stream, maximum_archive_bytes(expected))
    hardlinks = {}
    class HashReader:
        def __init__(self, fd):self.fd,self.digest=fd,hashlib.sha256()
        def read(self, count):
            data=os.read(self.fd,min(count,1024**2));self.digest.update(data);return data
    def header(path, row, stamp):
        info=tarfile.TarInfo(path)
        info.mode,info.uid,info.gid=row['mode'],row['uid'],row['gid']
        info.uname=info.gname=''
        info.mtime=stamp // 10**9
        info.pax_headers={'mtime':_mtime(stamp)}
        return info
    def attributes(info, target, *, symlink=False):
        keys = os.listxattr(target, follow_symlinks=False) if symlink else os.listxattr(target)
        for key in keys:
            value = os.getxattr(target,key,follow_symlinks=False) if symlink else os.getxattr(target,key)
            info.pax_headers['SCHILY.xattr.'+key] = value.decode('utf-8','surrogateescape')
    try:
        if fingerprint(os.fstat(root_fd)) != before['.']:
            raise ValueError('runtime root changed before export')
        with tarfile.open(fileobj=written,mode='w|',format=tarfile.PAX_FORMAT) as archive:
            info=header('usr',expected['root_metadata'],before['.'][6]);info.type=tarfile.DIRTYPE
            attributes(info,root_fd);archive.addfile(info)
            for ordinal,(path,row) in enumerate(sorted(expected['entries'].items()),1):
                info=header('usr/'+path,row,before[path][6])
                if row['kind']=='directory':
                    fd=_open_file(root_fd,path)
                    try:
                        if fingerprint(os.fstat(fd))!=before[path]:raise ValueError('runtime directory changed before export')
                        info.type=tarfile.DIRTYPE;attributes(info,fd);archive.addfile(info)
                    finally:os.close(fd)
                elif row['kind']=='symlink':
                    info.type=tarfile.SYMTYPE;info.linkname=row['target'];attributes(info,root/path,symlink=True);archive.addfile(info)
                else:
                    fd=_open_file(root_fd,path)
                    try:
                        current=os.fstat(fd)
                        if fingerprint(current)!=before[path] or not stat.S_ISREG(current.st_mode):
                            raise ValueError('runtime file changed before export')
                        attributes(info,fd)
                        key=(current.st_dev,current.st_ino)
                        if key in hardlinks:
                            target,digest,size=hardlinks[key]
                            if digest!=row['raw_sha256'] or size!=row['bytes']:
                                raise ValueError('hardlink identity differs from bound content')
                            info.type=tarfile.LNKTYPE;info.linkname=target;archive.addfile(info)
                        else:
                            reader=HashReader(fd);info.type=tarfile.REGTYPE;info.size=row['bytes']
                            archive.addfile(info,reader)
                            digest=reader.digest.hexdigest()
                            if digest!=row['raw_sha256']:
                                raise ValueError('runtime file content differs from bound inventory')
                            hardlinks[key]=(info.name,digest,row['bytes'])
                        if fingerprint(os.fstat(fd))!=before[path]:
                            raise ValueError('runtime file changed during export')
                    finally:os.close(fd)
                if progress is not None and ordinal % 5000 == 0:progress(ordinal,written.written)
        _,after,_=_scan(root,hash_contents=False)
        if before!=after:
            raise ValueError('runtime changed during snapshot export')
    finally:os.close(root_fd)
    return written.written


def verify_archive(path: Path, expected: dict) -> dict:
    validate(expected)
    initial=path.stat(follow_symlinks=False)
    if not stat.S_ISREG(initial.st_mode) or initial.st_size>maximum_archive_bytes(expected) or initial.st_size%512:
        raise ValueError('invalid archive file type, size or block framing')
    seen,files,attribute_values={},{},{}
    with tarfile.open(path,mode='r|') as archive:
        for member in archive:
            name=member.name.rstrip('/')
            if name in seen or (name!='usr' and not name.startswith('usr/')):
                raise ValueError('duplicate or outside-runtime archive member')
            relative=name[4:] if name!='usr' else '.'
            row=expected['root_metadata'] if relative=='.' else expected['entries'].get(relative)
            if row is None or (member.mode,member.uid,member.gid)!=(row['mode'],row['uid'],row['gid']):
                raise ValueError('archive metadata/paths differ from expected inventory')
            kind='directory' if relative=='.' else row['kind']
            if kind=='directory':
                if not member.isdir():raise ValueError('archive directory type mismatch')
            elif kind=='symlink':
                if not member.issym() or member.linkname!=row['target']:raise ValueError('archive symlink mismatch')
            else:
                if member.islnk():
                    if member.linkname not in files:raise ValueError('hardlink lacks a prior validated file')
                    digest,size=files[member.linkname]
                elif member.isfile():
                    handle=archive.extractfile(member);digest_object=hashlib.sha256();size=0
                    while True:
                        data=handle.read(1024**2)
                        if not data:break
                        digest_object.update(data);size+=len(data)
                    digest=digest_object.hexdigest()
                else:raise ValueError('archive regular-file type mismatch')
                if digest!=row['raw_sha256'] or size!=row['bytes']:raise ValueError('archive file content mismatch')
                files[name]=(digest,size)
            attribute_values[name]={k[13:]:v.encode('utf-8','surrogateescape').hex() for k,v in member.pax_headers.items() if k.startswith('SCHILY.xattr.')}
            seen[name]=True
        end_of_members=archive.offset
    with path.open('rb') as handle:
        handle.seek(end_of_members);tail_bytes=0
        while data:=handle.read(1024**2):
            tail_bytes+=len(data)
            if any(data):raise ValueError('nonzero material after archive end')
        if tail_bytes<1024:raise ValueError('archive lacks complete zero-block terminator')
    if set(seen)!={'usr',*('usr/'+name for name in expected['entries'])}:
        raise ValueError('archive omits expected runtime members')
    digest=hashlib.sha256()
    with path.open('rb') as handle:
        while data:=handle.read(1024**2):digest.update(data)
    if fingerprint(path.stat(follow_symlinks=False))!=fingerprint(initial):
        raise ValueError('archive changed during verification')
    return {'archive_raw_sha256':digest.hexdigest(),'archive_bytes':initial.st_size,
            'inventory_sha256':expected['inventory_sha256'],'validated_members':len(seen),
            'extended_attributes_sha256':canonical_sha256(attribute_values),
            'entries_with_extended_attributes':sum(bool(value) for value in attribute_values.values()),
            'extraction_or_runtime_restoration_verified':False}


CODE="""import json,sys
from pathlib import Path
sys.path.insert(0,'/audit')
from build_evidence_calibration_runtime_snapshot import export
expected=json.loads(Path('/expected.json').read_text())
export(Path('/host-runtime'),expected,sys.stdout.buffer,
 progress=lambda n,b: print(json.dumps({'entries_exported':n,'archive_bytes':b}),file=sys.stderr,flush=True))
"""


def create(expected_path: Path, directory: Path):
    expected=json.loads(expected_path.read_text());validate(expected)
    allowed=ROOT/'output/infrastructure'
    if directory.exists() or allowed.resolve() not in directory.resolve().parents:
        raise ValueError('fresh ignored infrastructure namespace required; no replay')
    directory.mkdir(parents=True)
    limit=maximum_archive_bytes(expected)
    if shutil.disk_usage(directory).free < limit+8*1024**3:
        raise ValueError('snapshot needs declared byte budget plus 8 GiB free reserve')
    code=directory/'code';code.mkdir()
    files=source_closure()
    for name in ('build_evidence_calibration_runtime_snapshot.py','observe_evidence_calibration_container_runtime_audit.py'):
        files[name]=(ROOT/'analysis'/name).read_bytes()
    for name,content in files.items():(code/name).write_bytes(content)
    image=json.loads(subprocess.run(['docker','image','inspect',IMAGE],capture_output=True,text=True,check=True,timeout=10).stdout)[0]
    identity={'schema':'crane-runtime-snapshot-request/v1-development','runtime_root':'/usr',
        'expected_inventory_sha256':expected['inventory_sha256'],
        'expected_raw_sha256':hashlib.sha256(expected_path.read_bytes()).hexdigest(),
        'audit_image':IMAGE,'image_id':image['Id'],'image_layers':image['RootFS']['Layers'],
        'source_files':{n:hashlib.sha256(b).hexdigest() for n,b in files.items()},
        'command_code_sha256':hashlib.sha256(CODE.encode()).hexdigest(),
        'maximum_archive_bytes':limit,'memory_bytes':2*1024**3,'cpus':2,'pids_limit':32,
        'timeout_seconds':1800,'model_call_attempted':False,'method_runtime_changed':False}
    identity_sha=canonical_sha256(identity);name='crane-runtime-snapshot-'+uuid.uuid4().hex
    _write_once(directory/'intent.json',{'request':identity,'request_sha256':identity_sha,'container_name':name,'terminal_record_pending':True})
    argv=['docker','run','--rm','--pull=never','--platform','linux/amd64','--name',name,
        '--label','crane.runtime-snapshot='+identity_sha,'--network','none','--read-only','--cap-drop','ALL',
        '--cap-add','DAC_READ_SEARCH','--security-opt','no-new-privileges','--memory','2g','--cpus','2','--pids-limit','32',
        '--mount','type=bind,source=/usr,target=/host-runtime,readonly',
        '--mount','type=bind,source='+str(code.resolve())+',target=/audit,readonly',
        '--mount','type=bind,source='+str(expected_path.resolve())+',target=/expected.json,readonly',
        IMAGE,'python','-I','-S','-B','-c',CODE]
    result,error,status,absent=None,None,'FAILED_SNAPSHOT_RETAIN_NO_REPLAY',False
    try:
        with (directory/'runtime.tar').open('xb') as stdout,(directory/'stderr.bin').open('xb') as stderr:
            done=subprocess.run(argv,stdout=stdout,stderr=stderr,check=False,timeout=1800)
        if done.returncode:raise ValueError('snapshot exporter failed; partial archive retained')
        if any((code/n).read_bytes()!=b for n,b in files.items()):raise ValueError('staged snapshot source changed')
        result=verify_archive(directory/'runtime.tar',expected)
        status='EXACT_RUNTIME_ARCHIVE_VERIFIED_DEVELOPMENT_ONLY'
    except BaseException as exception:
        error=type(exception).__name__+': '+str(exception);raise
    finally:
        inspected=subprocess.run(['docker','container','inspect',name],capture_output=True,text=True,check=False,timeout=10)
        if inspected.returncode==0:
            state=json.loads(inspected.stdout)[0]
            if state.get('Config',{}).get('Labels',{}).get('crane.runtime-snapshot')==identity_sha:
                removed=subprocess.run(['docker','container','rm','--force',name],capture_output=True,check=False,timeout=10)
                absent=removed.returncode==0
        elif any(s in inspected.stderr for s in ('No such container: '+name,'No such object: '+name)):absent=True
        if not absent:status='FAILED_CLEANUP_UNKNOWN'
        terminal={'schema':'crane-runtime-snapshot-terminal/v1-development','request_sha256':identity_sha,
            'status':status,'result':result,'error':error,'container_removed_or_absent':absent,
            'scientific_runtime_adopted':False,'model_call_attempted':False,'method_runtime_changed':False}
        _write_once(directory/'terminal.json',terminal)
    return terminal


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory',type=Path,required=True);parser.add_argument('--directory',type=Path,required=True)
    args=parser.parse_args();record=create(args.inventory,args.directory);print(json.dumps(record,indent=2))
    return 0 if record['status']=='EXACT_RUNTIME_ARCHIVE_VERIFIED_DEVELOPMENT_ONLY' else 65


if __name__=='__main__':sys.exit(main())
