"""Offline compatibility checks for the prospective neutral-input non-rank options."""

from __future__ import annotations

from build_evidence_calibration_agent_qualification import LEVELS
from build_evidence_calibration_neutral_level_suite_v2 import NON_RANK_OPTIONS
from evidence_calibration_neutral_level_qualification import (
    aggregate,
    packet_for as legacy_packet_for,
    score_return as legacy_score_return,
)


def packet_for(case: dict, slot: str, suite_hash: str) -> dict:
    if case["form"]["abstraction_level_options"] != [*LEVELS, *NON_RANK_OPTIONS]:
        raise ValueError("non-rank options must be uniform and separate from the six diagnostic levels")
    return legacy_packet_for(case, slot, suite_hash)


def score_return(case: dict, returned: dict, *, slot: str, suite_hash: str) -> dict:
    packet_for(case, slot, suite_hash)
    # Reuse the unchanged field scorer; neither sentinels nor diagnostic ranks earn credit.
    return legacy_score_return(case, returned, slot=slot, suite_hash=suite_hash)
