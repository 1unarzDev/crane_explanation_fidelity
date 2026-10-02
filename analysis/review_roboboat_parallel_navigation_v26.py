"""Root source/trace review of the fixed concurrent navigation operational assay."""
import argparse
import json
from pathlib import Path

import run_roboboat_parallel_navigation_operational_v26 as collector
from roboboat_owned_player_bundle_v1 import binding, verify_build, verify as verify_bundle
from audit_roboboat_action_trace_v1 import read as audit_actions
from audit_roboboat_frame_timing_v1 import audit as audit_frames
from audit_roboboat_launcher_terminal_v1 import assess as assess_launcher
from roboboat_trace_qualified_validity_v1 import assess as assess_validity
from build_roboboat_terminal_batch import save


def review(declaration_path):
    path = Path(declaration_path).resolve(); d = json.loads(path.read_text())
    registry_path, registry, rows = collector.validate_declaration(d, path)
    root = Path(d['output_root']); terminal_path = root/'terminal.json'
    terminal = json.loads(terminal_path.read_text())
    if (terminal['status'] != 'PARALLEL_NAVIGATION_OPERATIONAL_BATCH_FINISHED' or
        terminal['declaration_sha256'] != binding(path)['sha256'] or terminal['physical_attempts'] != 2 or
        [r['row']['id'] for r in terminal['results']] != d['rows']):
        raise ValueError('complete fixed declared two-run operational schedule required')
    build, _ = verify_build(collector.BUILD_IDENTITY)
    results = []
    for row in rows:
        out = root/row['id']; original = json.loads((out/'capture-attempt.json').read_text())
        published = json.loads((out/'capture-export-terminal-trace-v3.json').read_text())
        if published['original_capture_terminal'] != binding(out/'capture-attempt.json'):
            raise ValueError('original capture binding changed')
        for source in published['raw_sources']:
            if binding(source['path']) != source:
                raise ValueError('original raw capture source changed')
        worker = json.loads((out/'worker-0/result.json').read_text())
        summary = json.loads((out/'navigation-reset-summary.json').read_text())
        fixture = json.loads((out/'fixture-summary.json').read_text())
        records = [json.loads(line) for line in (out/'action-timing.jsonl').read_text().splitlines() if line.strip()]
        validity = assess_validity(summary, worker, fixture, records, (out/'worker-0/player.log').read_text())
        actions = audit_actions(out/'action-timing.jsonl', worker=worker)
        frames = audit_frames(out/'frame-timing.jsonl')
        launcher = assess_launcher(summary, worker, fixture, (out/'controller.log').read_text(), (out/'endpoint.log').read_text(), original['return_code'])
        receipt_path = out/'fixture-capture-complete.token.receipt.json'; receipt = json.loads(receipt_path.read_text())
        render = json.loads((out/'render-audit.json').read_text())
        verify_bundle(out/'owned-player')
        checks = dict(validity['checks']); checks.update(collector.operational_probe_checks(worker))
        resource=d['resources'][row['id']]
        checks.update(collector.own_stream_checks(row, fixture, summary, resource['domain'], resource['port']))
        pose=collector.assess_pose(row, out/'worker-0/player.log')
        checks['startup_pose']=pose['initialization_readback_pass']
        checks.update(command_trace_integrity=actions['trace_integrity_pass'],
            frame_trace=frames['retained_frame_rows'] > 0 and not frames['issues'],
            fixed_step=abs(frames['metadata']['fixedDeltaTime']-.02) < 1e-7,
            clock_cap=abs(frames['metadata']['appliedMaximumDeltaTime']-.04) < 1e-6,
            launcher_terminal=launcher['terminal_classification_pass'],
            original_all_checks=all(original['checks'].values()),
            capture_finish=worker.get('finishedAfterCaptureCompletion') is True,
            capture_identity=receipt['run_id'] == row['id'] and receipt['episode_id'] == row['id']+'-worker-0',
            capture_summary_binding=receipt['summary'] == binding(out/'fixture-summary.json'),
            capture_token_binding=collector.digest_token((out/'fixture-capture-complete.token').read_text()) == receipt['token_sha256'],
            capture_window=receipt['post_result_seconds'] == 8 and receipt['bt_drain_seconds'] == .5 and fixture['postResultSecondsObserved'] >= 8,
            render_complete=render['status'] == 'COMPLETE_DEVELOPMENT_ONLY' and render.get('placement_verified') is True and render['cleanup_errors'] == [],
            terminal_valid=original['status'] == published['status'] == 'VALID_TRACE_QUALIFIED_DEVELOPMENT')
        results.append({'row_id': row['id'], 'passed': all(checks.values()), 'checks': checks,
            'original': binding(out/'capture-attempt.json'), 'published': binding(out/'capture-export-terminal-trace-v3.json'),
            'receipt': binding(receipt_path), 'frames': frames, 'action_trace': actions,
            'navigation_status': fixture['status'], 'worker_wall_seconds': worker['wallSeconds'],
            'post_result_seconds_observed': fixture['postResultSecondsObserved']})
    observations_path=root/'simultaneous-navigation-observations.json'
    observations=json.loads(observations_path.read_text())
    concurrent=collector.simultaneous_navigation_progress(observations['samples']) and not observations['observer_errors']
    renders=[json.loads((root/row['id']/'render-audit.json').read_text()) for row in rows]
    acquired=[r['fps_lease'] for r in renders];released=[r['fps_lease_release'] for r in renders]
    fps_checks={
        'overlapping_lease_owners':sorted(a['active_owners'] for a in acquired)==[1,2],
        'common_original_fps':len({a['original_fps'] for a in acquired})==1,
        'desired_fps_60':all(a['desired_fps']==60 for a in acquired),
        'first_release_retains_fps':sum(r['remaining_owners']==1 and r['original_restored'] is False and r['fps']==60 for r in released)==1,
        'last_release_restores_original':sum(r['remaining_owners']==0 and r['original_restored'] is True and r['fps']==acquired[0]['original_fps'] for r in released)==1,
        'owned_outputs_removed':all(r.get('owned_output_removed') is True for r in renders)}
    statuses = sorted({r['navigation_status'] for r in results})
    return {'schema': 'roboboat-parallel-navigation-operational-review/v26',
        'declaration': binding(path), 'terminal': binding(terminal_path), 'review_source': binding(__file__),
        'build': binding(collector.BUILD_IDENTITY), 'bound_current_sources': len(build['source_bindings_current']),
        'results': results, 'fixed_two_case_parallel_navigation_qualified': all(r['passed'] for r in results) and concurrent and all(fps_checks.values()),
        'observations':binding(observations_path),'concurrent_command_validation_window_progress':concurrent,'fps_checks':fps_checks,
        'observed_navigation_statuses': statuses, 'timeout_retention_operationally_observed': 'timeout' in statuses,
        'v17_shutdown_population_qualified': False, 'varied_start_navigation_population_qualified': False,
        'parallel_collection_population_reliability_established': False, 'independent_n_added': 0, 'confirmation_n': 0, 'replication_n': 0,
        'scope': 'Fixed two zero-N concurrent v17-platform navigation replays, complete original trace/runtime/sensor/capture/launcher predicates reconstructed. All successes, including late-result completion. Own-run/mode/route-or-goal/pose/domain/port and observed concurrent command/validation progress plus FPS ownership/restoration required. No full timeout/failure reliability, causal speedup, physics equivalence, population rate or explanation endpoint claim. Root source/engineering review only.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--declaration', required=True); p.add_argument('--output', required=True)
    a = p.parse_args()
    if Path(a.output).exists(): raise FileExistsError('fresh review output required')
    result = review(a.declaration); save(Path(a.output), result)
    print(json.dumps({k: result[k] for k in ('fixed_two_case_parallel_navigation_qualified', 'observed_navigation_statuses', 'timeout_retention_operationally_observed', 'independent_n_added')}))
