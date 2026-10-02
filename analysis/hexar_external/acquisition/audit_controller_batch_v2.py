"""Separate v2 technical audit: absent inhibited commands are not exclusions."""
import argparse
import hashlib
import json
from pathlib import Path
from .audit_bag import audit
from .controller_context import validate
from .motion_context import timestamp
from .action_window import observed_window
from .navigation_context import QUESTIONS
from .navigation_packets import build
from .navigation_references import build as reference
from ..confirmatory_v1.rich_blind_projection import project
from ..confirmatory_v1.journal import exclusive_json, fingerprint


def review(plan_path):
    plan=json.loads(plan_path.read_text())
    if plan['phase']!='development' or plan['status']!='DEVELOPMENT_ONLY':
        raise ValueError('development plan only')
    rows=[];packets=[]
    for row in plan['records']:
        folder=plan_path.parent/row['episode_id'];result=dict(development_id=row['episode_id'],candidate_integrity=False,error=None)
        try:
            report=audit(folder)
            if not report['bag_integrity_passed']:raise ValueError(str(report['issues']))
            snapshots=[json.loads((folder/f'controller_{boundary}.json').read_text())['snapshot'] for boundary in ('start','end')]
            for snapshot in snapshots:validate(snapshot)
            events_path=folder/'events_development.json';motion_path=folder/'motion_events_v3.json'
            events=json.loads(events_path.read_text());motion=json.loads(motion_path.read_text())
            window=observed_window(motion)
            if window is None or not timestamp(snapshots[0]['stamp']) < window['start_stamp_ns'] < window['end_stamp_ns'] < timestamp(snapshots[1]['stamp']):
                raise ValueError('observed snapshots must bracket recorded action boundaries')
            if report['counts'].get('/parameter_events',0)<2:
                raise ValueError('parameter event transport messages unavailable')
            result.update(candidate_integrity=True,bag_integrity=report,
                          snapshots_equal_except_stamp=snapshots[0]['parameters']==snapshots[1]['parameters'] and snapshots[0]['subscribers']==snapshots[1]['subscribers'] and snapshots[0]['publishers']==snapshots[1]['publishers'],
                          observed_action_window=window,
                          files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [events_path,motion_path,folder/'controller_start.json',folder/'controller_end.json']},
                          parameter_event_scope='transport presence only; no proof all mux changes were delivered',
                          observed_mux_output_messages=report['counts'].get('/mobile_base_controller/cmd_vel_unstamped',0),
                          absent_mux_commands_used_as_exclusion=False)
            local=[]
            for query in QUESTIONS:
                trio=[]
                for condition in ('intact','irrelevant_removal','diagnostic_removal'):
                    packet,closure=build(events,motion,query,condition,True,snapshots)
                    refs=reference(packet)
                    project(packet,refs,'Development projection integrity probe.')
                    item=dict(development_id=row['episode_id'],question_id=query,condition=condition,
                              method_packet=packet,packet_sha256=fingerprint(packet),closure=closure,
                              reference=refs)
                    trio.append(item);local.append(item)
                if trio[0]['method_packet']!=trio[1]['method_packet']:raise ValueError('irrelevant removal changed visible packet')
                if trio[2]['method_packet']['source_context']['controller_runtime_observations']:
                    raise ValueError('diagnostic removal leaked observed controller context')
            packets.extend(local)
        except Exception as failure:result.update(candidate_integrity=False,error=f'{type(failure).__name__}: {failure}')
        rows.append(result)
    return dict(schema='hexar-controller-boundary-development-batch/v2',phase='development_only',
                status='CANDIDATE_INTEGRITY_PASSED_NOT_FULL_QUALIFICATION' if all(r['candidate_integrity'] for r in rows) else 'FAILED_RETAINED',
                confirmatory_N=0,alpha_consumed=0,episode_n=len(rows),packets=packets,episodes=rows,
                plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),
                audit_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                prior_audit_preserved=True,revision="Absent commands may be legitimate under inhibition; do not require motion/command outcomes for technical admission.",
                method_or_judge_calls=0,full_acquisition_qualified=False,
                physical_cause_claim_qualified=False,continuous_parameter_stability_qualified=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    report=review(args.plan);exclusive_json(args.output,report)
    print(report['status'],len(report['packets']))
