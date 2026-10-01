"""Development equal-evidence packets from independently recorded channels.

Legacy callback replay remains unchanged. Motion is masked before numeric
derivation. Hidden scenario/seed metadata is never read to build packets.
"""
import sys
from pathlib import Path

from .navigation_context import QUESTIONS, project
from .motion_context import extend as motion_extend


def build(events, motion_events, question_id, condition):
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
    return packet, dict(legacy_closure=closure, packet_sha256=canonical_sha256(packet),
                        motion_mask_applied_before_summary=True,
                        phase='development_only',method_calls=0,judge_calls=0)
