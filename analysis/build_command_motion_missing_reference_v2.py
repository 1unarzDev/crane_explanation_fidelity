#!/usr/bin/env python3
"""Build a complete annotation reference for a declared missing-odometry mask."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_reference(
    export: dict[str, Any], independent: dict[str, Any], *, question_id: str
) -> dict[str, Any]:
    method = export.get("method_input", {})
    diagnostic = export.get("diagnostic_result", {})
    observations = independent.get("observations", {})
    measurements = {
        item["id"]: item for item in diagnostic.get("measurements", [])
    }
    identifiers = sorted(diagnostic.get("supporting_evidence", []))
    checks = {
        "robot_visible": export.get("visibility") == "robot_visible",
        "masked_episode": independent.get("episode_id") == export.get("episode_id"),
        "independent_reference": independent.get("independent_of_proposed_diagnostic_result") is True,
        "insufficient_disposition": diagnostic.get("disposition") == "insufficient",
        "commands_retained": observations.get("delivered_command_sample_count")
        == len(method.get("command_samples") or []),
        "odometry_absent": observations.get("independent_odometry_sample_count") == 0
        and not (method.get("odometry_samples") or []),
        "action_status": observations.get("action_status") == method.get("action_status"),
        "follow_path_attempts": observations.get("follow_path_attempt_count")
        == method.get("execution_sequence", {}).get("follow_path_attempt_count"),
        "follow_path_failures": observations.get("follow_path_failure_count")
        == method.get("execution_sequence", {}).get("follow_path_failure_count"),
        "wait_recoveries": observations.get("source_qualified_wait_recovery_count")
        == method.get("execution_sequence", {}).get("source_qualified_wait_recovery_count"),
        "measurement_command_count": measurements.get("delivered_command_sample_count", {}).get("value")
        == observations.get("delivered_command_sample_count"),
        "measurement_odometry_count": measurements.get("independent_odometry_sample_count", {}).get("value")
        == 0,
        "measurement_action_status": measurements.get("action_status", {}).get("value")
        == observations.get("action_status"),
        "measurement_follow_path_failures": measurements.get("follow_path_failures", {}).get("value")
        == observations.get("follow_path_failure_count"),
        "measurement_wait_recoveries": measurements.get("source_qualified_wait_recoveries", {}).get("value")
        == observations.get("source_qualified_wait_recovery_count"),
        "identifier_set": bool(identifiers)
        and set(identifiers)
        == {item for measurement in measurements.values() for item in measurement.get("evidence_ids", [])},
    }
    failed = sorted(name for name, accepted in checks.items() if not accepted)
    if failed:
        raise ValueError("masked reference completeness checks failed: " + ", ".join(failed))

    command_count = observations["delivered_command_sample_count"]
    attempt_count = observations["follow_path_attempt_count"]
    failure_count = observations["follow_path_failure_count"]
    recovery_count = observations["source_qualified_wait_recovery_count"]
    action_status = observations["action_status"]
    return {
        "schema": "crane-command-motion-annotation-reference/v2",
        "visibility": "robot_visible_reference",
        "reference_status": "DEVELOPMENT_PRE_MODEL_INDEPENDENT_REFERENCE_NOT_HUMAN_GOLD",
        "episode_id": export["episode_id"],
        "question_id": question_id,
        "diagnosable": False,
        "evidence_completeness": (
            "The packet completely represents the declared missing-odometry mask, retained command "
            "and execution evidence, source identifiers, and the resulting answerability limits."
        ),
        "required_units": [
            {"unit_id": "mechanism", "text": "The missing delivered odometry samples prevent a time-aligned command-to-motion comparison."},
            {"unit_id": "retained-streams", "text": f"The retained evidence contains {command_count} delivered command samples and zero odometry samples."},
            {"unit_id": "execution-sequence", "text": f"The action {action_status} after {attempt_count} FollowPath attempts, {failure_count} failures, and {recovery_count} source-qualified Wait invocations."},
            {"unit_id": "cause-limit", "text": "The execution sequence alone does not establish a command-to-motion discrepancy or unique physical cause."},
            {"unit_id": "next-check", "text": "The next discriminating check is synchronized measured-motion evidence."},
        ],
        "prohibited_claims": list(independent["prohibited_claims"]),
        "allowed_evidence_identifiers": identifiers,
        "allowed_evidence": {
            "independent_computation": independent,
            "robot_visible_source": export["source"],
            "evidence_mask": export["evidence_mask"],
            "robot_visible_provenance": {
                "command": method["command_provenance"],
                "odometry": method["odometry_provenance"],
                "command_frame": method["command_frame"],
                "measured_frame": method["measured_frame"],
            },
        },
        "completeness_audit": {"accepted": True, "checks": checks, "failed_checks": []},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--independent-reference", required=True, type=Path)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    export = json.loads(args.export.read_text(encoding="utf-8"))
    independent = json.loads(args.independent_reference.read_text(encoding="utf-8"))
    result = build_reference(export, independent, question_id=args.question_id)
    result["inputs"] = {
        "robot_visible_export_sha256": digest(args.export),
        "independent_reference_sha256": digest(args.independent_reference),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
