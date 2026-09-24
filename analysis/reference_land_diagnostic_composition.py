#!/usr/bin/env python3
"""Independent predicate audit for a bounded land diagnostic composition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _measurement(result: dict[str, Any], measurement_id: str) -> dict[str, Any]:
    matches = [item for item in result["measurements"] if item.get("id") == measurement_id]
    if len(matches) != 1:
        raise ValueError(f"reference expected one measurement: {measurement_id}")
    return matches[0]


def audit(command: dict[str, Any], geometry: dict[str, Any], composition: dict[str, Any]) -> dict[str, Any]:
    plan = composition["answer_plan"]
    result = command["diagnostic_result"]
    values = {
        item["id"]: item for item in plan["decisive_evidence"]
    }
    expected = {
        "calibrated_healthy_planar_speed": _measurement(result, "calibrated_healthy_planar_speed"),
        "discrepancy_commanded_planar_speed": _measurement(result, "discrepancy_commanded_planar_speed"),
        "discrepancy_measured_planar_speed": _measurement(result, "discrepancy_measured_planar_speed"),
        "sustained_discrepancy_duration": _measurement(result, "sustained_discrepancy_duration"),
    }
    numeric_parity = {
        key: key in values
        and float(values[key]["value"]) == float(source["value"])
        and values[key].get("interval_s") == source.get("interval_s")
        for key, source in expected.items()
    }
    text = composition["final_answer"]
    lowered = text.lower()
    semantic_checks = {
        "primary_mechanism_selected": plan.get("primary_mechanism") == "command_to_motion_discrepancy",
        "command_diagnosis_supported": result.get("disposition") == "supported",
        "geometry_retained_as_insufficient": geometry["diagnostic_result"].get("disposition") == "insufficient"
        and plan["competing_mechanisms"][0].get("disposition") == "insufficient",
        "nonterminal_boundary_retained": "no terminal result was observed" in lowered
        and "eventual action outcome is unresolved" in lowered,
        "no_abort_or_failure_claim": "the action aborted" not in lowered
        and "the action failed" not in lowered,
        "no_geometry_causation": "geometry caused" not in lowered
        and "obstacle caused" not in lowered,
        "no_evaluator_intervention": "mobility hold" not in lowered
        and "evaluator intervention" not in lowered,
        "execution_counts_match": "6 FollowPath failures" in text
        and "1 source-qualified Wait invocation" in text
        and "11 FollowPath attempts" in text,
        "exact_renderer_accepted": composition["final_text_verification"].get("accepted") is True,
    }
    accepted = all(numeric_parity.values()) and all(semantic_checks.values())
    return {
        "schema": "crane-land-diagnostic-composition-independent-reference/v1",
        "status": "DEVELOPMENT_REFERENCE_NOT_CONFIRMATORY",
        "episode_id": composition["episode_id"],
        "accepted": accepted,
        "implementation_independence": {
            "imports_proposed_composer": False,
            "imports_diagnostic_core": False,
            "human_label": False,
        },
        "numeric_parity": numeric_parity,
        "semantic_checks": semantic_checks,
        "allowed_conclusion": (
            "The bounded answer composition preserves the supported command-motion mechanism, "
            "decisive measurements, insufficient geometry, and unresolved terminal outcome."
            if accepted
            else "The bounded answer composition did not pass the independent predicate audit."
        ),
        "limitations": [
            "This is a deterministic predicate audit, not a human semantic judgment.",
            "This inspected development case cannot estimate comparative method performance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command-motion", type=Path, required=True)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--composition", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = audit(
        json.loads(args.command_motion.read_text(encoding="utf-8")),
        json.loads(args.geometry.read_text(encoding="utf-8")),
        json.loads(args.composition.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not payload["accepted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
