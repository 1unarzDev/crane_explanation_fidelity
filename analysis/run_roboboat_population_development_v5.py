#!/usr/bin/env python3
"""Development v5 optional-image-signature instrumentation probe. Immutable attempts; unchanged strict gates.

Single compositor worker until multi-window routing is independently qualified.
Other work may run concurrently on isolated ROS domains/ports and method workers.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from build_roboboat_terminal_batch import save
from generate_roboboat_population_v1 import ROOT, digest
from export_roboboat_population_v2 import project, publish_terminal

PLAYER = Path('/home/lunarz/worktrees/roboboat-docking/packages/crane_ml/Builds/CRANE-RoboBoat-Bow/CRANE.x86_64')
PLAYER_SHA256 = 'a7ad5b156bd9a1232544ff6fc12e5f863d8f1f2348c5b141f5c3d4230e5be292'
PROBE_VERSION = 'roboboat-image-signature-instrumentation-probe/v5'
SOURCE_ROOT = Path(__file__).resolve().parents[1]
INSTRUMENTATION_SOURCES = tuple(SOURCE_ROOT / path for path in (
    'packages/crane_ml/Assets/Scripts/Utils/Performance/CraneProfiler.cs',
    'packages/crane_ml/Assets/Scripts/Performance/CraneBenchmarkRunner.cs',
    'packages/crane_ml/Assets/Scripts/Sensors/Vision/RosDepthCameraAsync.cs'))


def verify_player():
    if digest(PLAYER) != PLAYER_SHA256:
        raise ValueError('immutable physical player hash mismatch')


def default_affinity():
    cpus = sorted(os.sched_getaffinity(0))
    if cpus != list(range(os.cpu_count())):
        raise ValueError('v5 requires unrestricted default host CPU affinity')
    return cpus


def bound(binding):
    path = ROOT / binding['path']
    if digest(path) != binding['sha256']: raise ValueError('bound input changed: ' + str(path))
    return path


def technical_checks(summary, worker, fixture):
    """Inherited strict checks, with task outcome excluded from admission by design."""
    transport = summary['transport']
    timing = worker.get('actionTiming', {})
    accepted = worker.get('acceptedActions')
    checks = {'worker_valid': worker.get('valid') is True,
              'action_observer_complete': fixture.get('status') in ('succeeded', 'aborted', 'canceled', 'timeout'),
              'rejected_actions_zero': worker.get('rejectedActions') == 0,
              'stale_actions_zero': worker.get('staleActions') == 0,
              'cross_episode_actions_zero': worker.get('crossEpisodeActions') == 0,
              'runtime_errors_zero': worker.get('loggedErrors') == 0,
              'runtime_exceptions_zero': worker.get('loggedExceptions') == 0,
              'invalid_water_searches_zero': worker.get('invalidWaterSearches') == 0,
              'stale_observations_zero': worker.get('staleObservations') == 0,
              'failed_observations_zero': worker.get('failedObservations') == 0,
              'duplicate_registrations_zero': transport['duplicateNodeRegistrations'] == 0,
              'endpoint_errors_zero': transport['endpointErrors'] == 0,
              'single_connection': transport['maximumConcurrentUnityConnections'] <= 1,
              'connection_closed': transport['activeConnectionsAtShutdown'] == 0,
              'accepted_action_count_matches': timing.get('acceptedActions') == accepted,
              'known_source_count_matches': timing.get('knownSourceActions') == accepted,
              'bounded_source_lag': 0 <= timing.get('maximumSourceToApplicationTicks', -1) <= 10,
              'bounded_receive_lag': 0 <= timing.get('maximumReceiveToApplicationTicks', -1) <= 10,
              'measured_trajectory': len(fixture.get('trajectory', [])) > 0}
    return checks


def capture(row, registry, registry_path, output, domain, port):
    out = output / row['id']
    record = out / 'capture-attempt.json'
    if record.exists():
        previous = json.loads(record.read_text())
        if previous['registry_sha256'] != digest(registry_path): raise ValueError('registry differs')
        if previous['status'] in ('VALID_DEVELOPMENT', 'TECHNICAL_FAILURE'): return previous
        raise RuntimeError('unresolved attempt retained; inspect before successor, never reissue')
    out.mkdir(parents=True, exist_ok=False)
    verify_player()
    affinity = default_affinity()
    config = bound(registry['nav2_configuration'])
    if 'path_file' in row: bound(row['path_file'])
    bound(row['task_contract'])
    env = {**{k:v for k,v in os.environ.items() if not k.startswith('CRANE_')}, 'CRANE_RUN_ID': row['id'], 'CRANE_ROS_PORT': str(port), 'CRANE_ROS_DOMAIN_ID': str(domain),
           'CRANE_RESULT_ROOT': str(out), 'CRANE_PLAYER': str(PLAYER),
           'CRANE_ASTRO_DOCK': '/home/lunarz/crane_explain/packages/astro_dock',
           'CRANE_NOGRAPHICS': '0', 'CRANE_DURATION': '340', 'CRANE_WARMUP': '3',
           'CRANE_SCREEN_WIDTH': '640', 'CRANE_SCREEN_HEIGHT': '360', 'CRANE_TIME_SCALE': '1',
           'CRANE_NAV2_ACTION_DURATION': '310', 'CRANE_NAV2_POST_RESULT_DURATION': '8',
           'CRANE_NAV2_PARAMS': str(config), 'CRANE_CAPTURE_RUNTIME_PARAMETERS': '1',
           'CRANE_NAV2_ACTION_MODE': row['action_mode'], 'CRANE_NAV2_PROFILE': 'train-gpu',
           'CRANE_NAV2_CONTROLLER_EXTRA_ARGS': f"-p goal_checker.xy_goal_tolerance:={row['internal_xy_tolerance_m']}",
           'CRANE_NAV2_GOAL_X': str(row['goal']['x']), 'CRANE_NAV2_GOAL_Y': str(row['goal']['y']),
           'CRANE_NAV2_GOAL_YAW': str(row['goal']['yaw']), 'CRANE_DOCKING_EVALUATOR': '1', 'CRANE_SEED_BASE': str(row['seed'])}
    # Prevent unrelated inherited per-run overrides from altering a declared launch.
    for key in ('CRANE_NAV2_PATH_FILE', 'CRANE_NAV2_UNITY_EXTRA_ARGS', 'CRANE_NAV2_BT_XML', 'CRANE_DISABLE_DEPTH', 'CRANE_DISABLE_RGB'):
        env.pop(key, None)
    env['CRANE_NAV2_UNITY_EXTRA_ARGS'] = '--crane-no-signatures'
    if 'path_file' in row: env['CRANE_NAV2_PATH_FILE'] = str(ROOT / row['path_file']['path'])
    command = [str(ROOT/'scripts/run_roboboat_hidden_render.sh'), str(ROOT/'packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh')]
    ledger = {'status': 'RUNNING', 'row': row, 'registry_sha256': digest(registry_path), 'started_unix': time.time(),
              'command': command, 'launch_values': {k: v for k, v in env.items() if k.startswith('CRANE_')},
              'player_sha256': digest(PLAYER), 'physical_player': {'path': str(PLAYER), 'sha256': PLAYER_SHA256},
              'collector_sha256': digest(Path(__file__)), 'probe_version': PROBE_VERSION,
              'image_signatures': False, 'default_cpu_affinity': affinity,
              'inspected_instrumentation_sources': [{'path': str(path), 'sha256': digest(path)} for path in INSTRUMENTATION_SOURCES],
              'intervention': 'Only optional full-byte image signature hashing disabled; counts and payload publication remain active', 'technical_validity_definition': 'no desired outcome check; strict runtime/sensor/transport gates',
              'launcher_sha256': digest(Path(command[1])), 'wrapper_sha256': digest(Path(command[0])), 'quality_retries': 0}
    save(out / 'capture-intent.json', ledger)
    # Mutable operational terminal record is atomic; original intent never changes.
    with (out/'launcher.log').open('x') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try: code = process.wait(timeout=480)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=30)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait()
            code = 124
    ledger.update(return_code=code, finished_unix=time.time())
    try:
        summary = json.loads((out/'navigation-reset-summary.json').read_text())
        worker = json.loads((out/'worker-0/result.json').read_text())
        fixture = json.loads((out/'fixture-summary.json').read_text())
        checks = technical_checks(summary, worker, fixture)
        checks.update(operational_probe_checks(worker))
        # A nonzero launcher is accepted only when its sole failure was inherited
        # expected-status validation. Timeout/early death can never be reclassified.
        checks['launcher_completed'] = code in (0, 1)
        if code == 1:
            checks['status_gate_only_failure'] = fixture['status'] != summary['expectedNavigationStatus']
        ledger['checks'] = checks
        ledger['observed_navigation_status'] = fixture['status']
        ledger['real_time_factor'] = worker.get('realTimeFactor')
        if not all(checks.values()): raise ValueError('failed checks: ' + ', '.join(k for k,v in checks.items() if not v))
        ledger['level_outcomes'] = project(row, out, out/'exports-v2', config)
        ledger['status'] = 'VALID_DEVELOPMENT'
    except (OSError, ValueError, KeyError, TypeError) as error:
        ledger.update(status='TECHNICAL_FAILURE', error=str(error))
    save(record, ledger)
    if ledger['status'] == 'VALID_DEVELOPMENT':
        # Supplemental export provenance binds original intent and new namespace.
        ledger = publish_terminal(row, registry_path, out, config)
    print(json.dumps({'id': row['id'], 'status': ledger['status'], 'observed': ledger.get('observed_navigation_status'), 'error': ledger.get('error')}), flush=True)
    return ledger



def operational_probe_checks(worker):
    return {
        'image_signatures_disabled': worker.get('imageSignatures') is False,
        'screen_640x360': (worker.get('screenWidth'), worker.get('screenHeight')) == (640, 360),
        'depth_resolution_unchanged': (worker.get('depthCamera', {}).get('width'), worker.get('depthCamera', {}).get('height')) == (1280, 720),
        'depth_acquired': worker.get('depthCamera', {}).get('acquisitionCount', 0) > 0,
        'camera_topology_unchanged': tuple(worker.get(k) for k in ('enabledCameras', 'enabledSensorCameras', 'enabledSpectatorCameras', 'enabledWaterDriverCameras')) == (1, 1, 0, 0),
        'time_scale_unchanged': worker.get('timeScale') == 1,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry', required=True, type=Path)
    p.add_argument('--output-root', required=True, type=Path)
    p.add_argument('--max-new-attempts', type=int, default=4)
    p.add_argument('--domain', type=int, default=191)
    p.add_argument('--port', type=int, default=11481)
    a = p.parse_args()
    if a.max_new_attempts < 1 or not 0 <= a.domain <= 232 or not 1024 <= a.port <= 65535:
        raise ValueError('invalid probe resources/count')
    registry = json.loads(a.registry.read_text())
    if registry['status'] != 'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION':
        raise ValueError('development registry required')
    if len({row['id'] for row in registry['rows']}) != len(registry['rows']):
        raise ValueError('duplicate registry identities')
    output = a.output_root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with Path('/tmp/crane-roboboat-population-render.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_player()
        affinity = default_affinity()
        rows = [row for row in registry['rows'] if not (output/row['id']).exists()][:a.max_new_attempts]
        if not rows:
            print(json.dumps({'status': 'NO_UNTOUCHED_ROWS', 'probe_version': PROBE_VERSION}))
            return
        intent = output/'image-signature-probes-v5'/f'probe-{rows[0]["id"] if rows else "no-new-rows"}.json'
        intent.parent.mkdir(parents=True, exist_ok=True)
        with intent.open('x') as stream:
            json.dump({'schema':PROBE_VERSION, 'status':'DEVELOPMENT_ONLY',
                'registry_sha256':digest(a.registry), 'collector_sha256':digest(Path(__file__)),
                'rows':[row['id'] for row in rows], 'screen':[640,360], 'time_scale':1,
                'default_cpu_affinity': affinity, 'image_signatures': False,
                'physical_player': {'path':str(PLAYER), 'sha256':PLAYER_SHA256},
                'inspected_instrumentation_sources': [{'path':str(path),'sha256':digest(path)} for path in INSTRUMENTATION_SOURCES],
                'unity_extra_args':['--crane-no-signatures'], 'pilot_max_attempts':a.max_new_attempts,
                'change':'Only optional full-byte image hashing disabled; original direct player/default CPU affinity, sensor dimensions/cadence/physics/task/strict gates preserved. Hypothesis unproven.',
                'stop_rule':'Stop after two consecutive fresh technical failures. No old failures counted as new probes.',
                'quality_retries':0,'confirmation_n':0,'alpha_consumed':0},stream,indent=2)
        results=[]
        for row in rows:
            results.append(capture(row,registry,a.registry.resolve(),output,a.domain,a.port))
            if len(results)>=2 and all(r['status']=='TECHNICAL_FAILURE' for r in results[-2:]):
                break
        save(intent.with_name(intent.stem+'-terminal.json'),{'status':'DEVELOPMENT_PROBE_FINISHED',
            'intent_sha256':digest(intent), 'results':results, 'confirmation_n':0, 'replication_n':0,
            'physical_attempts':len(results), 'valid_recordings':sum(r['status']=='VALID_DEVELOPMENT' for r in results),
            'remaining_rows':[row['id'] for row in rows[len(results):]], 'study_ceiling':None})


if __name__ == '__main__': main()
