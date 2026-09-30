#!/usr/bin/env python3
"""Fixed offline service CPU-accounting probe; no cumulative budget is enforced."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

from evidence_calibration_mcp_stdio_v3 import strict_json
from observe_evidence_calibration_cgroup_limits import write_once

PROBE = r'''
import json, os, resource, subprocess, sys, time
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
relative = Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1]
cgroup = Path('/sys/fs/cgroup') / relative.lstrip('/')
def cpu_stat():
    return {key: int(value) for key, value in
            (line.split() for line in (cgroup / 'cpu.stat').read_text().splitlines())}
before = cpu_stat()
child_code = "import json,resource,time; resource.setrlimit(resource.RLIMIT_CPU,(1,1)); start=time.process_time();\nwhile time.process_time()-start < .15: pass\nprint(json.dumps({'cpu_seconds':time.process_time()-start}))"
children = []
observed = []
try:
    for _ in range(3):
        children.append(subprocess.Popen(['/usr/bin/python3', '-I', '-S', '-B', '-c', child_code],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
    start = time.process_time()
    while time.process_time() - start < .10:
        pass
    parent_work = time.process_time() - start
    for child in children:
        stdout, stderr = child.communicate(timeout=5)
        if child.returncode != 0 or stderr:
            raise RuntimeError('fixed child failed')
        observed.append(json.loads(stdout))
finally:
    for child in children:
        if child.poll() is None:
            child.kill()
        child.wait()
        child.stdout.close()
        child.stderr.close()
after = cpu_stat()
usage = resource.getrusage(resource.RUSAGE_CHILDREN)
row = {'cgroup':relative, 'before':before, 'after':after,
       'cpu_max':(cgroup / 'cpu.max').read_text().strip(),
       'children':observed, 'children_reaped':True, 'parent_work_cpu_seconds':parent_work,
       'children_rusage_cpu_seconds':usage.ru_utime + usage.ru_stime,
       'per_process_rlimit_cpu_seconds':1}
with Path(sys.argv[1]).open('x') as handle:
    json.dump(row,handle,indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
'''

FIELDS = 'LoadState,ActiveState,SubState,Result,ExecMainCode,ExecMainStatus,CPUUsageNSec,ControlGroup,TasksCurrent'


def parse_properties(raw: str) -> dict:
    properties = {}
    for line in raw.splitlines():
        if '=' not in line:
            raise ValueError('malformed service property')
        key, value = line.split('=', 1)
        if key in properties:
            raise ValueError('duplicate service property')
        properties[key] = value
    if set(properties) != set(FIELDS.split(',')):
        raise ValueError('missing or unexpected service properties')
    value = properties['CPUUsageNSec']
    if not value.isascii() or not value.isdecimal() or not 0 <= int(value) < 2**64 - 1:
        raise ValueError('CPU counter absent or unrecognized')
    properties['CPUUsageNSec'] = int(value)
    return properties


def validate_observation(row: dict, snapshots: list[dict]) -> None:
    for name in ('before', 'after'):
        counter = row[name]
        if not {'usage_usec', 'user_usec', 'system_usec'} <= set(counter):
            raise ValueError('missing kernel CPU accounting')
        if any(type(value) is not int or value < 0 for value in counter.values()):
            raise ValueError('invalid kernel CPU counters')
    before, after = row['before']['usage_usec'], row['after']['usage_usec']
    children = row['children']
    if (row['children_reaped'] is not True or len(children) != 3
            or type(row['per_process_rlimit_cpu_seconds']) is not int
            or row['per_process_rlimit_cpu_seconds'] != 1):
        raise ValueError('fixed descendants or process CPU limit differ')
    amounts = [child['cpu_seconds'] for child in children]
    amounts.extend([row['parent_work_cpu_seconds'], row['children_rusage_cpu_seconds']])
    if any(type(value) not in (int, float) or not .0 < value < 1 for value in amounts):
        raise ValueError('invalid fixed process CPU measurement')
    child_sum = sum(child['cpu_seconds'] for child in children)
    if (any(not .15 <= child['cpu_seconds'] < .5 for child in children)
            or not .10 <= row['parent_work_cpu_seconds'] < .5
            or row['children_rusage_cpu_seconds'] + .02 < child_sum
            or (after - before) / 1e6 + .02 < child_sum + row['parent_work_cpu_seconds']):
        raise ValueError('exited-descendant CPU consumption not accounted')
    if row['cpu_max'] != '100000 100000':
        raise ValueError('fixed one-core CPU rate differs')
    if len(snapshots) < 3:
        raise ValueError('missing retained service accounting samples')
    counters = [sample['CPUUsageNSec'] for sample in snapshots]
    if (any(type(value) is not int or value < 0 for value in counters)
            or any(a > b for a, b in zip(counters, counters[1:]))):
        raise ValueError('service CPU accounting is invalid or nonmonotonic')
    final = snapshots[-3:]
    if (len(set(sample['CPUUsageNSec'] for sample in final)) != 1
            or counters[-1] < after * 1000):
        raise ValueError('post-exit CPU accounting lost or unstable')
    for sample in final:
        if (sample['LoadState'] != 'loaded' or sample['ActiveState'] != 'active'
                or sample['SubState'] != 'exited' or sample['Result'] != 'success'
                or sample['ExecMainCode'] != '1' or sample['ExecMainStatus'] != '0'
                or sample['ControlGroup'] != row['cgroup']
                or sample['TasksCurrent'] != '0'):
            raise ValueError('retained accounting lacks successful empty process tree')


def environment() -> dict:
    return {key: os.environ[key] for key in ('PATH', 'XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS')
            if key in os.environ}


def control(env: dict, unit: str, *arguments: str) -> dict:
    completed = subprocess.run(['/usr/bin/systemctl', '--user', *arguments, unit], env=env,
                               stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=3)
    return {'return_code': completed.returncode, 'stdout': completed.stdout, 'stderr': completed.stderr}


def observe(directory: Path) -> dict:
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    unit = 'crane-tree-cpu-probe-' + uuid.uuid4().hex
    argv = ['/usr/bin/systemd-run', '--user', '--quiet', '--no-block', '--expand-environment=no',
            '--unit=' + unit, '-p', 'RemainAfterExit=yes',
            '-p', 'CPUQuota=100%', '-p', 'MemoryMax=67108864', '-p', 'MemorySwapMax=0',
            '-p', 'TasksMax=16', '-p', 'RuntimeMaxSec=8s', '-p', 'TimeoutStopSec=1s',
            '-p', 'KillMode=control-group', '/usr/bin/python3', '-I', '-S', '-B', '-c', PROBE,
            str(directory / 'probe.json')]
    write_once(directory / 'intent.json', {'schema': 'crane-tree-cpu-accounting-intent/v2-development',
        'unit': unit, 'command': argv, 'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'probe_sha256': hashlib.sha256(PROBE.encode()).hexdigest(), 'model_calls_authorized': False,
        'cumulative_budget_enforced': False, 'scientific_harness_adopted': False})
    terminal = {'schema': 'crane-tree-cpu-accounting-terminal/v2-development', 'unit': unit,
                'status': 'TECHNICAL_FAILURE', 'observation': None, 'samples': []}
    env = environment()
    try:
        launched = subprocess.run(argv, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                                  text=True, timeout=3)
        terminal['launch'] = {'return_code': launched.returncode, 'stdout': launched.stdout, 'stderr': launched.stderr}
        if launched.returncode:
            raise ValueError('fixed service launch failed; no retry')
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            raw = control(env, unit, 'show', '--property=' + FIELDS)
            terminal.setdefault('raw_samples', []).append(raw)
            if raw['return_code']:
                raise ValueError('service counter query failed; no restart')
            sample = parse_properties(raw['stdout'])
            terminal['samples'].append(sample)
            if sample['SubState'] in {'failed', 'dead'}:
                raise ValueError('fixed service exited unsuccessfully')
            if len(terminal['samples']) >= 3 and all(s['SubState'] == 'exited' for s in terminal['samples'][-3:]):
                row = strict_json((directory / 'probe.json').read_bytes())
                terminal['observation'] = row
                validate_observation(row, terminal['samples'])
                terminal['status'] = 'PASS_EXITED_DESCENDANT_CPU_ACCOUNTING_ONLY'
                break
            time.sleep(.05)
        else:
            raise ValueError('accounting observation timeout; no retry')
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        terminal['error'] = str(error)
    finally:
        terminal['cleanup'] = {'actions': []}
        try:
            for verb in ('stop', 'reset-failed'):
                terminal['cleanup']['actions'].append({'verb': verb, **control(env, unit, verb)})
            state = control(env, unit, 'show', '--property=LoadState', '--value')
            terminal['cleanup']['final_state'] = state
            if state['return_code'] != 0 or state['stdout'].strip() != 'not-found':
                terminal['status'] = 'TECHNICAL_FAILURE'
                terminal['cleanup']['error'] = 'exact service cleanup unverified'
        except (OSError, subprocess.TimeoutExpired) as error:
            terminal['status'] = 'TECHNICAL_FAILURE'
            terminal['cleanup']['error'] = str(error)
        write_once(directory / 'terminal.json', terminal)
    return terminal


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    args = parser.parse_args()
    terminal = observe(args.output_directory)
    print(json.dumps({'status': terminal['status'], 'observation': terminal['observation'],
                      'error': terminal.get('error'), 'cleanup': terminal['cleanup']}))
    raise SystemExit(0 if terminal['status'].startswith('PASS') else 1)


if __name__ == '__main__':
    main()
