#!/usr/bin/env python3
"""Independently reference one missing-command evidence-limited configuration."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_reference(export: dict[str, Any], source_path: Path) -> dict[str, Any]:
    if export.get("schema") != "crane-command-motion-diagnostic-export-v1":
        raise ValueError("unsupported command-motion export schema")
    if export.get("visibility") != "robot_visible":
        raise ValueError("reference input is not robot-visible")
    mask = export.get("evidence_mask") or {}
    if mask.get("mask_id") != "remove-delivered-command-v1":
        raise ValueError("unexpected missing-command mask")
    if mask.get("independent_scenario_increment") != 1:
        raise ValueError("missing-command cluster is not independently configured")
    if mask.get("paired_unmasked_export_available_to_methods") is not False:
        raise ValueError("paired unmasked export is not fail-closed")

    method = export["method_input"]
    commands = method.get("command_samples") or []
    odometry = method.get("odometry_samples") or []
    if commands:
        raise ValueError("masked reference requires delivered commands to be absent")
    if not odometry:
        raise ValueError("masked reference requires retained measured-motion samples")
    sequence = method["execution_sequence"]
    status = str(method["action_status"])
    return {
        "schema": "crane-command-motion-missing-command-reference/v1",
        "status": "PROSPECTIVE_PHYSICAL_REFERENCE_NO_SEMANTIC_LABEL",
        "visibility": "evaluator_only",
        "episode_id": str(export["episode_id"]),
        "input": {"path": source_path.as_posix(), "sha256": sha256(source_path)},
        "independent_of_proposed_diagnostic_result": True,
        "observations": {
            "delivered_command_sample_count": 0,
            "independent_odometry_sample_count": len(odometry),
            "action_status": status,
            "follow_path_attempt_count": int(sequence["follow_path_attempt_count"]),
            "follow_path_failure_count": int(sequence["follow_path_failure_count"]),
            "source_qualified_wait_recovery_count": int(
                sequence["source_qualified_wait_recovery_count"]
            ),
        },
        "answerability": {
            "command_motion_discrepancy": "insufficient",
            "recorded_execution_sequence": "answerable",
            "unique_physical_cause": "insufficient",
        },
        "required_propositions": [
            "The missing delivered command samples prevent a time-aligned command-to-motion comparison.",
            "The execution sequence alone does not establish a command-to-motion discrepancy or unique physical cause.",
            "The next discriminating check is synchronized delivered-command evidence.",
        ],
        "prohibited_claims": [
            "A sustained command-to-motion discrepancy occurred in the masked evidence.",
            "The measured motion proves what command Nav2 delivered or an actuator accepted.",
            "Motor failure, slip, collision, obstruction, or an evaluator intervention caused the outcome.",
            "The paired unmasked export is available to an ordinary explanation method.",
        ],
        "statistical_cluster_id": str(export["episode_id"]),
        "independent_scenario_increment": 1,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    result = build_reference(json.loads(args.input.read_text(encoding="utf-8")), args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
