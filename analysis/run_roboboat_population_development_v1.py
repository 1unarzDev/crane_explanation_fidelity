#!/usr/bin/env python3
"""Additive geometry-development collector. Immutable attempts; no outcome admission.

Single compositor worker until multi-window routing is independently qualified.
Other work may run concurrently on isolated ROS domains/ports and method workers.
"""
import argparse
import copy
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from build_roboboat_terminal_batch import runtime_config, save
from generate_roboboat_population_v1 import ROOT, DOC, digest
from roboboat_temporal_certificate import build_ladder
from roboboat_temporal_certificate_v2 import upgrade_development_packet, certificate, render, audit_ladder
from reference_roboboat_temporal_v2 import calculate

PLAYER = Path('/home/lunarz/worktrees/roboboat-docking/packages/crane_ml/Builds/CRANE-RoboBoat-Bow/CRANE.x86_64')


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


def build(row, out, config):
    contract = json.loads(bound(row['task_contract']).read_text())
    readback = json.loads((out / 'runtime-parameters.json').read_text())
    effective = runtime_config(config.read_bytes(), readback, row['internal_xy_tolerance_m'])
    (out / 'effective-configuration.yaml').write_bytes(effective)
    summary = json.loads((out / 'fixture-summary.json').read_text())
    legacy = copy.deepcopy(contract)
    legacy.update(schema='roboboat-terminal-task/v1', id=contract['id']+'-legacy-build', contact_required=True)
    legacy.pop('contact_policy')
    opaque = 'opaque-geometry-' + hashlib.sha256(row['id'].encode()).hexdigest()[:20]
    levels = build_ladder(summary, effective, legacy, opaque+'-raw')
    packets = []
    for index, packet in enumerate(levels):
        packet = upgrade_development_packet(packet, opaque+f'-L{index}', contract)
        cert = certificate(packet)
        reference = calculate(packet)
        if cert['sampled_task_support'] != reference['sampled_task_support']:
            raise ValueError('independent task reference mismatch')
        # Keep every permitted value identical for both future methods. References,
        # source capture identities and candidate outputs stay outside method packets.
        save(out / 'method_packets' / f'L{index}.json', packet)
        save(out / 'evaluator' / f'L{index}.json', reference)
        save(out / 'candidate_outputs' / f'L{index}.json', {'answer': render(packet, cert), 'certificate': cert, 'model_calls': 0})
        packets.append(packet)
    save(out / 'evaluator' / 'ladder-audit.json', audit_ladder(packets))
    return [certificate(packet)['sampled_task_support'] for packet in packets]


def capture(row, registry, registry_path, output, domain, port):
    out = output / row['id']
    record = out / 'capture-attempt.json'
    if record.exists():
        previous = json.loads(record.read_text())
        if previous['registry_sha256'] != digest(registry_path): raise ValueError('registry differs')
        if previous['status'] in ('VALID_DEVELOPMENT', 'TECHNICAL_FAILURE'): return previous
        raise RuntimeError('unresolved attempt retained; inspect before successor, never reissue')
    out.mkdir(parents=True, exist_ok=False)
    config = bound(registry['nav2_configuration'])
    if 'path_file' in row: bound(row['path_file'])
    bound(row['task_contract'])
    env = {**{k:v for k,v in os.environ.items() if not k.startswith('CRANE_')}, 'CRANE_RUN_ID': row['id'], 'CRANE_ROS_PORT': str(port), 'CRANE_ROS_DOMAIN_ID': str(domain),
           'CRANE_RESULT_ROOT': str(out), 'CRANE_PLAYER': str(PLAYER),
           'CRANE_ASTRO_DOCK': '/home/lunarz/crane_explain/packages/astro_dock',
           'CRANE_NOGRAPHICS': '0', 'CRANE_DURATION': '340', 'CRANE_WARMUP': '3',
           'CRANE_NAV2_ACTION_DURATION': '310', 'CRANE_NAV2_POST_RESULT_DURATION': '8',
           'CRANE_NAV2_PARAMS': str(config), 'CRANE_CAPTURE_RUNTIME_PARAMETERS': '1',
           'CRANE_NAV2_ACTION_MODE': row['action_mode'], 'CRANE_NAV2_PROFILE': 'train-gpu',
           'CRANE_NAV2_CONTROLLER_EXTRA_ARGS': f"-p goal_checker.xy_goal_tolerance:={row['internal_xy_tolerance_m']}",
           'CRANE_NAV2_GOAL_X': str(row['goal']['x']), 'CRANE_NAV2_GOAL_Y': str(row['goal']['y']),
           'CRANE_NAV2_GOAL_YAW': str(row['goal']['yaw']), 'CRANE_DOCKING_EVALUATOR': '1', 'CRANE_SEED_BASE': str(row['seed'])}
    # Prevent unrelated inherited per-run overrides from altering a declared launch.
    for key in ('CRANE_NAV2_PATH_FILE', 'CRANE_NAV2_UNITY_EXTRA_ARGS', 'CRANE_NAV2_BT_XML', 'CRANE_DISABLE_DEPTH', 'CRANE_DISABLE_RGB'):
        env.pop(key, None)
    if 'path_file' in row: env['CRANE_NAV2_PATH_FILE'] = str(ROOT / row['path_file']['path'])
    command = [str(ROOT/'scripts/run_roboboat_hidden_render.sh'), str(ROOT/'packages/crane_ml/Tools/Performance/run_nav2_controller_fixture.sh')]
    ledger = {'status': 'RUNNING', 'row': row, 'registry_sha256': digest(registry_path), 'started_unix': time.time(),
              'command': command, 'launch_values': {k: v for k, v in env.items() if k.startswith('CRANE_')},
              'player_sha256': digest(PLAYER), 'technical_validity_definition': 'no desired outcome check; strict runtime/sensor/transport gates',
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
        # A nonzero launcher is accepted only when its sole failure was inherited
        # expected-status validation. Timeout/early death can never be reclassified.
        checks['launcher_completed'] = code in (0, 1)
        if code == 1:
            checks['status_gate_only_failure'] = fixture['status'] != summary['expectedNavigationStatus']
        ledger['checks'] = checks
        ledger['observed_navigation_status'] = fixture['status']
        ledger['real_time_factor'] = worker.get('realTimeFactor')
        if not all(checks.values()): raise ValueError('failed checks: ' + ', '.join(k for k,v in checks.items() if not v))
        ledger['level_outcomes'] = build(row, out, config)
        ledger['status'] = 'VALID_DEVELOPMENT'
    except (OSError, ValueError, KeyError, TypeError) as error:
        ledger.update(status='TECHNICAL_FAILURE', error=str(error))
    save(record, ledger)
    print(json.dumps({'id': row['id'], 'status': ledger['status'], 'observed': ledger.get('observed_navigation_status'), 'error': ledger.get('error')}), flush=True)
    return ledger


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--registry', required=True, type=Path)
    p.add_argument('--output-root', required=True, type=Path)
    p.add_argument('--domain', default=191, type=int)
    p.add_argument('--port', default=11481, type=int)
    a = p.parse_args()
    registry = json.loads(a.registry.read_text())
    if registry['status'] != 'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION': raise ValueError('development registry required')
    if not 0 <= a.domain <= 232 or not 1024 <= a.port <= 65535: raise ValueError('invalid worker resources')
    output = a.output_root.resolve(); output.mkdir(parents=True, exist_ok=True)
    with Path('/tmp/crane-roboboat-population-render.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        results = []
        for row in registry['rows']:
            result = capture(row, registry, a.registry.resolve(), output, a.domain, a.port)
            results.append(result)
            # Stop repeated infrastructure faults; next independent development batch
            # may follow a documented repair. Every failed attempt remains retained.
            if len(results) >= 2 and all(r['status']=='TECHNICAL_FAILURE' for r in results[-2:]): break
        save(output/'batch-accounting.json', {'status': 'DEVELOPMENT_ONLY', 'registry_sha256': digest(a.registry),
             'attempted': len(results), 'valid_recordings': sum(r['status']=='VALID_DEVELOPMENT' for r in results),
             'technical_failures': sum(r['status']=='TECHNICAL_FAILURE' for r in results),
             'complete_paired_clusters': sum(all(any(r['row']['id']==identifier and r['status']=='VALID_DEVELOPMENT' for r in results) for identifier in cluster['rows']) for cluster in registry['clusters']),
             'unattempted': [r['id'] for r in registry['rows'] if r['id'] not in {v['row']['id'] for v in results}],
             'confirmation_n': 0, 'land_n_added': 0})

if __name__ == '__main__': main()
