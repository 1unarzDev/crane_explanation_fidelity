#!/usr/bin/env python3
"""Fixed offline resource probes around the unchanged v2 namespace command."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

from evidence_calibration_io import canonical_sha256
from evidence_calibration_local_tool_sandbox_v2 import Limits, command
from observe_evidence_calibration_cgroup_limits import write_once
from stage_evidence_calibration_workspace import inventory, verify

LIMITS = Limits(10, 5, 256 * 1024**2, 8192)
PROBES = {
    'isolation': '''import json, os
from pathlib import Path
checks = {'visible_read': json.loads(Path('visible.json').read_text()) == {'synthetic_visible': True},
          'home_absent': not Path('/home').exists(), 'sysfs_absent': not Path('/sys').exists(),
          'environment_cleared': set(os.environ) <= {'PATH', 'LC_ALL'},
          'arithmetic': sum(range(11)) == 55}
try:
    Path('visible.json').write_text('changed')
    checks['visible_write_denied'] = False
except OSError:
    checks['visible_write_denied'] = True
print(json.dumps(checks))
''',
    'task_limit': '''import json, subprocess
children = []
blocked = False
try:
    for _ in range(24):
        try:
            children.append(subprocess.Popen(['/usr/bin/sleep', '10']))
        except BlockingIOError:
            blocked = True
            break
finally:
    for child in children: child.kill()
    for child in children: child.wait()
print(json.dumps({'children_started': len(children), 'task_creation_blocked': blocked, 'children_reaped': True}))
''',
    'memory_pressure': "x = bytearray(128 * 1024**2); print('MEMORY_LIMIT_NOT_ENFORCED')",
    'service_wall': "import time; time.sleep(8); print('WALL_LIMIT_NOT_ENFORCED')",
}


def service_command(workspace: Path, identity: dict, probe: str, unit: str) -> list[str]:
    if probe not in PROBES:
        raise ValueError('only registered fixed operator probes permitted')
    return ['/usr/bin/systemd-run', '--user', '--wait', '--pipe', '--unit=' + unit,
            '-p', 'MemoryMax=67108864', '-p', 'MemorySwapMax=0', '-p', 'TasksMax=16',
            '-p', 'CPUQuota=100%', '-p', 'OOMPolicy=kill',
            '-p', 'RuntimeMaxSec=2s', '-p', 'TimeoutStopSec=1s', '-p', 'KillMode=control-group',
            *command(workspace, identity, ['-c', PROBES[probe]], LIMITS)]


def properties(text: str) -> dict:
    return dict(line.split('=', 1) for line in text.splitlines() if '=' in line)


def validate_result(probe: str, row: dict) -> None:
    if row['cleanup']['load_state'] != 'not-found':
        raise ValueError('service cleanup not established')
    if probe in {'isolation', 'task_limit'}:
        if row['return_code'] != 0:
            raise ValueError('positive namespace probe failed')
        output = json.loads(row['stdout'])
        if probe == 'isolation' and (len(output) != 6 or any(value is not True for value in output.values())):
            raise ValueError('namespace behavior changed')
        if probe == 'task_limit' and (output['task_creation_blocked'] is not True
                or output['children_reaped'] is not True or type(output['children_started']) is not int
                or not 1 <= output['children_started'] < 16):
            raise ValueError('descendant task limit not established')
    elif probe in {'memory_pressure', 'service_wall'}:
        expected = 'oom-kill' if probe == 'memory_pressure' else 'timeout'
        if row['return_code'] == 0 or row['unit_properties'].get('Result') != expected:
            raise ValueError('registered resource failure not established')
        if row['stdout']:
            raise ValueError('resource failure emitted unexpected success output')
    else:
        raise ValueError('unknown probe')


def observe(directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    workspace = directory / 'workspace'
    workspace.mkdir()
    (workspace / 'visible.json').write_text('{"synthetic_visible":true}')
    identity = {'inventory': inventory(workspace)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    environment = {key: os.environ[key] for key in
                   ('PATH', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS') if key in os.environ}
    overall = {'schema': 'crane-cgroup-sandbox-observation/v1-development',
               'status': 'TECHNICAL_FAILURE', 'probes': {}, 'model_calls_authorized': False,
               'scientific_harness_adopted': False}
    for probe in PROBES:
        unit = 'crane-cgroup-sandbox-' + uuid.uuid4().hex
        argv = service_command(workspace, identity, probe, unit)
        write_once(directory / (probe + '.intent.json'), {
            'unit': unit, 'command': argv, 'workspace_identity': identity,
            'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        row = {'unit': unit, 'status': 'TECHNICAL_FAILURE'}
        try:
            completed = subprocess.run(argv, env=environment, capture_output=True, text=True, timeout=12)
            row.update(return_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
            state = subprocess.run(['/usr/bin/systemctl', '--user', 'show', unit,
                    '--property=Result,ActiveState,LoadState'], env=environment,
                    capture_output=True, text=True, timeout=5)
            row['unit_properties'] = properties(state.stdout)
            row['unit_check'] = {'return_code': state.returncode, 'stdout': state.stdout, 'stderr': state.stderr}
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            row['error'] = str(error)
        finally:
            # Only this fresh operator service: no study request or other unit is affected.
            cleanup = []
            for verb in ('stop', 'reset-failed'):
                result = subprocess.run(['/usr/bin/systemctl', '--user', verb, unit], env=environment,
                                        capture_output=True, text=True, timeout=5)
                cleanup.append({'verb': verb, 'return_code': result.returncode,
                                'stdout': result.stdout, 'stderr': result.stderr})
            state = subprocess.run(['/usr/bin/systemctl', '--user', 'show', unit, '--property=LoadState', '--value'],
                                   env=environment, capture_output=True, text=True, timeout=5)
            row['cleanup'] = {'actions': cleanup, 'load_state': state.stdout.strip(),
                              'return_code': state.returncode, 'stderr': state.stderr}
            try:
                verify(workspace, identity)
                validate_result(probe, row)
                row['status'] = 'PASS_FIXED_OPERATOR_PROBE'
            except (ValueError, KeyError) as error:
                row['error'] = str(error)
            write_once(directory / (probe + '.terminal.json'), row)
        overall['probes'][probe] = row
        if row['status'] != 'PASS_FIXED_OPERATOR_PROBE':
            break
    if len(overall['probes']) == len(PROBES) and all(
            row['status'] == 'PASS_FIXED_OPERATOR_PROBE' for row in overall['probes'].values()):
        overall['status'] = 'PASS_FIXED_NAMESPACE_RESOURCE_PROBES_ONLY'
    write_once(directory / 'terminal.json', overall)
    return overall


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.output_directory)
    print(json.dumps({'status': result['status'],
                      'probes': {name: row['status'] for name, row in result['probes'].items()}}))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__ == '__main__':
    main()
