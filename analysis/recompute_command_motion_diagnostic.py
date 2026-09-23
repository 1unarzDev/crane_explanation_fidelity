#!/usr/bin/env python3
"""Recompute the command-motion diagnosis from a blind robot-visible method input."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"
sys.path.insert(0, str(CORE))

from crane_explain.diagnostics import (  # noqa: E402
    CommandMotionObservation,
    CommandMotionWindow,
    diagnose_command_motion_discrepancy,
    render_diagnostic,
    verify_diagnostic_text,
)


FORBIDDEN = {"diagnostic_result", "final_answer", "final_text_verification"}


def method_input_from_export(export: dict[str, Any]) -> dict[str, Any]:
    if export.get("schema") != "crane-command-motion-diagnostic-export-v1":
        raise ValueError("unsupported command-motion export schema")
    if export.get("visibility") != "robot_visible":
        raise ValueError("command-motion export is not robot-visible")
    return {
        "schema": "crane-command-motion-method-input-v1",
        "episode_id": export["episode_id"],
        "visibility": "robot_visible",
        "source": export["source"],
        "method_input": export["method_input"],
        "evidence_boundary": export["evidence_boundary"],
    }


def _windows(method: dict[str, Any]) -> tuple[CommandMotionWindow, ...]:
    config = method["windowing"]
    window_seconds = float(config["window_seconds"])
    duration = float(method["analysis_duration_s"])
    count = max(0, math.ceil(duration / window_seconds))
    commands = method.get("command_samples") or []
    odometry = method.get("odometry_samples") or []
    result = []
    for index in range(count):
        start = index * window_seconds
        end = start + window_seconds
        command_values = [
            float(item["planar_speed_mps"])
            for item in commands
            if start <= float(item["offset_s"]) < end
        ]
        odometry_values = [
            float(item["planar_speed_mps"])
            for item in odometry
            if start <= float(item["offset_s"]) < end
        ]
        result.append(
            CommandMotionWindow(
                index=index,
                start_offset_s=start,
                end_offset_s=end,
                command_sample_count=len(command_values),
                odometry_sample_count=len(odometry_values),
                median_commanded_planar_speed_mps=(
                    statistics.median(command_values) if command_values else None
                ),
                median_measured_planar_speed_mps=(
                    statistics.median(odometry_values) if odometry_values else None
                ),
            )
        )
    return tuple(result)


def build_result(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("schema") != "crane-command-motion-method-input-v1":
        raise ValueError("unsupported command-motion method-input schema")
    if payload.get("visibility") != "robot_visible":
        raise ValueError("method input is not robot-visible")
    leaked = FORBIDDEN.intersection(payload)
    if leaked:
        raise ValueError(f"precomputed diagnostic fields are forbidden: {sorted(leaked)}")
    source = payload["source"]
    method = payload["method_input"]
    config = method["windowing"]
    sequence = method["execution_sequence"]
    computation_version = str(
        method.get("diagnostic_computation_version", "command-motion-discrepancy-v1")
    )
    if computation_version not in {
        "command-motion-discrepancy-v1",
        "command-motion-discrepancy-v2",
    }:
        raise ValueError("unsupported command-motion computation version")
    hashes = {
        "events": str(source["events_sha256"]),
        "runtime-manifest": str(source["runtime_manifest_sha256"]),
        "bt-policy": str(source["bt_policy_sha256"]),
        "nav2-config": str(source["nav2_config_sha256"]),
    }
    if any(len(value) != 64 for value in hashes.values()):
        raise ValueError("source SHA-256 values must be present")
    classifier = sequence["recovery_node_classifier"]
    if classifier.get("policy_sha256") != hashes["bt-policy"]:
        raise ValueError("recovery classifier policy hash does not match retained BT source")
    if classifier.get("classifier_rule") != "Wait:IDLE->RUNNING":
        raise ValueError("unsupported recovery classifier rule")
    observation = CommandMotionObservation(
        episode_id=str(payload["episode_id"]),
        evidence_ids=tuple(f"{name}-sha256:{value}" for name, value in hashes.items()),
        command_frame=str(method["command_frame"]),
        measured_frame=str(method["measured_frame"]),
        action_status=str(method["action_status"]),
        windows=_windows(method),
        raw_command_sample_count=len(method.get("command_samples") or ()),
        raw_odometry_sample_count=len(method.get("odometry_samples") or ()),
        window_seconds=float(config["window_seconds"]),
        minimum_command_samples_per_window=int(
            config["minimum_command_samples_per_window"]
        ),
        minimum_odometry_samples_per_window=int(
            config["minimum_odometry_samples_per_window"]
        ),
        calibration_window_count=int(config["calibration_window_count"]),
        minimum_commanded_speed_mps=float(config["minimum_commanded_speed_mps"]),
        minimum_healthy_measured_speed_mps=float(
            config["minimum_healthy_measured_speed_mps"]
        ),
        maximum_discrepancy_response_ratio=float(
            config["maximum_discrepancy_response_ratio"]
        ),
        minimum_consecutive_discrepancy_windows=int(
            config["minimum_consecutive_discrepancy_windows"]
        ),
        follow_path_failure_count=int(sequence["follow_path_failure_count"]),
        follow_path_attempt_count=int(sequence["follow_path_attempt_count"]),
        source_qualified_recovery_count=int(
            sequence["source_qualified_wait_recovery_count"]
        ),
        source_anchor_ids=(
            f"bt-policy-sha256:{hashes['bt-policy']}",
            f"nav2-config-sha256:{hashes['nav2-config']}",
        ),
        computation_version=computation_version,
    )
    result = diagnose_command_motion_discrepancy(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    if not verification.accepted:
        raise RuntimeError("checked deterministic rendering failed verification")
    return {
        "schema": "crane-command-motion-recomputed-diagnostic-v1",
        "episode_id": observation.episode_id,
        "visibility": "robot_visible",
        "diagnostic_result": json.loads(json.dumps(result.to_dict())),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": True,
            "policy": "exact-checked-deterministic-rendering",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = build_result(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
