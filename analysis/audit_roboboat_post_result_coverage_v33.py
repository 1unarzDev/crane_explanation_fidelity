"""Read-only coverage audit separating received results from fixture timeouts."""
import argparse
from collections import Counter
import json
from pathlib import Path
from run_roboboat_population_responses_v1 import binding,checked
from roboboat_temporal_certificate_v2 import certificate
from roboboat_post_result_clock_v28 import capture_gate


def audit(profile_path):
    profile_path=Path(profile_path).resolve();p=json.loads(profile_path.read_text())
    if p['schema']!='roboboat-trace-development-profile/v2' or p['confirmation_n']!=0:
        raise ValueError('development profile only')
    for record in p['dependencies']:checked(record)
    declaration_path=Path(p['dependencies'][0]['path']);d=json.loads(declaration_path.read_text())
    registry=json.loads(Path(d['registry']).read_text());by_id={r['id']:r for r in registry['rows']}
    if [r['id'] for r in p['rows']]!=d['rows']:raise ValueError('full fixed denominator required')
    results=[];dependencies=[binding(profile_path),binding(__file__),binding(Path(capture_gate.__code__.co_filename)),binding(Path(certificate.__code__.co_filename))]
    for row in p['rows']:
        record=dict(row)
        if row['status']!='VALID_TRACE_QUALIFIED_DEVELOPMENT':results.append(record);continue
        out=Path(d['output_root'])/row['id'];fixture_path=out/'fixture-summary.json';packet_path=out/'exports-v2/method_packets/L2.json';worker_path=out/'worker-0/result.json'
        f=json.loads(fixture_path.read_text());e=json.loads(packet_path.read_text());w=json.loads(worker_path.read_text())
        dependencies.extend(binding(path) for path in (fixture_path,packet_path,worker_path))
        raw=[r for r in f['trajectory'] if r['phase']=='post_result'];packet=e['post_result']
        if len(raw)!=len(packet) or [r['simSeconds'] for r in raw]!=[r['simSeconds'] for r in packet]:
            raise ValueError('raw-to-L2 post-result clock inventory differs')
        cert=certificate(e)
        if cert['coverage']['complete_sampled_window']!=row['complete_sampled_window']:raise ValueError('profile/certificate mismatch')
        if f['status']!=e['action']['status'] or f['status']!=row['action_status']:
            raise ValueError('fixture/packet/profile action status mismatch')
        received=f['terminalEventV2'] is not None
        if not received:
            action=e['action']
            if (f['status']!='timeout' or raw or packet or f['postResultSecondsObserved'] is not None
                    or action['event_time_support']!='historical-event-time-unavailable'
                    or any(action[k] is not None for k in ('identity','receipt_clock','receipt_wall_seconds'))):
                raise ValueError('missing-result timeout scope mismatch')
            gate=None
        else:
            event=f['terminalEventV2'];action=e['action']
            if (f['status'] not in ('succeeded','aborted','canceled') or event['status']!=f['status']
                    or action['identity']!=event['goal_id']
                    or action['receipt_clock']!=event['receipt_clock']
                    or action['receipt_wall_seconds']!=event['receipt_wall_seconds']
                    or action['event_time_support']!='recorded-client-receipt'):
                raise ValueError('received-result scope mismatch')
            gate=capture_gate(f['trajectory'],f['postResultSecondsObserved'])
        sim_span=raw[-1]['simSeconds']-raw[0]['simSeconds'] if len(raw)>1 else 0.
        wall_span=raw[-1]['wallSeconds']-raw[0]['wallSeconds'] if len(raw)>1 else 0.
        record.update(distance_band=by_id[row['id']]['distance_band'],received_action_result=received,
            coverage_population='received-action-result' if received else 'fixture-timeout-without-result',
            raw_post_samples=len(raw),raw_sim_span_seconds=sim_span if received else None,
            raw_wall_span_seconds=wall_span if received else None,post_result_wall_observed=f['postResultSecondsObserved'],
            worker_average_real_time_factor=w['realTimeFactor'],raw_to_packet_clock_inventory_exact=True,
            dwell_seconds=e['task']['dwell_s'],raw_sim_span_shorter_than_dwell=sim_span<e['task']['dwell_s'] if received else None,
            contact_evidence_present='contacts' in e,contact_support=cert['component_support']['contact'],
            hypothetical_v28_gate_on_original_capture=gate)
        results.append(record)
    valid=[r for r in results if r['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT']
    received=[r for r in valid if r['received_action_result']]
    return {'schema':'roboboat-development-post-result-coverage-audit/v33','profile':binding(profile_path),
        'dependencies':dependencies,'rows':results,'scheduled_denominator':len(results),
        'valid_recordings':len(valid),'complete_geometry_pairs_in_profile':p['complete_geometry_pairs'],
        'received_result_recordings':len(received),'fixture_timeout_without_result_recordings':len(valid)-len(received),
        'received_result_complete_sampled_window_counts':dict(Counter(str(r['complete_sampled_window']) for r in received)),
        'complete_sampled_window_recording_counts':dict(Counter(str(r['complete_sampled_window']) for r in valid)),
        'raw_span_shorter_than_dwell_recording_count':sum(r['raw_sim_span_shorter_than_dwell'] for r in received),
        'raw_span_shorter_than_dwell_denominator':len(received),
        'contact_support_recording_counts':dict(Counter(r['contact_support'] for r in valid)),
        'task_support_recording_counts':p['L2_sampled_task_recording_counts'],
        'raw_to_packet_clock_inventory_all_exact':all(r['raw_to_packet_clock_inventory_exact'] for r in valid),
        'scope':'Recording-level exploratory measurement audit; every fixed scheduled disposition retained. Missing-result fixture timeouts have no post-result span or hypothetical received-result gate and are excluded from that denominator. Raw-to-packet clock equality means simulator-header stamps only; packets do not expose per-sample wall time. Hypothetical diagnostics do not alter admissions or establish candidate runtime behavior. No ROS cancellation completion, method score, causal mechanism, endpoint effect, power estimate or new independent N.',
        'source_judges_qualified':False,'confirmation_n':0,'replication_n':0,'independent_n_added':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--profile',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();target=Path(a.output)
    if target.exists():raise FileExistsError('immutable coverage audit required')
    r=audit(a.profile);target.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({k:r[k] for k in ('valid_recordings','raw_span_shorter_than_dwell_recording_count','raw_to_packet_clock_inventory_all_exact','independent_n_added')}))
