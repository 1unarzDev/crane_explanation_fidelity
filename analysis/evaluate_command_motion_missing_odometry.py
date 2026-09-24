#!/usr/bin/env python3
"""Independently reference a command-motion case with measured motion withheld."""

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
    method = export["method_input"]
    commands = method.get("command_samples") or []
    odometry = method.get("odometry_samples") or []
    if not commands:
        raise ValueError("masked reference requires retained command samples")
    if odometry:
        raise ValueError("masked reference requires independently measured motion to be absent")
    sequence = method["execution_sequence"]
    return {
        "schema": "crane-command-motion-missing-odometry-reference-v1",
        "status": "INDEPENDENT_DEVELOPMENT_REFERENCE_NOT_HUMAN_GOLD",
        "visibility": "evaluator_only",
        "episode_id": export["episode_id"],
        "input": {
            "path": source_path.as_posix(),
            "sha256": sha256(source_path),
        },
        "independent_of_proposed_diagnostic_result": True,
        "observations": {
            "delivered_command_sample_count": len(commands),
            "independent_odometry_sample_count": 0,
            "action_status": method["action_status"],
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
            "The missing independently measured motion samples prevent a time-aligned command-to-motion comparison.",
            "The retained action aborted after three FollowPath attempts, two failures, and two source-qualified Wait recovery invocations.",
            "The execution sequence alone does not establish a command-to-motion discrepancy or unique physical cause.",
            "The next discriminating check is synchronized independent motion evidence.",
        ],
        "prohibited_claims": [
            "A sustained command-to-motion discrepancy occurred in the masked evidence.",
            "The delivered commands were proven accepted or applied by an actuator.",
            "Motor failure, slip, collision, obstruction, or an evaluator intervention caused the outcome.",
            "The paired unmasked diagnosis is available to an ordinary explanation method.",
        ],
        "statistical_cluster_id": "command-motion-held-nominal-pair-001",
        "independent_scenario_increment": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_reference(payload, args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
