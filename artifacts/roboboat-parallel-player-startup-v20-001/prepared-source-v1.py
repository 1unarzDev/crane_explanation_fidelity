"""Two simultaneous rendered startup benchmarks; no ROS/navigation/study N."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
import uuid

from roboboat_owned_player_bundle_v1 import binding, verify_build, prepare as prepare_bundle, verify as verify_bundle
from roboboat_initial_pose_contract_v1 import launch_args, assess as assess_pose, UNITS, OPTION
from audit_roboboat_frame_timing_v1 import audit as audit_frames
from roboboat_hidden_render_v4 import state
from build_roboboat_terminal_batch import save

ROOT = Path(__file__).resolve().parents[1]


def checked(record):
    if binding(record['path']) != record:
        raise ValueError('bound parallel-player input changed')
    return Path(record['path'])


def prepare(root, manifest):
    root, manifest = Path(root).resolve(), Path(manifest).resolve()
    if root.exists():
        raise FileExistsError('fresh fixed parallel-player namespace required')
    value, _ = verify_build(manifest)
    for record in value['source_bindings_current']:
        checked(record)
    sources = [Path(__file__), ROOT/'scripts/run_roboboat_hidden_render_v4.sh']
    sources += [ROOT/'analysis'/name for name in ('roboboat_owned_player_bundle_v1.py',
        'roboboat_initial_pose_contract_v1.py', 'audit_roboboat_frame_timing_v1.py',
        'roboboat_hidden_render_v4.py', 'roboboat_render_fps_lease_v1.py', 'build_roboboat_terminal_batch.py')]
    cases = []
    for index, pose in enumerate(((-2., -5., .25), (-2.5, -6., -.25))):
        cases.append({'id': f'parallel-player-{index+1}', 'worker_id': 20+index,
            'seed': 43220+index, 'initial_pose_request': dict(zip(('x', 'y', 'yaw'), pose)),
            'initial_pose_units': dict(UNITS), 'initial_pose_cli_option': OPTION})
    d = {'schema': 'roboboat-parallel-player-declaration/v20', 'root': str(root),
         'build': binding(manifest), 'sources': [binding(p) for p in sources], 'cases': cases,
         'duration_s': 20, 'warmup_s': 3, 'timeout_s_after_gate': 120,
         'monitor_period_s': .5, 'render_lock': '/tmp/crane-roboboat-population-render.lock',
         'mode': 'two simultaneous train-gpu players; original depth/signatures; ROS disabled',
         'design': 'Both fixed cases once. All results/failures retained. No outcome retries.',
         'scope': 'Window/FPS ownership and rendered aquatic startup benchmark only. No ROS/command/navigation isolation, sensing equivalence or throughput qualification.',
         'independent_n_added': 0, 'confirmation_n': 0, 'replication_n': 0}
    root.mkdir(parents=True)
    save(root/'declaration.json', d)
    return d


def live_snapshot(jobs, now):
    """Read only nonce-owned client fields; never retain unrelated desktop data."""
    clients = state('clients')
    observations = []
    for job in jobs:
        expected = job['bundle']['expected_class']
        matches = [c for c in clients if c.get('class') == expected]
        own = [{k: c.get(k) for k in ('pid', 'class', 'mapped', 'monitor', 'workspace')}
               for c in matches]
        stream = job['output']/'validation.jsonl'
        samples = 0
        if stream.exists():
            # Complete newline records only; the writer may be appending.
            samples = stream.read_bytes().count(b'\n')
        observations.append({'case_id': job['case']['id'], 'wrapper_live': job['process'].poll() is None,
                             'clients': own, 'validation_records': samples})
    return {'elapsed_wall_s': now, 'observations': observations}


def simultaneous_progress(samples):
    """Require distinct live mapped windows and growing validation streams."""
    eligible = []
    for sample in samples:
        observations = sample.get('observations', [])
        if len(observations) != 2:
            continue
        if not all(o.get('wrapper_live') and len(o.get('clients', [])) == 1 and
                   o['clients'][0].get('mapped') is True and o.get('validation_records', 0) > 0
                   for o in observations):
            continue
        clients = [o['clients'][0] for o in observations]
        if (len({c.get('pid') for c in clients}) != 2 or len({c.get('class') for c in clients}) != 2 or
                len({c.get('monitor') for c in clients}) != 2 or
                len({c.get('workspace', {}).get('name') for c in clients}) != 2):
            continue
        eligible.append(sample)
    # Use case identity rather than list position; record counts must grow in
    # both simultaneously observed windows over at least one second.
    for first in eligible:
        for last in eligible:
            if last['elapsed_wall_s'] - first['elapsed_wall_s'] < 1:
                continue
            a = {o['case_id']: o['validation_records'] for o in first['observations']}
            b = {o['case_id']: o['validation_records'] for o in last['observations']}
            if len(a) == 2 and a.keys() == b.keys() and all(b[k] > a[k] for k in a):
                return True
    return False


def assess_worker(case, worker, frames, pose, render, output, code, timeout):
    checks = {
        'player_exit_zero': code == 0 and not timeout,
        'worker_valid': worker.get('valid') is True,
        'worker_identity': worker.get('workerId') == case['worker_id'] and worker.get('randomSeed') == case['seed'],
        'startup_pose': pose.get('initialization_readback_pass') is True,
        'owned_render_complete': render.get('status') == 'COMPLETE_DEVELOPMENT_ONLY' and render.get('placement_verified') is True and
                                 render.get('owned_output_removed') is True and render.get('cleanup_errors') == [],
        'scene_profile': worker.get('scene') == 'Roboboat Course' and worker.get('runtimeProfile') == 'train-gpu',
        'original_signatures': worker.get('imageSignatures') is True,
        'screen_dimensions': (worker.get('screenWidth'), worker.get('screenHeight')) == (640, 360),
        'camera_topology': tuple(worker.get(k) for k in ('enabledCameras', 'enabledSensorCameras', 'enabledSpectatorCameras', 'enabledWaterDriverCameras')) == (1, 1, 0, 0),
        'depth_acquired': worker.get('depthCamera', {}).get('acquisitionCount', 0) > 0,
        'depth_dimensions': (worker.get('depthCamera', {}).get('width'), worker.get('depthCamera', {}).get('height')) == (1280, 720),
        'original_time_scale': worker.get('timeScale') == 1,
        'validation_path': worker.get('validationStream') == str(output/'validation.jsonl'),
        'validation_samples': worker.get('validationSamplesCaptured', 0) >= 2,
        'frame_trace_present': frames.get('retained_frame_rows', 0) > 0,
        'fixed_physics_step': abs(frames.get('metadata', {}).get('fixedDeltaTime', -1)-.02) < 1e-7,
        'catch_up_cap': abs(frames.get('metadata', {}).get('appliedMaximumDeltaTime', -1)-.04) < 1e-6,
        'frame_clock_constant': frames.get('issues') == [],
        'ros_actions_absent': worker.get('acceptedActions') == 0 and worker.get('rejectedActions') == 0,
    }
    for key in ('loggedErrors', 'loggedExceptions', 'invalidWaterSearches', 'staleObservations', 'failedObservations', 'depthBufferValidationMismatches'):
        checks[key+'_zero'] = worker.get(key) == 0
    return checks


def execute(root):
    root = Path(root).resolve()
    declaration = root/'declaration.json'; d = json.loads(declaration.read_text())
    if d['schema'] != 'roboboat-parallel-player-declaration/v20' or d['root'] != str(root) or any(d[k] != 0 for k in ('independent_n_added', 'confirmation_n', 'replication_n')):
        raise ValueError('fixed zero-N parallel-player declaration required')
    for record in d['sources']:
        checked(record)
    manifest = checked(d['build']); value, _ = verify_build(manifest)
    for record in value['source_bindings_current']:
        checked(record)
    save(root/'run-intent.json', {'declaration': binding(declaration), 'independent_n_added': 0})
    jobs = []
    for case in d['cases']:
        output = root/case['id']; output.mkdir()
        bundle = prepare_bundle(manifest, output/'owned-player', uuid.uuid4().hex)
        args = [bundle['executable']['path'], '-screen-fullscreen', '0', '-screen-width', '640',
            '-screen-height', '360', '-logFile', str(output/'player.log'), '--crane-worker',
            '--crane-benchmark', '--crane-scene', 'Roboboat Course', '--crane-profile', 'train-gpu',
            '--crane-disable-ros', '--crane-time-scale', '1', '--crane-duration', str(d['duration_s']),
            '--crane-warmup', str(d['warmup_s']), '--crane-worker-id', str(case['worker_id']),
            '--crane-seed', str(case['seed']), '--crane-maximum-delta-time', '.04',
            '--crane-frame-timing-audit', str(output/'frame-timing.jsonl'),
            '--crane-validation-output', str(output/'validation.jsonl'), '--crane-output', str(output/'worker-result.json')]
        command = [str(ROOT/'scripts/run_roboboat_hidden_render_v4.sh'), '--expected-class',
                   bundle['expected_class'], '--audit-path', str(output/'render-audit.json'), *launch_args(case, args)]
        save(output/'launch-intent.json', {'case': case, 'command': command, 'bundle': bundle, 'independent_n_added': 0})
        log = (output/'process-output.log').open('x')
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
            env={**{k: v for k, v in os.environ.items() if not k.startswith('CRANE_')}, 'CRANE_NOGRAPHICS': '0', 'SDL_VIDEODRIVER': 'x11'})
        jobs.append({'case': case, 'output': output, 'bundle': bundle, 'process': process, 'log': log})
    start = time.monotonic(); samples = []; observer_errors = []
    timed_out = False
    while any(job['process'].poll() is None for job in jobs):
        elapsed = time.monotonic()-start
        if elapsed > d['timeout_s_after_gate']:
            timed_out = True
            for job in jobs:
                if job['process'].poll() is None:
                    job['process'].terminate()
            break
        try:
            samples.append(live_snapshot(jobs, elapsed))
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            observer_errors.append({'elapsed_wall_s': elapsed, 'error_type': type(error).__name__})
        time.sleep(d['monitor_period_s'])
    save(root/'simultaneous-window-observations.json', {'samples': samples, 'observer_errors': observer_errors})
    results = []
    for job in jobs:
        output = job['output']; record = {'case': job['case'], 'timeout_retained': timed_out, 'passed': False, 'independent_n_added': 0}
        try:
            record['return_code'] = job['process'].wait(timeout=30)
            job['log'].close()
            verify_bundle(output/'owned-player')
            worker = json.loads((output/'worker-result.json').read_text())
            render = json.loads((output/'render-audit.json').read_text())
            frames = audit_frames(output/'frame-timing.jsonl'); save(output/'frame-audit.json', frames)
            pose = assess_pose(job['case'], output/'player.log'); save(output/'pose-audit.json', pose)
            record['checks'] = assess_worker(job['case'], worker, frames, pose, render, output, record['return_code'], timed_out)
            record['passed'] = all(record['checks'].values())
            record['worker'] = binding(output/'worker-result.json'); record['render'] = binding(output/'render-audit.json')
            record['render_report'] = render
        except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
            record['error_type'] = type(error).__name__
            record['cleanup_pending'] = job['process'].poll() is None
        save(output/'terminal.json', record); results.append(record)
    overlap = simultaneous_progress(samples)
    reports = [r.get('render_report', {}) for r in results]
    leases = [r.get('fps_lease', {}) for r in reports]; releases = [r.get('fps_lease_release', {}) for r in reports]
    result = {'schema': 'roboboat-parallel-player-result/v20', 'declaration': binding(declaration),
        'results': results, 'simultaneous_windows_and_validation_growth': overlap,
        'two_fps_owners_observed': any(l.get('active_owners') == 2 for l in leases),
        'first_last_release': sorted(r.get('remaining_owners', -1) for r in releases) == [0, 1],
        'observer_errors': observer_errors, 'independent_n_added': 0,
        'ROS_navigation_isolation_qualified': False, 'full_platform_qualified': False}
    result['parallel_startup_benchmark_pass'] = all(r['passed'] for r in results) and overlap and result['two_fps_owners_observed'] and result['first_last_release'] and not observer_errors
    verify_build(manifest)
    save(root/'terminal.json', result)
    print(json.dumps({'parallel_startup_benchmark_pass': result['parallel_startup_benchmark_pass'], 'independent_n_added': 0}), flush=True)
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('phase', choices=('prepare', 'execute'))
    p.add_argument('--root', required=True); p.add_argument('--manifest'); a = p.parse_args()
    if a.phase == 'prepare':
        d = prepare(a.root, a.manifest)
        print(json.dumps({'fixed_cases': len(d['cases']), 'independent_n_added': 0}))
    else:
        root = Path(a.root).resolve(); d = json.loads((root/'declaration.json').read_text())
        print('Waiting for shared render gate; no player started.', flush=True)
        with Path(d['render_lock']).open('a') as lock:
            # SH parent and SH wrappers are compatible. Waiting time is not an
            # operational attempt or a player timeout; EX legacy runs stay safe.
            fcntl.flock(lock, fcntl.LOCK_SH)
            execute(root)
