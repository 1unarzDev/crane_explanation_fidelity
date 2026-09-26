from __future__ import annotations

import json
from pathlib import Path

from analysis.build_focused_command_motion_reference import build_focused_reference


ROOT = Path(__file__).parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def test_persistent_reference_binds_only_question_essential_units():
    reference = build_focused_reference(
        load("data/robot_visible/dev/cm-land-conf-042/command-motion-diagnostic-v3.json"),
        load("data/evaluator_only/dev/cm-land-conf-042/command-motion-independent-reference-v1.json"),
        question_id="focused:persistent:dry-run",
    )
    ids = [item["unit_id"] for item in reference["required_units"]]
    assert ids == [
        "mechanism-command-motion-response",
        "healthy-and-event-comparison",
        "action-outcome",
        "causal-limit",
    ]
    assert reference["complete_endpoint_unit_ids"] == ids
    assert reference["primary_endpoint_eligible"] is True
    assert "next-check" not in ids


def test_recovery_reference_requires_recovered_measurement_and_order_limit():
    reference = build_focused_reference(
        load("data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json"),
        load("data/evaluator_only/dev/cm-land-conf-043/command-motion-independent-reference-v1.json"),
        question_id="focused:recovery:dry-run",
    )
    ids = [item["unit_id"] for item in reference["required_units"]]
    assert "measured-response-recovery" in ids
    assert "causal-limit" in ids
    assert reference["complete_endpoint_unit_ids"] == ids
