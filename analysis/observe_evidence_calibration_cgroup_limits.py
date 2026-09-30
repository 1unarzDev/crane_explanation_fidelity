#!/usr/bin/env python3
"""One-shot non-study observation of user-service process-tree resource controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

PROBE = r'''
import json, subprocess
from pathlib import Path
path = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
files = ['memory.max', 'memory.swap.max', 'pids.max', 'cpu.max']
settings = {name: (path / name).read_text().strip() for name in files}
children = []
blocked = False
try:
    for _ in range(12):
        try:
            children.append(subprocess.Popen(['/usr/bin/sleep', '10']))
        except BlockingIOError:
            blocked = True
            break
finally:
    for child in children:
        child.kill()
    for child in children:
        child.wait()
print(json.dumps({'kernel_settings': settings, 'children_started': len(children),
                  'task_creation_blocked': blocked, 'children_reaped': True}))
'''


def validate_observation(row: dict) -> None:
    settings = row['kernel_settings']
    if settings['memory.max'] != '67108864' or settings['memory.swap.max'] != '0' or settings['pids.max'] != '8':
        raise ValueError('kernel resource settings differ from probe request')
    quota, period = settings['cpu.max'].split()
    if quota == 'max' or int(quota) != int(period):
        raise ValueError('CPU quota is not the requested one-core rate')
    if (row['task_creation_blocked'] is not True or row['children_reaped'] is not True
            or type(row['children_started']) is not int or not 1 <= row['children_started'] < 8):
        raise ValueError('task-limit enforcement or cleanup not observed')


def write_once(path: Path, value: dict) -> None:
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def observe(directory: Path) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    unit = 'crane-cgroup-probe-' + uuid.uuid4().hex
    command = ['/usr/bin/systemd-run', '--user', '--wait', '--pipe', '--collect',
               '--unit=' + unit, '-p', 'MemoryMax=67108864', '-p', 'MemorySwapMax=0',
               '-p', 'TasksMax=8', '-p', 'CPUQuota=100%', '/usr/bin/python', '-c', PROBE]
    intent = {'schema': 'crane-cgroup-observation-intent/v1-development',
              'unit': unit, 'command': command,
              'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'model_calls_authorized': False, 'scientific_harness_adopted': False}
    write_once(directory / 'intent.json', intent)
    terminal = {'schema': 'crane-cgroup-observation-terminal/v1-development',
                'unit': unit, 'status': 'TECHNICAL_FAILURE', 'observation': None}
    try:
        environment = {key: os.environ[key] for key in
                       ('PATH', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS') if key in os.environ}
        completed = subprocess.run(command, env=environment, capture_output=True, text=True, timeout=30)
        terminal.update(return_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr)
        if completed.returncode:
            raise ValueError('resource probe service failed')
        row = json.loads(completed.stdout)
        validate_observation(row)
        # --collect discards the transient unit after its terminal result.
        state = subprocess.run(['/usr/bin/systemctl', '--user', 'show', unit, '--property=LoadState', '--value'],
                               env=environment, capture_output=True, text=True, timeout=5)
        terminal['post_probe_unit_check'] = {'return_code': state.returncode,
                                            'stdout': state.stdout, 'stderr': state.stderr}
        if state.stdout.strip() != 'not-found':
            raise ValueError('transient unit cleanup not observed')
        terminal.update(status='PASS_BOUNDED_CGROUP_AVAILABILITY_ONLY', observation=row)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        # No relaunch on failure or unknown intent. Clean up this exact operator probe only.
        terminal['error'] = str(error)
        cleanup = subprocess.run(['/usr/bin/systemctl', '--user', 'stop', unit],
                                 capture_output=True, text=True, timeout=5)
        terminal['failure_cleanup'] = {'return_code': cleanup.returncode,
                                      'stdout': cleanup.stdout, 'stderr': cleanup.stderr}
    finally:
        write_once(directory / 'terminal.json', terminal)
    return terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    result = observe(args.output_directory)
    print(json.dumps({'status': result['status'], 'observation': result['observation']}))
    raise SystemExit(0 if result['status'].startswith('PASS') else 1)


if __name__ == '__main__':
    main()
