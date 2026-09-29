#!/usr/bin/env python3
"""Normalize retained robot-visible command-motion inputs without copying old answers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_calibration_io import canonical_json_bytes


SCHEMA = "crane-normalized-method-evidence/v1"


def normalize(diagnostic: dict[str, Any], *, configuration_id: str, question: str,
              omit_odometry: bool = False) -> dict[str, Any]:
    required = {"schema", "episode_id", "source", "method_input", "diagnostic_result",
                "final_answer", "final_text_verification", "evidence_boundary", "development_only",
                "visibility"}
    if set(diagnostic) != required:
        raise ValueError("unexpected command-motion diagnostic fields")
    if not diagnostic["development_only"]:
        raise ValueError("only retained development diagnostics may be normalized here")
    if diagnostic["visibility"] != "robot_visible":
        raise ValueError("diagnostic is not certified robot-visible")
    method = diagnostic["method_input"]
    required_method = {
        "accepted_goal_record_id", "action_error_code", "action_result_record_id", "action_status",
        "analysis_duration_s", "anchor", "command_frame", "command_provenance", "command_samples",
        "diagnostic_computation_version", "execution_sequence", "goal_id", "measured_frame",
        "odometry_provenance", "odometry_samples", "windowing",
    }
    if set(method) != required_method:
        raise ValueError("unexpected method-input fields")
    if not question.strip() or not configuration_id:
        raise ValueError("question and configuration identity are required")
    measurements = diagnostic["diagnostic_result"]["measurements"]
    evidence = {
        "navigate_to_pose_result": {
            "evidence_ids": ["action-result"], "goal_id": method["goal_id"],
            "accepted_goal_record_id": method["accepted_goal_record_id"],
            "action_result_record_id": method["action_result_record_id"],
            "action_status": method["action_status"], "action_error_code": method["action_error_code"],
        },
        "behavior_tree_transitions": {
            "evidence_ids": ["recovery-trace"], "execution_sequence": method["execution_sequence"],
        },
        "source_anchors": {
            "evidence_ids": ["source-anchors"],
            "bt_policy_sha256": diagnostic["source"]["bt_policy_sha256"],
            "nav2_config_sha256": diagnostic["source"]["nav2_config_sha256"],
            "diagnostic_config_sha256": diagnostic["source"]["diagnostic_config_sha256"],
        },
        "delivered_command_stream": {
            "evidence_ids": ["delivered-command-stream"], "frame": method["command_frame"],
            "provenance": method["command_provenance"], "samples": method["command_samples"],
            "windowing": method["windowing"],
        },
    }
    if not omit_odometry:
        evidence["delivered_odometry_stream"] = {
            "evidence_ids": ["delivered-odometry-stream"], "frame": method["measured_frame"],
            "provenance": method["odometry_provenance"], "samples": method["odometry_samples"],
            "windowing": method["windowing"],
        }
        evidence["command_motion_computation"] = {
            "evidence_ids": ["command-motion-computation"],
            "computation": diagnostic["diagnostic_result"]["computation"],
            "computation_version": diagnostic["diagnostic_result"]["computation_version"],
            "diagnostic_disposition": diagnostic["diagnostic_result"]["disposition"],
            "measurements": measurements,
            "assumptions": diagnostic["diagnostic_result"]["assumptions"],
        }
    return {
        "schema": SCHEMA, "episode_id": diagnostic["episode_id"],
        "configuration_id": configuration_id, "question": question, "evidence": evidence,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--configuration-id", required=True)
    parser.add_argument("--question", required=True)
    parser.add_argument("--omit-odometry", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = normalize(json.loads(args.diagnostic.read_text()), configuration_id=args.configuration_id,
                       question=args.question, omit_odometry=args.omit_odometry)
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
