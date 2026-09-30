#!/usr/bin/env python3
"""Fixed offline probes of bubblewrap's separate structured status descriptor."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox_v2 import Limits
from evidence_calibration_local_tool_sandbox_v6 import ScratchLimits, bounded_namespace_command
from observe_evidence_calibration_cgroup_limits import write_once
from stage_evidence_calibration_workspace import inventory, verify

LIMITS = Limits(3, 2, 256 * 1024**2, 8192)
SCRATCH = ScratchLimits(1024**2, 1024**2)
PROBES = {
    'success': "print('fixed synthetic output')",
    'program_failure': "import sys; print('bwrap: synthetic setup-looking text',file=sys.stderr); sys.exit(7)",
    'setup_failure': "print('PAYLOAD_MUST_NOT_START')",
    'exec_failure': "print('PAYLOAD_MUST_NOT_START')",
    'descriptor_visibility': '''import json,os,pathlib
accessible=[]
for directory in pathlib.Path('/proc').iterdir():
 if not directory.name.isdigit():continue
 try:
  for file in (directory/'fd').iterdir():
   try:
    if 'namespace-status.bin' in str(file.readlink()):accessible.append(directory.name+':'+file.name)
   except OSError:pass
 except OSError:pass
print(json.dumps({'status_descriptor_visible': bool(accessible)}))
''',
}


def parse_status(raw: bytes) -> list[dict]:
    if len(raw) > 8192:
        raise ValueError('operator status capture exceeds fixed probe bound')
    rows = [json.loads(line) for line in raw.splitlines()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError('status record must be an object')
    return rows


def validate(probe: str, row: dict) -> None:
    records = row['status_records']
    if probe in {'setup_failure', 'exec_failure'}:
        if (row['return_code'] == 0 or len(records) != 1
                or type(records[0].get('child-pid')) is not int or records[0]['child-pid'] <= 0
                or 'exit-code' in records[0] or row['stdout']):
            raise ValueError('registered pre-launch failure not observed')
        return
    if (len(records) != 2 or type(records[0].get('child-pid')) is not int
            or records[0]['child-pid'] <= 0 or 'exit-code' not in records[1]):
        raise ValueError('namespace lifecycle records not observed')
    if records[1]['exit-code'] != row['return_code']:
        raise ValueError('recorded payload exit differs from launcher exit')
    if probe == 'program_failure':
        if row['return_code'] != 7:
            raise ValueError('program failure not observed')
    elif probe == 'success':
        if row['return_code'] != 0 or row['stdout'] != 'fixed synthetic output\n':
            raise ValueError('success output changed')
    elif probe == 'descriptor_visibility':
        if row['return_code'] != 0 or json.loads(row['stdout']) != {'status_descriptor_visible': False}:
            raise ValueError('status descriptor accessible from payload namespace')
    else:
        raise ValueError('unknown fixed probe')


def observe(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=False)
    workspace = root / 'workspace'; workspace.mkdir()
    identity = {'inventory': inventory(workspace)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    overall = {'schema': 'crane-namespace-status-observation/v1-development',
               'status': 'TECHNICAL_FAILURE', 'probes': {}, 'model_calls_authorized': False}
    for name, code in PROBES.items():
        directory = root / name; directory.mkdir()
        status_path = directory / 'namespace-status.bin'
        fd = os.open(status_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        argv = bounded_namespace_command(workspace, identity, ['-c', code], LIMITS, SCRATCH)
        argv[1:1] = ['--json-status-fd', str(fd)]
        if name == 'setup_failure':
            index = argv.index('--')
            argv[index:index] = ['--ro-bind', str(directory/'registered-absent-source'), '/absent-probe']
        if name == 'exec_failure':
            argv[argv.index('--') + 1] = str(directory / 'registered-absent-executable')
        write_once(directory/'intent.json', {'command': argv, 'workspace_identity': identity,
                    'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    'status_path': str(status_path), 'operator_probe_only': True})
        row = {'status': 'TECHNICAL_FAILURE'}
        try:
            result = subprocess.run(argv, env={}, stdin=subprocess.DEVNULL, pass_fds=(fd,),
                                    capture_output=True, timeout=3)
            os.fsync(fd)
            raw = status_path.read_bytes()
            row.update(return_code=result.returncode, stdout=result.stdout.decode(), stderr=result.stderr.decode(),
                       status_sha256=hashlib.sha256(raw).hexdigest(), status_records=parse_status(raw))
            verify(workspace, identity)
            validate(name, row)
            row['status'] = 'PASS_FIXED_STATUS_PROBE'
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            row['error'] = str(error)
        finally:
            os.close(fd)
            write_once(directory/'terminal.json', row)
        overall['probes'][name] = row
        if row['status'] != 'PASS_FIXED_STATUS_PROBE':
            break
    if len(overall['probes']) == len(PROBES) and all(
            row['status'] == 'PASS_FIXED_STATUS_PROBE' for row in overall['probes'].values()):
        overall['status'] = 'PASS_FIXED_NAMESPACE_STATUS_SEAM_ONLY'
    write_once(root/'terminal.json', overall)
    return overall


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.output_directory)
    print(json.dumps({'status': result['status'], 'probes': {
        name: {'status': row['status'], 'return_code': row.get('return_code'),
               'status_records': row.get('status_records')} for name,row in result['probes'].items()}}))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__ == '__main__':
    main()
