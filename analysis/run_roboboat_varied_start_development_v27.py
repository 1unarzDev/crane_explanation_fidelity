#!/usr/bin/env python3
"""Prospectively declared trace-qualified development collector, candidate v27. No old failures salvaged; fixed fresh-row schedule; confirmation remains separate.

Fresh diverse development configurations; every scheduled outcome retained.
Two isolated compositors, ROS domains, ports and owned player bundles.
Other work may run concurrently on isolated ROS domains/ports and method workers.
"""
import argparse
import hashlib
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
from export_roboboat_population_v2 import project
from export_roboboat_trace_qualified_v4 import publish_terminal
from audit_roboboat_launcher_terminal_v1 import assess as assess_launcher
from roboboat_trace_qualified_validity_v1 import assess as assess_validity

PLAYER = Path('/home/lunarz/worktrees/roboboat-command-shutdown-v17/crane_ml/Builds/CRANE-Worker/CRANE.x86_64')
BUILD_IDENTITY = ROOT/'artifacts/roboboat-command-shutdown-v17/full-build-v1.json'
from audit_roboboat_frame_timing_v1 import audit as audit_frames
from roboboat_initial_pose_contract_v1 import launch_args as pose_args, assess as assess_pose, requested_pose
from roboboat_launch_mount_v24 import launch_route
from roboboat_parallel_navigation_contract_v26 import own_stream_checks, simultaneous_navigation_progress
from roboboat_hidden_render_v4 import state
from concurrent.futures import ThreadPoolExecutor

PLAYER_SHA256 = None # Supplied only from a predeclared verified build before capture.
PROBE_VERSION = 'roboboat-varied-start-population/v27-development'
SOURCE_ROOT = Path(__file__).resolve().parents[1]
LAUNCH_PROJECT = ROOT/'artifacts/roboboat-varied-start-development-v27-001/launch-project'
INSTRUMENTATION_PROJECT = Path('/home/lunarz/worktrees/roboboat-command-shutdown-v17/crane_ml')
INSTRUMENTATION_SOURCES = tuple(INSTRUMENTATION_PROJECT / path for path in (
    'Assets/Scripts/Utils/Performance/CraneActionTimingAudit.cs',
    'Assets/Scripts/Utils/Performance/CraneActionGate.cs',
    'Assets/Scripts/Controllers/ROSOmniXCommand.cs',
    'Assets/Scripts/Performance/CraneBenchmarkRunner.cs',
    'Assets/Scripts/Controllers/CraneROSNavigationState.cs',
    'Assets/Scripts/Utils/ROS/ROSClock.cs'))


def digest_token(value):
    if not value.endswith('\n') or len(value)!=65: raise ValueError('completion marker shape mismatch')
    return hashlib.sha256(value[:-1].encode()).hexdigest()


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


def capture(row, registry, registry_path, output, domain, port, maximum_delta_time=None, declaration_path=None):
    if declaration_path is None: raise ValueError('prospective declaration required')
    out = output / row['id']
    record = out / 'capture-attempt.json'
    if record.exists():
        previous = json.loads(record.read_text())
        if previous['registry_sha256'] != digest(registry_path): raise ValueError('registry differs')
        if previous['status'] in ('VALID_TRACE_QUALIFIED_DEVELOPMENT', 'TECHNICAL_FAILURE'): return previous
        raise RuntimeError('unresolved attempt retained; inspect before successor, never reissue')
    out.mkdir(parents=True, exist_ok=False)
    verify_player()
    bundle = prepare_bundle(BUILD_IDENTITY, out/'owned-player', uuid.uuid4().hex)
    verify_bundle(out/'owned-player')
    affinity = default_affinity()
    config = bound(registry['nav2_configuration'])
    launch_config = LAUNCH_PROJECT/'Tools/Performance'/config.name
    if digest(launch_config) != digest(config): raise ValueError('copied config mismatch')
    requested_pose(row)
    if 'path_file' in row: bound(row['path_file'])
    bound(row['task_contract'])
    env = {**{k:v for k,v in os.environ.items() if not k.startswith('CRANE_')}, 'CRANE_RUN_ID': row['id'], 'CRANE_ROS_PORT': str(port), 'CRANE_ROS_DOMAIN_ID': str(domain),
           'SDL_VIDEODRIVER': 'x11', 'CRANE_RESULT_ROOT': str(out), 'CRANE_PLAYER': bundle['executable']['path'],
           'CRANE_ASTRO_DOCK': '/home/lunarz/crane_explain/packages/astro_dock',
           'CRANE_NOGRAPHICS': '0', 'CRANE_DURATION': '340', 'CRANE_WARMUP': '3',
           'CRANE_SCREEN_WIDTH': '640', 'CRANE_SCREEN_HEIGHT': '360', 'CRANE_TIME_SCALE': '1',
           'CRANE_NAV2_ACTION_DURATION': '310', 'CRANE_NAV2_POST_RESULT_DURATION': '8',
           'CRANE_NAV2_PARAMS': str(launch_config), 'CRANE_CAPTURE_RUNTIME_PARAMETERS': '1',
           'CRANE_NAV2_ACTION_MODE': row['action_mode'], 'CRANE_NAV2_PROFILE': 'train-gpu',
           'CRANE_NAV2_CONTROLLER_EXTRA_ARGS': f"-p goal_checker.xy_goal_tolerance:={row['internal_xy_tolerance_m']}",
           'CRANE_NAV2_GOAL_X': str(row['goal']['x']), 'CRANE_NAV2_GOAL_Y': str(row['goal']['y']),
           'CRANE_NAV2_GOAL_YAW': str(row['goal']['yaw']), 'CRANE_DOCKING_EVALUATOR': '1', 'CRANE_SEED_BASE': str(row['seed'])}
    # Prevent unrelated inherited per-run overrides from altering a declared launch.
    for key in ('CRANE_NAV2_PATH_FILE', 'CRANE_NAV2_UNITY_EXTRA_ARGS', 'CRANE_NAV2_BT_XML', 'CRANE_DISABLE_DEPTH', 'CRANE_DISABLE_RGB'):
        env.pop(key, None)
    if any(c.isspace() for c in str(out)): raise ValueError('inherited launcher requires whitespace-free audit path')
    env['CRANE_NAV2_UNITY_EXTRA_ARGS'] = '--crane-frame-timing-audit '+str(out/'frame-timing.jsonl')+' --crane-action-timing-audit '+str(out/'action-timing.jsonl')
    if maximum_delta_time is not None: env['CRANE_NAV2_UNITY_EXTRA_ARGS'] += ' --crane-maximum-delta-time '+str(maximum_delta_time)
    # The inherited launcher consumes a whitespace-separated extra-args field.
    # The pose helper emits only a fixed option and finite numeric CSV.
    env['CRANE_NAV2_UNITY_EXTRA_ARGS'] += ' ' + ' '.join(pose_args(row))
    if 'path_file' in row:
        original_path = ROOT/row['path_file']['path']
        # Resolve exact staged bytes inside the launcher Docker mount.
        # Compiler sources and the exact player remain on the original project.
        launch_path = launch_route(LAUNCH_PROJECT, row, ROOT)
        if digest(launch_path) != digest(original_path): raise ValueError('copied path mismatch')
        env['CRANE_NAV2_PATH_FILE'] = str(launch_path)
    command = [str(ROOT/'scripts/run_roboboat_hidden_render_v4.sh'), '--expected-class', bundle['expected_class'], '--audit-path', str(out/'render-audit.json'), str(LAUNCH_PROJECT/'Tools/Performance/run_nav2_controller_fixture_capture_v15.sh')]
    ledger = {'status': 'RUNNING', 'row': row, 'registry_sha256': digest(registry_path), 'started_unix': time.time(),
              'command': command, 'launch_values': {k: v for k, v in env.items() if k.startswith('CRANE_')},
              'player_sha256': digest(PLAYER), 'physical_player': {'path': str(PLAYER), 'sha256': PLAYER_SHA256},
              'owned_player_bundle': bundle, 'collector_sha256': digest(Path(__file__)), 'probe_version': PROBE_VERSION,
              'image_signatures': True, 'default_cpu_affinity': affinity, 'maximum_delta_time': maximum_delta_time,
              'full_compiled_build': {'path':str(BUILD_IDENTITY), 'sha256':digest(BUILD_IDENTITY)},
              'inspected_instrumentation_sources': [{'path': str(path), 'sha256': digest(path)} for path in INSTRUMENTATION_SOURCES],
              'intervention': 'Sparse frame timing enabled; optional catch-up cap only as declared. Original signatures/sensing/physics step preserved; revised compiled build bound.', 'technical_validity_definition': 'prospective trace-qualified development; stale rejections allowed only with complete gate/counter/payload qualification; other gates retained',
              'launcher_sha256': digest(Path(command[-1])), 'wrapper_sha256': digest(Path(command[0])),
              'render_runtime_source': {'path':str(ROOT/'analysis/roboboat_hidden_render_v4.py'), 'sha256':digest(ROOT/'analysis/roboboat_hidden_render_v4.py')}, 'quality_retries': 0}
    ledger['prospective_declaration'] = {'path':str(declaration_path), 'sha256':digest(declaration_path)}
    ledger['development_recording_admitted'] = False
    ledger['confirmation_n'] = 0
    ledger['independent_n_added'] = 0
    ledger['operational_replay'] = False
    ledger['platform_version'] = json.loads(declaration_path.read_text())['platform_version']
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
        records = [json.loads(line) for line in (out/'action-timing.jsonl').read_text().splitlines() if line.strip()]
        validity = assess_validity(summary,worker,fixture,records,(out/'worker-0/player.log').read_text())
        save(out/'trace-qualified-validity-candidate-audit.json',validity)
        checks = dict(validity['checks'])
        pose_audit = assess_pose(row, out/'worker-0/player.log')
        save(out/'initial-pose-contract-audit.json', pose_audit)
        checks['initial_pose_readback'] = pose_audit['initialization_readback_pass']
        receipt_path = out/'fixture-capture-complete.token.receipt.json'
        receipt = json.loads(receipt_path.read_text())
        marker = out/'fixture-capture-complete.token'
        checks['capture_completion_finish_observed'] = worker.get('finishedAfterCaptureCompletion') is True
        checks['completion_identity'] = receipt['run_id']==row['id'] and receipt['episode_id']==row['id']+'-worker-0'
        checks['complete_fixture_binding'] = receipt['summary']=={'path':str(out/'fixture-summary.json'),'sha256':digest(out/'fixture-summary.json')}
        checks['completion_token_binding'] = digest_token(marker.read_text())==receipt['token_sha256']
        checks['fixture_capture_duration'] = receipt['post_result_seconds']==8 and receipt['bt_drain_seconds']==.5
        ledger['capture_completion_receipt'] = {'path':str(receipt_path),'sha256':digest(receipt_path)}
        render = json.loads((out/'render-audit.json').read_text())
        checks['owned_render_complete'] = (render.get('status') == 'COMPLETE_DEVELOPMENT_ONLY' and render.get('placement_verified') is True and render.get('cleanup_errors') == [])
        actions = audit_actions(out/'action-timing.jsonl', worker=worker)
        save(out/'action-timing-audit.json', actions)
        checks['command_trace_integrity'] = actions['trace_integrity_pass']
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
        launcher = assess_launcher(summary,worker,fixture,(out/'controller.log').read_text(),(out/'endpoint.log').read_text(),code)
        save(out/'launcher-terminal-audit.json',launcher)
        checks['launcher_terminal_classification'] = launcher['terminal_classification_pass']
        checks.update(own_stream_checks(row, fixture, summary, domain, port))
        checks['declared_ros_domain_port'] = (summary['transport']['rosDomainId']==domain and summary['transport']['rosTcpPort']==port)
        ledger['checks'] = checks
        ledger['observed_navigation_status'] = fixture['status']
        ledger['real_time_factor'] = worker.get('realTimeFactor')
        if not all(checks.values()): raise ValueError('failed checks: ' + ', '.join(k for k,v in checks.items() if not v))
        ledger['level_outcomes'] = project(row, out, out/'exports-v2', config)
        ledger['status'] = 'VALID_TRACE_QUALIFIED_DEVELOPMENT'
        ledger['development_recording_admitted'] = True
    except (OSError, ValueError, KeyError, TypeError) as error:
        ledger.update(status='TECHNICAL_FAILURE', error=str(error))
    save(record, ledger)
    if ledger['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT':
        # Supplemental export provenance binds original intent and new namespace.
        ledger = publish_terminal(row, registry_path, out, config, declaration_path)
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


def validate_declaration(d, declaration_path):
    if d['schema']!='roboboat-trace-qualified-development-declaration/v1' or d['confirmation_n']!=0 or d['replication_n']!=0:
        raise ValueError('development only; no confirmation/replication contamination')
    dependencies={str(Path(v['path']).resolve()):v['sha256'] for v in d['dependencies']}
    for path,expected in dependencies.items():
        if digest(Path(path))!=expected:raise ValueError('declared input changed: '+path)
    required=[Path(__file__).resolve(),Path(d['registry']),Path(d['original_registry']),BUILD_IDENTITY,
        LAUNCH_PROJECT/'launch-mount-manifest.json']
    required+=[ROOT/'analysis'/name for name in ('export_roboboat_trace_qualified_v4.py',
        'export_roboboat_population_v2.py','audit_roboboat_launcher_terminal_v1.py','roboboat_trace_qualified_validity_v1.py',
        'audit_roboboat_trace_semantics_v1.py','audit_roboboat_action_trace_v1.py','audit_roboboat_frame_timing_v1.py',
        'roboboat_owned_player_bundle_v1.py','roboboat_hidden_render_v4.py','roboboat_render_fps_lease_v1.py',
        'roboboat_initial_pose_contract_v1.py','roboboat_launch_mount_v24.py','roboboat_parallel_navigation_contract_v26.py',
        'probe_roboboat_parallel_players_v20.py','roboboat_development_schedule_v27.py')]
    if not all(str(p.resolve()) in dependencies for p in required):raise ValueError('complete collection closure required')
    mount=json.loads((LAUNCH_PROJECT/'launch-mount-manifest.json').read_text())
    if mount['root']!=str(LAUNCH_PROJECT):raise ValueError('exact isolated launch mount required')
    for item in mount['launch_files']+mount['routes']:
        for kind in ('original','snapshot'):
            record=item[kind]
            if dependencies.get(str(Path(record['path']).resolve()))!=record['sha256'] or digest(Path(record['path']))!=record['sha256']:
                raise ValueError('complete source/mount bytes required')
    verify_player()
    registry_path=Path(d['registry']);registry=json.loads(registry_path.read_text())
    original=json.loads(Path(d['original_registry']).read_text())
    operational=json.loads(Path(d['operational_origin_declaration']).read_text())
    from roboboat_development_schedule_v27 import schedule
    rows,clusters,lanes,excluded=schedule(original,list(operational['origin_rows'].values()),d['schedule_seed'])
    if registry['status']!='DEVELOPMENT_EXPLORATORY_VARIED_START' or registry['rows']!=rows or registry['clusters']!=clusters:
        raise ValueError('outcome-blind original development population required')
    if d['rows']!=[r['id'] for r in rows] or d['lanes']!=lanes or d['excluded_inspected_clusters']!=excluded:
        raise ValueError('complete declared fresh schedule required')
    for row in rows:
        requested_pose(row)
        for key in ('path_file','task_contract'):
            if key in row and str(bound(row[key]).resolve()) not in dependencies:raise ValueError('all route/task inputs must be bound')
        if 'path_file' in row:launch_route(LAUNCH_PROJECT,row,ROOT)
    # Existing operational aliases retain their original population identities.
    # Exclude both variants of every inspected geometry, regardless of outcome.
    attempted=set()
    for prior in d['prior_capture_roots']:
        for path in Path(prior).glob('*/capture-intent.json'):
            old=json.loads(path.read_text())['row'];attempted.add(old['cluster_id'])
    if {r['cluster_id'] for r in rows}&attempted:raise ValueError('attempted geometry cannot enter fresh development')
    if len(d['resources'])!=2 or len({r['domain'] for r in d['resources']})!=2 or len({r['port'] for r in d['resources']})!=2:
        raise ValueError('two isolated execution resources required')
    if not all(0<=r['domain']<=232 and 1024<=r['port']<=65535 for r in d['resources']) or d['maximum_delta_time']!=.04:
        raise ValueError('declared ROS resources/catch-up cap required')
    review=json.loads(Path(d['parallel_qualification']['path']).read_text())
    if digest(Path(d['parallel_qualification']['path']))!=d['parallel_qualification']['sha256'] or not review['fixed_two_case_parallel_navigation_qualified']:
        raise ValueError('completed parallel operational qualification required before collection')
    return registry_path,registry,rows


def snapshot(rows, output, futures, elapsed):
    clients=state('clients'); observations=[]
    for row, future in zip(rows, futures):
        out=output/row['id']; manifest=out/'owned-player/bundle-binding.json'
        expected=json.loads(manifest.read_text())['expected_class'] if manifest.exists() else None
        own=[{k:c.get(k) for k in ('pid','class','mapped','monitor','workspace')} for c in clients if expected and c.get('class')==expected]
        def count(name):
            path=out/name
            return path.read_bytes().count(b'\n') if path.exists() else 0
        observations.append({'case_id':row['id'], 'wrapper_live':not future.done(), 'clients':own,
            'validation_records':count('worker-0/result.validation.jsonl'), 'action_records':count('action-timing.jsonl')})
    return {'elapsed_wall_s':elapsed, 'observations':observations}


def run_lane(ids,resource,by_id,registry,registry_path,output,d,declaration):
    results=[]
    for identifier in ids:
        row=by_id[identifier]
        # No retries, admission remains independent of navigation outcome.
        results.append(capture(row,registry,registry_path,output,resource['domain'],resource['port'],
            d['maximum_delta_time'],declaration))
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--declaration',type=Path,required=True)
    a=p.parse_args();d=json.loads(a.declaration.read_text())
    global PLAYER_SHA256
    PLAYER_SHA256=digest(PLAYER)
    registry_path,registry,rows=validate_declaration(d,a.declaration)
    output=Path(d['output_root']);output.mkdir(parents=True,exist_ok=False)
    by_id={r['id']:r for r in rows}
    save(output/'run-intent.json',{'declaration_sha256':digest(a.declaration),'status':'RUNNING',
        'scheduled_geometries':len(registry['clusters']),'scheduled_attempts':len(rows),'phase':'DEVELOPMENT_EXPLORATORY',
        'quality_retries':0,'confirmation_n':0,'replication_n':0})
    with Path('/tmp/crane-roboboat-population-render.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(run_lane,ids,resource,by_id,registry,registry_path,output,d,a.declaration.resolve())
                for ids,resource in zip(d['lanes'],d['resources'])]
            results=[record for future in futures for record in future.result()]
    save(output/'terminal.json',{'schema':PROBE_VERSION,'status':'TRACE_QUALIFIED_DEVELOPMENT_BATCH_FINISHED',
        'declaration_sha256':digest(a.declaration),'results':results,'physical_attempts':len(results),
        'valid_recordings':sum(r['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT' for r in results),
        'confirmation_n':0,'replication_n':0,'land_n_added':0,'study_ceiling':None})


if __name__=='__main__':main()
