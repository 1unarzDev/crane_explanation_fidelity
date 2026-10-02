#!/usr/bin/env python3
"""Controlled tracing on/off reliability assay; never new independent N.

Additive collector copy preserves v8 and the bound v9 player. Instrumentation
is the sole requested toggle; fixed geometry/seed/task/controller/sensing/frame
audit remain shared. Repeated operational namespaces are not fresh configurations.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import uuid
from roboboat_owned_player_bundle_v1 import verify_build, prepare as prepare_bundle, verify as verify_bundle
from audit_roboboat_action_trace_v1 import read as audit_actions

from build_roboboat_terminal_batch import save
from generate_roboboat_population_v1 import ROOT, digest

PLAYER = Path('/home/lunarz/worktrees/roboboat-action-timing-v9/crane_ml/Builds/CRANE-Worker/CRANE.x86_64')
BUILD_IDENTITY = ROOT/'artifacts/roboboat-action-timing-v9/full-build-root-v1.json'
from audit_roboboat_frame_timing_v1 import audit as audit_frames
PLAYER_SHA256 = 'a7ad5b156bd9a1232544ff6fc12e5f863d8f1f2348c5b141f5c3d4230e5be292'
PROBE_VERSION = 'roboboat-tracing-overhead/v1-reliability-only'
SOURCE_ROOT = Path(__file__).resolve().parents[1]
INSTRUMENTATION_PROJECT = Path('/home/lunarz/worktrees/roboboat-action-timing-v9/crane_ml')
INSTRUMENTATION_SOURCES = tuple(INSTRUMENTATION_PROJECT / path for path in (
    'Assets/Scripts/Utils/Performance/CraneActionTimingAudit.cs',
    'Assets/Scripts/Utils/Performance/CraneActionGate.cs',
    'Assets/Scripts/Controllers/ROSOmniXCommand.cs',
    'Assets/Scripts/Performance/CraneBenchmarkRunner.cs'))


def verify_player():
    value, root = verify_build(BUILD_IDENTITY)
    if root/'CRANE.x86_64' != PLAYER.resolve(): raise ValueError('bound build root mismatch')
    for item in value['source_bindings_current']:
        if digest(Path(item['path'])) != item['sha256']: raise ValueError('bound source changed')
    return value


def default_affinity():
    cpus = sorted(os.sched_getaffinity(0))
    if cpus != list(range(os.cpu_count())):
        raise ValueError('trace pilot requires unrestricted default host CPU affinity')
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


def capture(row, registry, registry_path, output, domain, port, maximum_delta_time=None, trace_enabled=True):
    out = output / row['id']
    record = out / 'capture-attempt.json'
    if record.exists():
        previous = json.loads(record.read_text())
        if previous['registry_sha256'] != digest(registry_path): raise ValueError('registry differs')
        if previous['status'] in ('OVERHEAD_CAPTURE_COMPLETE', 'TECHNICAL_FAILURE'): return previous
        raise RuntimeError('unresolved attempt retained; inspect before successor, never reissue')
    out.mkdir(parents=True, exist_ok=False)
    verify_player()
    bundle = prepare_bundle(BUILD_IDENTITY, out/'owned-player', uuid.uuid4().hex)
    verify_bundle(out/'owned-player')
    affinity = default_affinity()
    config = bound(registry['nav2_configuration'])
    if 'path_file' in row: bound(row['path_file'])
    bound(row['task_contract'])
    env = {**{k:v for k,v in os.environ.items() if not k.startswith('CRANE_')}, 'CRANE_RUN_ID': row['id'], 'CRANE_ROS_PORT': str(port), 'CRANE_ROS_DOMAIN_ID': str(domain),
           'SDL_VIDEODRIVER': 'x11', 'CRANE_RESULT_ROOT': str(out), 'CRANE_PLAYER': bundle['executable']['path'],
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
    if any(c.isspace() for c in str(out)): raise ValueError('inherited launcher requires whitespace-free audit path')
    env['CRANE_NAV2_UNITY_EXTRA_ARGS'] = '--crane-frame-timing-audit '+str(out/'frame-timing.jsonl')
    if trace_enabled: env['CRANE_NAV2_UNITY_EXTRA_ARGS'] += ' --crane-action-timing-audit '+str(out/'action-timing.jsonl')
    if maximum_delta_time is not None: env['CRANE_NAV2_UNITY_EXTRA_ARGS'] += ' --crane-maximum-delta-time '+str(maximum_delta_time)
    if 'path_file' in row: env['CRANE_NAV2_PATH_FILE'] = str(ROOT / row['path_file']['path'])
    command = [str(ROOT/'scripts/run_roboboat_hidden_render_v3.sh'), '--expected-class', bundle['expected_class'], '--audit-path', str(out/'render-audit.json'), str(ROOT/'packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh')]
    ledger = {'status': 'RUNNING', 'row': row, 'registry_sha256': digest(registry_path), 'started_unix': time.time(),
              'command': command, 'launch_values': {k: v for k, v in env.items() if k.startswith('CRANE_')},
              'player_sha256': digest(PLAYER), 'physical_player': {'path': str(PLAYER), 'sha256': PLAYER_SHA256},
              'owned_player_bundle': bundle, 'collector_sha256': digest(Path(__file__)), 'probe_version': PROBE_VERSION,
              'trace_enabled': trace_enabled, 'new_independent_n': 0, 'reliability_only': True, 'image_signatures': True, 'default_cpu_affinity': affinity, 'maximum_delta_time': maximum_delta_time,
              'full_compiled_build': {'path':str(BUILD_IDENTITY), 'sha256':digest(BUILD_IDENTITY)},
              'inspected_instrumentation_sources': [{'path': str(path), 'sha256': digest(path)} for path in INSTRUMENTATION_SOURCES],
              'intervention': 'Sparse frame timing enabled; optional catch-up cap only as declared. Original signatures/sensing/physics step preserved; revised compiled build bound.', 'technical_validity_definition': 'reliability assay only; inherited strict checks retained as measured outcomes; no study admission',
              'launcher_sha256': digest(Path(command[-1])), 'wrapper_sha256': digest(Path(command[0])),
              'render_runtime_source': {'path':str(ROOT/'analysis/roboboat_hidden_render_v3.py'), 'sha256':digest(ROOT/'analysis/roboboat_hidden_render_v3.py')}, 'quality_retries': 0}
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
    ledger.update(return_code=code, finished_unix=time.time(), scientific_admission_authorized=False)
    try:
        summary = json.loads((out/'navigation-reset-summary.json').read_text())
        worker = json.loads((out/'worker-0/result.json').read_text())
        fixture = json.loads((out/'fixture-summary.json').read_text())
        checks = technical_checks(summary, worker, fixture)
        render = json.loads((out/'render-audit.json').read_text())
        checks['owned_render_complete'] = (render.get('status') == 'COMPLETE_DEVELOPMENT_ONLY' and render.get('placement_verified') is True and render.get('cleanup_errors') == [])
        if trace_enabled:
            actions = audit_actions(out/'action-timing.jsonl', worker=worker)
            save(out/'action-timing-audit.json', actions)
            checks['command_trace_integrity'] = actions['trace_integrity_pass']
        else:
            checks['trace_disabled_as_declared'] = not (out/'action-timing.jsonl').exists()
        verify_bundle(out/'owned-player')
        checks.update(operational_probe_checks(worker))
        frames=audit_frames(out/'frame-timing.jsonl')
        save(out/'frame-timing-audit.json',frames)
        metadata=frames['metadata']
        expected=metadata['originalMaximumDeltaTime'] if maximum_delta_time is None else maximum_delta_time
        checks.update(frame_trace_present=frames['retained_frame_rows']>0,
                      fixed_physics_step_002=abs(metadata['fixedDeltaTime']-.02)<1e-7,
                      clock_cap_matches_declaration=abs(metadata['appliedMaximumDeltaTime']-expected)<1e-6,
                      clock_constant_through_trace=not frames['issues'])
        # A nonzero launcher is accepted only when its sole failure was inherited
        # expected-status validation. Timeout/early death can never be reclassified.
        checks['launcher_completed'] = code in (0, 1)
        if code == 1:
            checks['status_gate_only_failure'] = fixture['status'] != summary['expectedNavigationStatus']
        ledger['checks'] = checks
        ledger['observed_navigation_status'] = fixture['status']
        ledger['real_time_factor'] = worker.get('realTimeFactor')
        if not all(checks.values()): raise ValueError('failed checks: ' + ', '.join(k for k,v in checks.items() if not v))
        ledger['status'] = 'OVERHEAD_CAPTURE_COMPLETE'
        ledger['scientific_admission_authorized'] = False
    except (OSError, ValueError, KeyError, TypeError) as error:
        ledger.update(status='TECHNICAL_FAILURE', error=str(error))
    save(record, ledger)
    print(json.dumps({'id': row['id'], 'status': ledger['status'], 'observed': ledger.get('observed_navigation_status'), 'error': ledger.get('error')}), flush=True)
    return ledger



def operational_probe_checks(worker):
    return {
        'original_image_signatures_enabled': worker.get('imageSignatures') is True,
        'screen_640x360': (worker.get('screenWidth'), worker.get('screenHeight')) == (640, 360),
        'depth_resolution_unchanged': (worker.get('depthCamera', {}).get('width'), worker.get('depthCamera', {}).get('height')) == (1280, 720),
        'depth_acquired': worker.get('depthCamera', {}).get('acquisitionCount', 0) > 0,
        'camera_topology_unchanged': tuple(worker.get(k) for k in ('enabledCameras', 'enabledSensorCameras', 'enabledSpectatorCameras', 'enabledWaterDriverCameras')) == (1, 1, 0, 0),
        'time_scale_unchanged': worker.get('timeScale') == 1,
    }


def validate_declaration(d):
    if d['schema'] != 'roboboat-tracing-overhead-declaration/v1' or d['new_independent_n'] != 0:
        raise ValueError('exact nonstudy reliability declaration required')
    schedule = d['schedule']
    ids = [u['operational_run_id'] for u in schedule]
    if not schedule or len(ids) != len(set(ids)):
        raise ValueError('unique operational identities required')
    if any(not isinstance(u['trace_enabled'], bool) for u in schedule):
        raise ValueError('boolean tracing toggle required')
    if not any(u['trace_enabled'] for u in schedule) or all(u['trace_enabled'] for u in schedule):
        raise ValueError('both tracing conditions required')
    if any(not i.startswith('boat-reliability-') or '/' in i or '..' in i for i in ids):
        raise ValueError('reliability namespace required')
    paths = [str(Path(v['path']).resolve()) for v in d['dependencies']]
    if len(paths) != len(set(paths)) or str(Path(d['registry']).resolve()) not in paths or str(Path(__file__).resolve()) not in paths:
        raise ValueError('unique registry and collector bindings required')
    for value in d['dependencies']:
        if digest(Path(value['path'])) != value['sha256']:
            raise ValueError('predeclared source/input changed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--declaration',required=True,type=Path)
    a=p.parse_args(); d=json.loads(a.declaration.read_text())
    validate_declaration(d)
    registry_path=Path(d['registry']);registry=json.loads(registry_path.read_text())
    row=next(r for r in registry['rows'] if r['id']==d['physical_row_id'])
    output=Path(d['output_root']);output.mkdir(parents=True,exist_ok=False)
    results=[]
    with Path('/tmp/crane-roboboat-population-render.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for unit in d['schedule']:
            operational_row=json.loads(json.dumps(row))
            operational_row['id']=unit['operational_run_id']
            operational_row['disposition']='RELIABILITY_ONLY_NO_INDEPENDENT_N'
            result=capture(operational_row,registry,registry_path,output,d['domain'],d['port'],
                           d['maximum_delta_time'],trace_enabled=unit['trace_enabled'])
            results.append(result)
    save(output/'terminal.json',{'schema':'roboboat-tracing-overhead-terminal/v1',
         'declaration_sha256':digest(a.declaration),'status':'RELIABILITY_ASSAY_FINISHED',
         'results':results,'scientific_admission_authorized':False,'new_independent_n':0,
         'confirmation_n':0,'replication_n':0})


if __name__=='__main__':main()
