"""Read-only review of every valid timeout in a fixed full-denominator development profile."""
import argparse
import json
from pathlib import Path

import run_roboboat_varied_start_development_v27 as collector
from run_roboboat_population_responses_v1 import binding,checked
from roboboat_owned_player_bundle_v1 import verify as verify_bundle
from roboboat_temporal_certificate_v2 import certificate


def review(profile_path):
    profile_path=Path(profile_path).resolve();p=json.loads(profile_path.read_text())
    if p['schema']!='roboboat-trace-development-profile/v2' or p['confirmation_n']!=0:
        raise ValueError('development-only profile required')
    for r in p['dependencies']:checked(r)
    declaration=Path(p['dependencies'][0]['path']);d=json.loads(declaration.read_text())
    registry_path,registry,rows=collector.validate_declaration(d,declaration)
    by_id={r['id']:r for r in rows}
    if [r['id'] for r in p['rows']]!=d['rows']:raise ValueError('full declared denominator required')
    results=[];selected=[]
    for row in p['rows']:
        if row['status']!='VALID_TRACE_QUALIFIED_DEVELOPMENT' or row.get('action_status')!='timeout':continue
        selected.append(row['id']);out=Path(d['output_root'])/row['id']
        original=json.loads((out/'capture-attempt.json').read_text());published=json.loads((out/'capture-export-terminal-trace-v4.json').read_text())
        if published['original_capture_terminal']!=binding(out/'capture-attempt.json'):raise ValueError('original timeout binding mismatch')
        for source in published['raw_sources']:checked(source)
        worker=json.loads((out/'worker-0/result.json').read_text());fixture=json.loads((out/'fixture-summary.json').read_text());summary=json.loads((out/'navigation-reset-summary.json').read_text())
        records=[json.loads(r) for r in (out/'action-timing.jsonl').read_text().splitlines() if r.strip()]
        validity=collector.assess_validity(summary,worker,fixture,records,(out/'worker-0/player.log').read_text())
        trace=collector.audit_actions(out/'action-timing.jsonl',worker=worker);frames=collector.audit_frames(out/'frame-timing.jsonl')
        launcher=collector.assess_launcher(summary,worker,fixture,(out/'controller.log').read_text(),(out/'endpoint.log').read_text(),original['return_code'])
        receipt=json.loads((out/'fixture-capture-complete.token.receipt.json').read_text());render=json.loads((out/'render-audit.json').read_text())
        verify_bundle(out/'owned-player')
        physical=by_id[row['id']];resource=next(r for ids,r in zip(d['lanes'],d['resources']) if row['id'] in ids)
        checks=dict(validity['checks']);checks.update(collector.operational_probe_checks(worker))
        checks.update(collector.own_stream_checks(physical,fixture,summary,resource['domain'],resource['port']))
        checks.update(original_all_gates=all(original['checks'].values()),command_trace_complete=trace['trace_integrity_pass'],
            frame_trace_present=frames['retained_frame_rows']>0 and not frames['issues'],
            fixed_step=abs(frames['metadata']['fixedDeltaTime']-.02)<1e-7,
            clock_cap=abs(frames['metadata']['appliedMaximumDeltaTime']-.04)<1e-6,
            strict_start_receipt=collector.assess_pose(physical,out/'worker-0/player.log')['initialization_readback_pass'],
            launcher_terminal=launcher['terminal_classification_pass'],
            owned_render=render['status']=='COMPLETE_DEVELOPMENT_ONLY' and render['placement_verified'] is True and not render['cleanup_errors'],
            worker_capture_finish=worker.get('finishedAfterCaptureCompletion') is True,
            receipt_identity=receipt['run_id']==row['id'] and receipt['episode_id']==row['id']+'-worker-0',
            receipt_summary_binding=receipt['summary']==binding(out/'fixture-summary.json'),
            receipt_token_binding=receipt['token_sha256']==collector.digest_token((out/'fixture-capture-complete.token').read_text()),
            fixture_timeout=fixture['status']=='timeout',no_recorded_action_result=fixture['terminalEventV2'] is None,
            no_claimed_post_result_window=fixture['postResultSecondsObserved'] is None)
        levels=[]
        for level in range(3):
            packet_path=out/'exports-v2/method_packets'/f'L{level}.json';packet=json.loads(packet_path.read_text());action=packet['action'];reference=packet.get('return_observation')
            levels.append({'level':level,'packet':binding(packet_path),'sampled_task_support':certificate(packet)['sampled_task_support'],
                'checks':{'fixture_status_not_terminal_ros_result':action['status']=='timeout' and action['event_time_support']=='historical-event-time-unavailable',
                    'receipt_not_fabricated':action['identity'] is None and action['receipt_clock'] is None and action['receipt_wall_seconds'] is None,
                    'no_fabricated_post_result_samples':packet.get('post_result',[])==[],
                    'reference_scope':reference is None or reference['alignment']=='last-pre-result-observation'}})
        checks['all_levels_honest_scope']=all(all(r['checks'].values()) for r in levels)
        results.append({'row_id':row['id'],'passed':all(checks.values()),'checks':checks,'levels':levels,
            'original':binding(out/'capture-attempt.json'),'published':binding(out/'capture-export-terminal-trace-v4.json'),
            'receipt':binding(out/'fixture-capture-complete.token.receipt.json'),'action_trace':trace,
            'worker_wall_seconds':worker['wallSeconds'],'average_real_time_factor':worker['realTimeFactor']})
    return {'schema':'roboboat-clean-timeout-retention-review/v32','profile':binding(profile_path),'reviewer':binding(__file__),
        'declaration':binding(declaration),'build':binding(collector.BUILD_IDENTITY),'scheduled_denominator':len(p['rows']),
        'all_selected_valid_timeouts':selected,'results':results,'clean_fixture_timeout_retention_observed':bool(results) and all(r['passed'] for r in results),
        'scope':'Every admitted fixture timeout in this full scheduled development snapshot. Original predicates and missing result/post-result scope reconstructed; no original disposition changed. Not a ROS server cancellation/result, physical docking failure, full timeout population reliability, causal failure mechanism, source-complete explanation score or independent N.',
        'historical_external_runtime_closure_authenticated':False,'endpoint_scores':0,'model_calls':0,'confirmation_n':0,'replication_n':0,'independent_n_added':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();target=Path(a.output)
    if target.exists():raise FileExistsError('immutable timeout review required')
    r=review(a.profile);target.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'reviewed_timeouts':len(r['results']),'all_pass':r['clean_fixture_timeout_retention_observed'],'endpoint_scores':0}))
