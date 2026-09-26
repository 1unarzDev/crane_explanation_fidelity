#!/usr/bin/env python3
"""Independently reference a paired missing-odometry evidence condition."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_reference(
    export: dict[str, Any], source_path: Path, *, cluster_id: str
) -> dict[str, Any]:
    if export.get("schema") != "crane-command-motion-diagnostic-export-v1":
        raise ValueError("unsupported command-motion export schema")
    if export.get("visibility") != "robot_visible":
        raise ValueError("reference input is not robot-visible")
    mask = export.get("evidence_mask") or {}
    if mask.get("mask_id") != "missing-independent-odometry-samples-v1":
        raise ValueError("unexpected paired ambiguity mask")
    if mask.get("independent_scenario_increment") != 0:
        raise ValueError("missing-odometry condition is not paired within its source cluster")
    if mask.get("paired_source_available_to_methods") is not False:
        raise ValueError("paired source availability is not fail-closed")
    if not cluster_id.strip():
        raise ValueError("source cluster ID is required")

    method = export["method_input"]
    commands = method.get("command_samples") or []
    odometry = method.get("odometry_samples") or []
    if not commands:
        raise ValueError("masked reference requires retained command samples")
    if odometry:
        raise ValueError("masked reference requires delivered odometry to be absent")
    sequence = method["execution_sequence"]
    attempts = int(sequence["follow_path_attempt_count"])
    failures = int(sequence["follow_path_failure_count"])
    recoveries = int(sequence["source_qualified_wait_recovery_count"])
    status = str(method["action_status"])
    return {
        "schema": "crane-command-motion-paired-missing-odometry-reference/v1",
        "status": "DEVELOPMENT_PAIRED_REFERENCE_NO_SEMANTIC_LABEL",
        "visibility": "evaluator_only",
        "episode_id": str(export["episode_id"]),
        "input": {"path": source_path.as_posix(), "sha256": sha256(source_path)},
        "independent_of_proposed_diagnostic_result": True,
        "observations": {
            "delivered_command_sample_count": len(commands),
            "independent_odometry_sample_count": 0,
            "action_status": status,
            "follow_path_attempt_count": attempts,
            "follow_path_failure_count": failures,
            "source_qualified_wait_recovery_count": recoveries,
        },
        "answerability": {
            "command_motion_discrepancy": "insufficient",
            "recorded_execution_sequence": "answerable",
            "unique_physical_cause": "insufficient",
        },
        "required_propositions": [
            "The missing delivered odometry samples prevent a time-aligned command-to-motion comparison.",
            f"The action {status} after {attempts} FollowPath attempts, {failures} failures, and {recoveries} source-qualified Wait invocations.",
            "The execution sequence alone does not establish a command-to-motion discrepancy or unique physical cause.",
            "The next discriminating check is synchronized measured-motion evidence.",
        ],
        "prohibited_claims": [
            "A sustained command-to-motion discrepancy occurred in the masked evidence.",
            "The delivered commands were proven accepted or applied by an actuator.",
            "Motor failure, slip, collision, obstruction, or an evaluator intervention caused the outcome.",
            "The paired unmasked export is available to an ordinary explanation method.",
        ],
        "statistical_cluster_id": cluster_id,
        "independent_scenario_increment": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--cluster-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    result = build_reference(
        json.loads(args.input.read_text(encoding="utf-8")),
        args.input,
        cluster_id=args.cluster_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
