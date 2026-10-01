"""Development equal-evidence packets from independently recorded channels.

Legacy callback replay remains unchanged. Motion is masked before numeric
derivation. Hidden scenario/seed metadata is never read to build packets.
"""
import sys
from pathlib import Path

from .navigation_context import QUESTIONS, project
from .motion_context import extend as motion_extend


def build(events, motion_events, question_id, condition, use_observed_action_window=False, controller_snapshots=None):
    # Historical modules use repository-local absolute imports. Resolve that
    # existing interface without editing the preserved development pipeline.
    legacy = str(Path(__file__).resolve().parents[1])
    if legacy not in sys.path:
        sys.path.insert(0, legacy)
    from study_v2 import build_packet
    from evidence_calibration_io import canonical_sha256
    packet, _, closure = build_packet(events, QUESTIONS[question_id], condition)
    packet = project(packet, question_id)
    packet = motion_extend(packet, motion_events, condition)
    if use_observed_action_window:
        from .action_window import odometry_summary
        observed=odometry_summary(motion_events,condition)
        packet['evidence']['odometry_observation']=observed['odometry_observation']
        packet['availability']['odometry_observation']=observed['availability']
        # Observed software boundaries are outcome context and remain present
        # under diagnostic removal; they are not hidden scenario references.
        window=observed['observed_action_window']
        packet['evidence']['observed_action_window']=[] if window is None else [
            dict(evidence_id='observed-navigation-window',**window)]
        packet['availability']['observed_action_window']='present' if window else 'unavailable'
        packet['source_context']['motion_window_scope']=(
            'Odometry is restricted to recorded simulated ROS stamps within '
            'instrumented driver observations of acceptance-to-result/disposition. '
            'The recorded sample extent, boundary gaps and maximum internal gap '
            'remain explicit. Driver observations are software protocol evidence, '
            'not physical arrival. Command summaries retain their recording '
            'scope; no receipt-clock conversion or TF transform is inferred.')
    if controller_snapshots is not None:
        from .controller_context import extend as controller_extend
        packet=controller_extend(packet,controller_snapshots,condition)
    return packet, dict(legacy_closure=closure, packet_sha256=canonical_sha256(packet),
                        motion_mask_applied_before_summary=True,
                        observed_action_window_projection=use_observed_action_window,
                        phase='development_only',method_calls=0,judge_calls=0)
