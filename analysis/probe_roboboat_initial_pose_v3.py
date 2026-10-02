"""Fixed rendered initialization-only probe, never a study recording or N."""
import argparse
import fcntl
import uuid
import json
import math
import os
from pathlib import Path
import subprocess

from roboboat_owned_player_bundle_v1 import binding, verify_build, prepare as prepare_bundle

ROOT = Path(__file__).resolve().parents[1]


def checked(record):
    path = Path(record['path'])
    if binding(path) != record:
        raise ValueError('bound probe input changed')
    return path


def prepare(root, manifest):
    root, manifest = Path(root).resolve(), Path(manifest).resolve()
    if root.exists():
        raise FileExistsError('fresh fixed probe namespace required')
    value, build = verify_build(manifest)
    for source in value['source_bindings_current']:
        checked(source)
    root.mkdir()
    declaration = {'schema': 'roboboat-initial-pose-rendered-probe/v3', 'root': str(root),
        'build': binding(manifest), 'probe_source': binding(__file__),
        'cases': [{'id': 'default-absent', 'pose': None},
                  {'id': 'offset-positive-yaw', 'pose': [-2., -5., .25]},
                  {'id': 'offset-negative-yaw', 'pose': [-2.5, -6., -.25]}],
        'duration_s': 8, 'warmup_s': 2, 'seed': 43104, 'timeout_s': 90,
        'mode': 'rendered train-gpu; ROS transport disabled; startup benchmark only',
        'render_lock': '/tmp/crane-roboboat-population-render.lock',
        'additional_sources': [binding(ROOT / name) for name in ('scripts/run_roboboat_hidden_render_v3.sh',
            'analysis/roboboat_hidden_render_v3.py', 'analysis/roboboat_owned_player_bundle_v1.py')],
        'stopping': 'All three fixed cases once, no retries or outcome-dependent changes.',
        'scope': 'Rendered startup pose/benchmark only; no navigation, ROS transport, full command trace, population reliability or physical equivalence qualification.',
        'independent_n_added': 0, 'confirmation_n': 0, 'replication_n': 0}
    (root / 'declaration.json').write_text(json.dumps(declaration, indent=2) + '\n')
    return declaration


def readback(receipt, pose):
    values = receipt['requestedRosXYAndYaw']
    observed = receipt['observedUnityPosition']
    rotation = receipt['observedUnityRotation']
    theta = math.pi / 2 - pose[2]
    expected = [0., math.sin(theta / 2), 0., math.cos(theta / 2)]
    quaternion = [rotation[k] for k in ('x', 'y', 'z', 'w')]
    return (all(abs(values[k] - v) <= 1e-5 for k, v in zip(('x', 'y', 'z'), pose)) and
            abs(observed['x'] + pose[1]) <= 1e-5 and abs(observed['z'] - pose[0]) <= 1e-5 and
            abs(abs(sum(a * b for a, b in zip(expected, quaternion))) - 1) <= 1e-5 and
            receipt['scene'] == 'Roboboat Course')


def execute(root):
    root = Path(root).resolve(); declaration_path = root / 'declaration.json'
    d = json.loads(declaration_path.read_text()); checked(d['probe_source'])
    for source in d['additional_sources']:
        checked(source)
    manifest = checked(d['build']); value, build = verify_build(manifest)
    if d['root'] != str(root) or any(d[k] != 0 for k in ('independent_n_added', 'confirmation_n', 'replication_n')):
        raise ValueError('fixed zero-N initialization declaration required')
    for source in value['source_bindings_current']:
        checked(source)
    intent = root / 'run-intent.json'
    with intent.open('x') as stream:
        json.dump({'declaration': binding(declaration_path)}, stream)
    results = []
    for case in d['cases']:
        output = root / case['id']; output.mkdir()
        bundle = prepare_bundle(manifest, output / 'owned-player', uuid.uuid4().hex)
        command = [bundle['executable']['path'], '-screen-fullscreen', '0',
            '-screen-width', '640', '-screen-height', '360', '-logFile', str(output / 'player.log'),
            '--crane-worker', '--crane-benchmark', '--crane-scene', 'Roboboat Course',
            '--crane-profile', 'train-gpu', '--crane-disable-ros', '--crane-time-scale', '1',
            '--crane-duration', str(d['duration_s']), '--crane-warmup', str(d['warmup_s']),
            '--crane-seed', str(d['seed']), '--crane-maximum-delta-time', '.04',
            '--crane-frame-timing-audit', str(output / 'frame-timing.jsonl'),
            '--crane-output', str(output / 'worker-result.json')]
        if case['pose'] is not None:
            command.extend(['--crane-roboboat-start-pose', ','.join(str(v) for v in case['pose'])])
        command = [str(ROOT / 'scripts/run_roboboat_hidden_render_v3.sh'), '--expected-class',
                   bundle['expected_class'], '--audit-path', str(output / 'render-audit.json'), *command]
        record = {'case': case, 'command': command, 'owned_player_bundle': bundle, 'status': 'NONSTUDY_PROBE_FAILURE',
                  'independent_n_added': 0, 'study_recording_admitted': False}
        (output / 'launch-intent.json').write_text(json.dumps(record, indent=2) + '\n')
        with (output / 'process-output.log').open('x') as log:
            try:
                process = subprocess.run(command, env={**{k: v for k, v in os.environ.items() if not k.startswith('CRANE_')},
                                              'SDL_VIDEODRIVER': 'x11', 'CRANE_NOGRAPHICS': '0'},
                                         stdout=log, stderr=subprocess.STDOUT, timeout=d['timeout_s'], check=False)
                record['return_code'] = process.returncode
            except subprocess.TimeoutExpired:
                record['timeout_retained'] = True
        receipts = []
        log = output / 'player.log'
        if log.exists():
            for line in log.read_text(errors='replace').splitlines():
                if line.startswith('CRANE_ROBOBOAT_INITIAL_POSE '):
                    receipts.append(json.loads(line.split(' ', 1)[1]))
        record['initialization_receipts'] = receipts
        record['initialization_readback_matches'] = (not receipts if case['pose'] is None else
                                                     bool(receipts) and all(readback(r, case['pose']) for r in receipts))
        worker = output / 'worker-result.json'
        if worker.exists():
            result = json.loads(worker.read_text()); record['worker_result'] = binding(worker)
            record['worker_diagnostics'] = {k: result.get(k) for k in ('valid', 'loggedErrors', 'loggedExceptions', 'invalidWaterSearches')}
        if record.get('return_code') == 0 and record['initialization_readback_matches'] and worker.exists():
            record['status'] = 'INITIALIZATION_READBACK_MATCH_NONSTUDY'
        (output / 'terminal.json').write_text(json.dumps(record, indent=2) + '\n'); results.append(record)
        print(json.dumps({'id': case['id'], 'status': record['status']}), flush=True)
    verify_build(manifest)
    result = {'schema': 'roboboat-initial-pose-rendered-result/v3', 'declaration': binding(declaration_path),
              'results': results, 'independent_n_added': 0, 'confirmation_n': 0,
              'full_platform_qualified': False, 'study_recording_admitted': False}
    (root / 'terminal.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=('prepare', 'execute'))
    p.add_argument('--root', required=True); p.add_argument('--manifest'); a = p.parse_args()
    if a.phase == 'prepare':
        prepare(a.root, a.manifest)
    else:
        root = Path(a.root).resolve(); d = json.loads((root / 'declaration.json').read_text())
        with (root / 'queue-intent.json').open('x') as stream:
            json.dump({'declaration': binding(root / 'declaration.json'), 'status': 'WAITING_FOR_RENDER_LOCK_NO_ATTEMPTS'}, stream)
        print('Waiting for the shared render lock; no probe attempt has started.', flush=True)
        with Path(d['render_lock']).open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            print('Render lock acquired; revalidating fixed inputs before probe execution.', flush=True)
            execute(root)
