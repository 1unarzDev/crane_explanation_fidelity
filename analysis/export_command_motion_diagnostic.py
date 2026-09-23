#!/usr/bin/env python3
"""Export a blind, robot-visible command-to-motion diagnostic input and checked answer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


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


CONFIG = {
    "window_seconds": 1.0,
    "minimum_command_samples_per_window": 5,
    "minimum_odometry_samples_per_window": 20,
    "calibration_window_count": 5,
    "minimum_commanded_speed_mps": 0.4,
    "minimum_healthy_measured_speed_mps": 0.1,
    "maximum_discrepancy_response_ratio": 0.2,
    "minimum_consecutive_discrepancy_windows": 3,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_robot_visible(path: Path, label: str) -> None:
    parts = path.resolve().parts
    if "evaluator_only" in parts or "robot_visible" not in parts:
        raise ValueError(f"{label} must be inside a robot_visible data boundary")


def _planar(vector: dict[str, Any]) -> float:
    return math.hypot(float(vector["x"]), float(vector["y"]))


def _artifact(runtime: dict[str, Any], role: str) -> dict[str, Any]:
    matches = [item for item in runtime.get("artifacts", ()) if item.get("role") == role]
    if len(matches) != 1:
        raise ValueError(f"runtime manifest must declare exactly one {role} artifact")
    item = matches[0]
    if item.get("byte_identical_to_git_object") is not True:
        raise ValueError(f"{role} was not proven byte-identical to its source object")
    return item


def _load_events(path: Path) -> list[tuple[int, dict[str, Any]]]:
    records = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if line.strip():
                records.append((line_number, json.loads(line)))
    if not records or records[0][1].get("type") != "capture_started":
        raise ValueError("event stream does not start with capture_started")
    if records[-1][1].get("type") != "capture_stopped":
        raise ValueError("event stream does not end with capture_stopped")
    return records


def _windows(
    command_samples: list[dict[str, Any]],
    odometry_samples: list[dict[str, Any]],
    end_offset_s: float,
) -> tuple[CommandMotionWindow, ...]:
    count = max(0, math.ceil(end_offset_s / float(CONFIG["window_seconds"])))
    windows = []
    for index in range(count):
        start = index * float(CONFIG["window_seconds"])
        end = start + float(CONFIG["window_seconds"])
        commands = [
            float(item["planar_speed_mps"])
            for item in command_samples
            if start <= float(item["offset_s"]) < end
        ]
        odometry = [
            float(item["planar_speed_mps"])
            for item in odometry_samples
            if start <= float(item["offset_s"]) < end
        ]
        windows.append(
            CommandMotionWindow(
                index=index,
                start_offset_s=start,
                end_offset_s=end,
                command_sample_count=len(commands),
                odometry_sample_count=len(odometry),
                median_commanded_planar_speed_mps=(
                    statistics.median(commands) if commands else None
                ),
                median_measured_planar_speed_mps=(
                    statistics.median(odometry) if odometry else None
                ),
            )
        )
    return tuple(windows)


def _source_qualified_wait_policy(bt_xml: Path) -> dict[str, Any]:
    tree = ET.parse(bt_xml)
    recovery_nodes = list(tree.getroot().iter("RecoveryNode"))
    if len(recovery_nodes) != 1:
        raise ValueError("expected exactly one RecoveryNode in retained BT policy")
    children = list(recovery_nodes[0])
    if len(children) != 2:
        raise ValueError("retained RecoveryNode must have exactly primary and recovery children")
    waits = list(children[1].iter("Wait"))
    if len(waits) != 1:
        raise ValueError("expected exactly one Wait leaf in the RecoveryNode recovery child")
    return {
        "classifier_basis": "retained_bt_recovery_child_exact_node_name",
        "classifier_rule": "Wait:IDLE->RUNNING",
        "node_name": "Wait",
        "tree_path": "RecoveryNode/recovery_child/Sequence/Wait",
        "number_of_retries": int(recovery_nodes[0].attrib["number_of_retries"]),
        "policy_sha256": sha256(bt_xml),
    }


def export(
    events_path: Path,
    capture_manifest_path: Path,
    runtime_manifest_path: Path,
    bt_xml_path: Path,
    nav2_config_path: Path,
    *,
    episode_id: str,
) -> dict[str, Any]:
    for label, path in (
        ("events", events_path),
        ("capture manifest", capture_manifest_path),
        ("runtime manifest", runtime_manifest_path),
        ("behavior-tree XML", bt_xml_path),
    ):
        _require_robot_visible(path, label)
    lowered_episode_id = episode_id.lower()
    if any(token in lowered_episode_id for token in ("hold", "fault", "intervention")):
        raise ValueError("method-visible episode ID must not encode evaluator intervention identity")

    capture = json.loads(capture_manifest_path.read_text(encoding="utf-8"))
    runtime = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    if capture.get("schema") != "crane-explain-ros-capture/v1":
        raise ValueError("unsupported capture manifest schema")
    if runtime.get("schema") != "crane-runtime-provenance/v1":
        raise ValueError("unsupported runtime manifest schema")
    if capture.get("runtime_manifest_sha256") != sha256(runtime_manifest_path):
        raise ValueError("runtime manifest hash does not match capture manifest")
    if capture.get("bt_xml_sha256") != sha256(bt_xml_path):
        raise ValueError("BT XML hash does not match capture manifest")
    bt_artifact = _artifact(runtime, "behavior_tree_xml")
    nav2_artifact = _artifact(runtime, "nav2_parameter_file")
    if bt_artifact.get("content_sha256") != sha256(bt_xml_path):
        raise ValueError("BT XML hash does not match runtime source provenance")
    if nav2_artifact.get("content_sha256") != sha256(nav2_config_path):
        raise ValueError("Nav2 configuration hash does not match runtime source provenance")
    if runtime.get("run_id") != capture.get("run_id"):
        raise ValueError("capture and runtime run IDs do not match")

    records = _load_events(events_path)
    goal_events = [
        (line, item["event"])
        for line, item in records
        if item.get("type") == "harness_event"
        and item.get("event", {}).get("type") == "navigate_to_pose_goal"
        and item.get("event", {}).get("accepted") is True
    ]
    result_events = [
        (line, item["event"])
        for line, item in records
        if item.get("type") == "harness_event"
        and item.get("event", {}).get("type") == "navigate_to_pose_result"
    ]
    if len(goal_events) != 1 or len(result_events) != 1:
        raise ValueError("expected exactly one accepted goal and one action result")
    goal_line, goal = goal_events[0]
    result_line, action_result = result_events[0]
    if goal.get("goal_id") != action_result.get("goal_id"):
        raise ValueError("goal and result IDs do not match")
    goal_ns = int(goal["wall_time_ns"])
    result_ns = int(action_result["wall_time_ns"])
    if result_ns <= goal_ns:
        raise ValueError("action result does not follow accepted goal")

    raw_commands = []
    raw_odometry = []
    transitions = []
    for line, item in records:
        record_type = item.get("type")
        if record_type == "nav2_command":
            if item.get("provenance") != "delivered-nav2-command-not-proof-of-actuator-acceptance":
                raise ValueError("unexpected Nav2 command provenance semantics")
            stamp_ns = int(item["received_wall_time_ns"])
            if goal_ns <= stamp_ns <= result_ns:
                raw_commands.append((line, stamp_ns, _planar(item["linear_mps"])))
        elif record_type == "measured_odometry":
            if item.get("provenance") != "delivered-odometry-not-proof-of-nav2-consumption":
                raise ValueError("unexpected measured odometry provenance semantics")
            stamp_ns = int(item["received_wall_time_ns"])
            if goal_ns <= stamp_ns <= result_ns:
                raw_odometry.append(
                    (line, stamp_ns, _planar(item["linear_velocity_mps"]), str(item["frame_id"]))
                )
        elif record_type == "bt_transition":
            stamp = item["event_stamp"]
            stamp_ns = int(stamp["sec"]) * 1_000_000_000 + int(stamp["nanosec"])
            if goal_ns <= stamp_ns <= result_ns:
                transitions.append((line, item))

    active = [item for item in raw_commands if item[2] >= CONFIG["minimum_commanded_speed_mps"]]
    anchor_ns = active[0][1] if active else goal_ns
    command_samples = [
        {
            "record_id": f"events.jsonl#line:{line}",
            "offset_s": (stamp_ns - anchor_ns) / 1_000_000_000.0,
            "planar_speed_mps": speed,
        }
        for line, stamp_ns, speed in raw_commands
        if stamp_ns >= anchor_ns
    ]
    odometry_samples = [
        {
            "record_id": f"events.jsonl#line:{line}",
            "offset_s": (stamp_ns - anchor_ns) / 1_000_000_000.0,
            "planar_speed_mps": speed,
        }
        for line, stamp_ns, speed, _ in raw_odometry
        if stamp_ns >= anchor_ns
    ]
    end_offset_s = max(0.0, (result_ns - anchor_ns) / 1_000_000_000.0)
    windows = _windows(command_samples, odometry_samples, end_offset_s)
    policy = _source_qualified_wait_policy(bt_xml_path)
    follow_failures = sum(
        item.get("node_name") == "FollowPath"
        and item.get("previous_status") == "RUNNING"
        and item.get("current_status") == "FAILURE"
        for _, item in transitions
    )
    follow_attempts = sum(
        item.get("node_name") == "FollowPath"
        and item.get("previous_status") == "IDLE"
        and item.get("current_status") == "RUNNING"
        for _, item in transitions
    )
    wait_recoveries = sum(
        item.get("node_name") == policy["node_name"]
        and f"{item.get('node_name')}:{item.get('previous_status')}->{item.get('current_status')}"
        == policy["classifier_rule"]
        for _, item in transitions
    )
    event_sha = sha256(events_path)
    runtime_sha = sha256(runtime_manifest_path)
    bt_sha = sha256(bt_xml_path)
    nav2_sha = sha256(nav2_config_path)
    measured_frames = {item[3] for item in raw_odometry}
    if len(measured_frames) > 1:
        raise ValueError("measured odometry frame changed during the goal")
    observation = CommandMotionObservation(
        episode_id=episode_id,
        evidence_ids=(
            f"events-sha256:{event_sha}",
            f"runtime-manifest-sha256:{runtime_sha}",
            f"bt-policy-sha256:{bt_sha}",
            f"nav2-config-sha256:{nav2_sha}",
        ),
        command_frame="base_link-command-convention",
        measured_frame=next(iter(measured_frames), "unknown"),
        action_status=str(action_result["status"]),
        windows=windows,
        raw_command_sample_count=len(command_samples),
        raw_odometry_sample_count=len(odometry_samples),
        follow_path_failure_count=follow_failures,
        follow_path_attempt_count=follow_attempts,
        source_qualified_recovery_count=wait_recoveries,
        source_anchor_ids=(
            f"bt-policy-sha256:{bt_sha}",
            f"nav2-config-sha256:{nav2_sha}",
        ),
        **CONFIG,
    )
    result = diagnose_command_motion_discrepancy(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    if not verification.accepted:
        raise RuntimeError("deterministic command-motion rendering failed verification")

    return {
        "schema": "crane-command-motion-diagnostic-export-v1",
        "episode_id": episode_id,
        "visibility": "robot_visible",
        "development_only": True,
        "source": {
            "events_sha256": event_sha,
            "runtime_manifest_sha256": runtime_sha,
            "bt_policy_sha256": bt_sha,
            "nav2_config_sha256": nav2_sha,
            "bt_repository_commit": bt_artifact["repository_commit"],
            "bt_repository_path": bt_artifact["repository_path"],
            "nav2_repository_commit": nav2_artifact["repository_commit"],
            "nav2_repository_path": nav2_artifact["repository_path"],
        },
        "method_input": {
            "accepted_goal_record_id": f"events.jsonl#line:{goal_line}",
            "action_result_record_id": f"events.jsonl#line:{result_line}",
            "goal_id": str(goal["goal_id"]),
            "action_status": str(action_result["status"]),
            "action_error_code": int(action_result["error_code"]),
            "anchor": "first command at or above minimum_commanded_speed_mps after accepted goal",
            "analysis_duration_s": end_offset_s,
            "command_frame": observation.command_frame,
            "measured_frame": observation.measured_frame,
            "command_provenance": "delivered-nav2-command-not-proof-of-actuator-acceptance",
            "odometry_provenance": "delivered-odometry-not-proof-of-nav2-consumption",
            "command_samples": command_samples,
            "odometry_samples": odometry_samples,
            "windowing": dict(CONFIG),
            "execution_sequence": {
                "follow_path_failure_count": follow_failures,
                "follow_path_attempt_count": follow_attempts,
                "source_qualified_wait_recovery_count": wait_recoveries,
                "recovery_node_classifier": policy,
            },
        },
        "diagnostic_result": result.to_dict(),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "policy": "exact-checked-deterministic-rendering",
        },
        "evidence_boundary": {
            "included": [
                "delivered Nav2 command samples",
                "independently delivered planar odometry samples",
                "NavigateToPose goal/result status",
                "goal-scoped BehaviorTreeLog transitions",
                "hash-checked BT policy and Nav2 configuration",
                "bounded recovery-node classifier derivation",
            ],
            "excluded": [
                "acquisition run identifiers that encode the evaluator intervention",
                "evaluator-only intervention identity or timing",
                "simulator truth and collision state",
                "proof of actuator command acceptance",
                "proof that Nav2 consumed delivered odometry",
                "a unique motor, slip, obstruction, or collision attribution",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--capture-manifest", required=True, type=Path)
    parser.add_argument("--runtime-manifest", required=True, type=Path)
    parser.add_argument("--bt-xml", required=True, type=Path)
    parser.add_argument("--nav2-config", required=True, type=Path)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = export(
        args.events,
        args.capture_manifest,
        args.runtime_manifest,
        args.bt_xml,
        args.nav2_config,
        episode_id=args.episode_id,
    )
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    lowered = serialized.lower()
    if any(token in lowered for token in ("mobility hold", "persistent hold", "evaluator_only")):
        raise RuntimeError("evaluator-only intervention leaked into method-visible export")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8")


if __name__ == "__main__":
    main()
