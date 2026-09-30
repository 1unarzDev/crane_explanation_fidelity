#!/usr/bin/env python3
"""Read-only container audit of the existing host runtime; no method runtime migration."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid

from audit_evidence_calibration_runtime_tree import validate, summary
from evidence_calibration_io import canonical_sha256
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once

ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'python@sha256:7bf6c3111fe094f8ee1a1cbcdc63c4cfb345b0e3df42d5aa9a90b3b4b022ab6d'
CODE = """import json,sys
from pathlib import Path
sys.path.insert(0,'/audit')
from audit_evidence_calibration_runtime_tree import inventory
def progress(n,b):
 print(json.dumps({'entries_hashed':n,'bytes_read':b}),file=sys.stderr,flush=True)
record=inventory(Path('/host-runtime'),progress=progress)
json.dump(record,sys.stdout,sort_keys=True,ensure_ascii=False)
sys.stdout.write('\\n')
"""


def source_closure() -> dict[str, bytes]:
    """Copy only static local-module dependencies; no repository data/configuration mounts."""
    pending, files = ['audit_evidence_calibration_runtime_tree'], {}
    while pending:
        name = pending.pop()
        path = ROOT / 'analysis' / (name + '.py')
        if name in files or not path.is_file():
            continue
        content = path.read_bytes()
        files[name] = content
        for node in ast.walk(ast.parse(content)):
            if isinstance(node, ast.Import):
                pending.extend(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                pending.append(node.module.split('.')[0])
    return {name + '.py': content for name, content in sorted(files.items())}


def command(runtime: Path, code_directory: Path, name: str, identity_sha: str) -> list[str]:
    return ['docker', 'run', '--rm', '--pull=never', '--platform', 'linux/amd64', '--name', name,
        '--label', 'crane.runtime-audit=' + identity_sha, '--network', 'none', '--read-only',
        '--cap-drop', 'ALL', '--cap-add', 'DAC_READ_SEARCH', '--security-opt', 'no-new-privileges', '--pids-limit', '32',
        '--memory', '1g', '--cpus', '2',
        '--mount', 'type=bind,source=' + str(runtime.resolve()) + ',target=/host-runtime,readonly',
        '--mount', 'type=bind,source=' + str(code_directory.resolve()) + ',target=/audit,readonly',
        IMAGE, 'python', '-I', '-S', '-B', '-c', CODE]


def observe(runtime: Path, directory: Path) -> dict:
    if (directory.exists() or Path('/tmp') not in directory.resolve().parents
            or runtime.is_symlink() or not runtime.is_dir()):
        raise ValueError('fresh /tmp observation and nonsymlink runtime directory required')
    directory.mkdir(parents=True)
    code_directory = directory / 'code'
    code_directory.mkdir()
    files = source_closure()
    for name, content in files.items():
        (code_directory / name).write_bytes(content)
    image = json.loads(subprocess.run(['docker', 'image', 'inspect', IMAGE], capture_output=True,
        text=True, check=True, timeout=10).stdout)[0]
    if image['Os'] != 'linux' or image['Architecture'] != 'amd64':
        raise ValueError('registered audit image platform mismatch')
    image_binding = {'reference': IMAGE, 'image_id': image['Id'], 'repo_digests': image['RepoDigests'],
                     'rootfs_layers': image['RootFS']['Layers'], 'platform': 'linux/amd64'}
    identity = {'schema': 'crane-container-runtime-audit-request/v1-development',
        'scope': 'NON_STUDY_READ_ONLY_EXISTING_RUNTIME_AUDIT', 'runtime_root': str(runtime.resolve()),
        'audit_image': image_binding, 'source_files': {name: hashlib.sha256(value).hexdigest() for name,value in files.items()},
        'command_code_sha256': hashlib.sha256(CODE.encode()).hexdigest(),
        'controller_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'network': 'none', 'rootfs_read_only': True, 'mounts_read_only': True, 'capabilities': ['DAC_READ_SEARCH'],
        'pids_limit': 32, 'memory_bytes': 1024**3, 'cpus': 2, 'controller_timeout_seconds': 900,
        'model_call_attempted': False, 'method_runtime_changed': False}
    identity_sha = canonical_sha256(identity)
    name = 'crane-runtime-audit-' + uuid.uuid4().hex
    _write_once(directory / 'request.intent.json', {'request': identity, 'request_sha256': identity_sha,
        'container_name': name, 'terminal_record_pending': True})
    status, error = 'FAILED_RUNTIME_AUDIT_RETAIN_NO_REPLAY', None
    container_removed = False
    result = None
    try:
        with (directory / 'inventory.json').open('xb') as stdout, (directory / 'stderr.bin').open('xb') as stderr:
            done = subprocess.run(command(runtime, code_directory, name, identity_sha), stdout=stdout,
                                  stderr=stderr, check=False, timeout=900)
        if done.returncode != 0:
            raise RuntimeError('container audit failed; retain stderr and partial inventory without replay')
        record = json.loads((directory / 'inventory.json').read_text())
        validate(record)
        if any((code_directory/name).read_bytes() != content for name,content in files.items()):
            raise ValueError('staged audit source changed')
        result = {**summary(record), 'raw_inventory_sha256': hashlib.sha256((directory/'inventory.json').read_bytes()).hexdigest()}
        status = 'COMPLETE_CONTENT_OBSERVATION_LIVE_RUNTIME_NOT_FROZEN'
    except BaseException as exception:
        error = type(exception).__name__ + ': ' + str(exception)
        raise
    finally:
        # Only remove this invocation's labelled container, never an unknown/pre-existing job.
        inspected = subprocess.run(['docker','container','inspect',name],capture_output=True,text=True,check=False,timeout=10)
        if inspected.returncode == 0:
            live = json.loads(inspected.stdout)[0]
            if live.get('Config',{}).get('Labels',{}).get('crane.runtime-audit') != identity_sha:
                error = 'container label mismatch; unknown container left untouched'
                status = 'FAILED_RUNTIME_AUDIT_RETAIN_NO_REPLAY'
            else:
                removed = subprocess.run(['docker','container','rm','--force',name],capture_output=True,check=False,timeout=10)
                container_removed = removed.returncode == 0
        elif any(message in inspected.stderr for message in ('No such container: ' + name, 'No such object: ' + name)):
            container_removed = True  # Authoritative absence after --rm or failed creation.
        else:
            status = 'FAILED_CLEANUP_UNKNOWN'
            error = 'container inspection failed; absence not verified'
        terminal = {'schema': 'crane-container-runtime-audit-terminal/v1-development',
            'request_sha256': identity_sha, 'status': status, 'error': error, 'result': result,
            'container_removed_or_absent': container_removed, 'full_runtime_frozen': False,
            'method_runtime_changed': False, 'model_call_attempted': False}
        _write_once(directory / 'terminal.json', terminal)
    return {'request': identity, 'terminal': terminal}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-directory', type=Path, required=True)
    args = parser.parse_args()
    record = observe(Path('/usr'),args.raw_directory)
    print(json.dumps(record,indent=2))
    return 0 if record['terminal']['status'] == 'COMPLETE_CONTENT_OBSERVATION_LIVE_RUNTIME_NOT_FROZEN' and record['terminal']['container_removed_or_absent'] else 65


if __name__ == '__main__':
    sys.exit(main())
