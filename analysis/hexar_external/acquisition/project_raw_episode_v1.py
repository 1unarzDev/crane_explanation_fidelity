"""Read-only deterministic query/reference closure; no semantic method calls."""
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
from ..confirmatory_v1.journal import fingerprint


def review(folder,episode_id,events,motion):
    folder=Path(folder)
    result=dict(development_id=episode_id,candidate_integrity=False,error=None)
    packets=[]
    try:
        report=audit(folder)
        if not report['bag_integrity_passed']:raise ValueError(str(report['issues']))
        snapshots=[json.loads((folder/f'controller_{b}.json').read_text())['snapshot'] for b in ('start','end')]
        for snapshot in snapshots:validate(snapshot)
        window=observed_window(motion)
        if window is None or not timestamp(snapshots[0]['stamp'])<window['start_stamp_ns']<window['end_stamp_ns']<timestamp(snapshots[1]['stamp']):
            raise ValueError('original controller snapshots must bracket action')
        events_raw=(json.dumps(events,indent=2)+'\n').encode()
        motion_raw=(json.dumps(motion,indent=2)+'\n').encode()
        result.update(candidate_integrity=True,bag_integrity=report,
            snapshots_equal_except_stamp=snapshots[0]['parameters']==snapshots[1]['parameters'] and snapshots[0]['subscribers']==snapshots[1]['subscribers'] and snapshots[0]['publishers']==snapshots[1]['publishers'],
            observed_action_window=window,files={'events_development.json':hashlib.sha256(events_raw).hexdigest(),
                'motion_events_v3.json':hashlib.sha256(motion_raw).hexdigest(),
                **{f'controller_{b}.json':hashlib.sha256((folder/f'controller_{b}.json').read_bytes()).hexdigest() for b in ('start','end')}},
            parameter_events_optional_observed_count=report['counts'].get('/parameter_events',0),
            parameter_event_scope='Optional infrastructure channel; absence remains unknown, and presence does not prove complete event delivery or continuous configuration stability.',
            observed_mux_output_messages=report['counts'].get('/mobile_base_controller/cmd_vel_unstamped',0),
            absent_mux_commands_used_as_exclusion=False)
        for query in QUESTIONS:
            trio=[]
            for condition in ('intact','irrelevant_removal','diagnostic_removal'):
                packet,closure=build(events,motion,query,condition,True,snapshots)
                refs=reference(packet)
                project(packet,refs,'Development projection integrity probe.')
                item=dict(development_id=episode_id,question_id=query,condition=condition,
                          method_packet=packet,packet_sha256=fingerprint(packet),closure=closure,reference=refs)
                trio.append(item);packets.append(item)
            if trio[0]['method_packet']!=trio[1]['method_packet']:raise ValueError('irrelevant removal changed visible packet')
            if trio[2]['method_packet']['source_context']['controller_runtime_observations']:
                raise ValueError('diagnostic removal leaked observed controller context')
    except Exception as exc:
        result.update(candidate_integrity=False,error=type(exc).__name__+': '+str(exc))
        packets=[]
    return dict(episode=result,packets=packets,method_or_judge_calls=0,original_capture_mutated=False,
                identity_key_note='development_id is a preserved compatibility field; phase/eligibility comes from bound acquisition provenance.')
