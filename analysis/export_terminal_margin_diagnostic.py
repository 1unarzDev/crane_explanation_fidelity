#!/usr/bin/env python3
"""Export a compact robot-visible terminal-margin diagnosis from a fixture summary.

The large fixture summary remains governed at its source.  This exporter retains only the goal,
independent odometry-derived poses/motion, action outcome, and exact source configuration needed
to reproduce the diagnosis.  Evaluator docking labels and hidden simulator state are not copied.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE_SRC = ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"
sys.path.insert(0, str(CORE_SRC))

from crane_explain.diagnostics import (  # noqa: E402
    GoalTerminationObservation,
    diagnose_terminal_stopping_margin,
    render_diagnostic,
    verify_diagnostic_text,
)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def pose_error(pose: dict[str, float], goal: dict[str, float]) -> float:
    return math.hypot(pose["x"] - goal["x"], pose["y"] - goal["y"])


def config_value(config_text: str, key: str) -> float:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([0-9]+(?:\.[0-9]+)?)\s*$", config_text, re.M)
    if not match:
        raise ValueError(f"configuration key not found: {key}")
    return float(match.group(1))


def build_export(
    summary_path: Path,
    config_repository: Path,
    config_commit: str,
    config_path: str,
    task_tolerance_m: float,
    source_reference: str,
) -> dict[str, Any]:
    raw = summary_path.read_bytes()
    summary = json.loads(raw)
    config_bytes = subprocess.run(
        ["git", "show", f"{config_commit}:{config_path}"],
        cwd=config_repository,
        check=True,
        capture_output=True,
    ).stdout
    config_text = config_bytes.decode("utf-8")

    if summary.get("provenance") != "latest-delivered-odometry-not-proven-internal-consumption":
        raise ValueError("fixture does not declare the required independent odometry provenance")
    if summary.get("status") != "succeeded":
        raise ValueError("terminal-margin diagnostic currently requires a succeeded action")
    path = summary.get("plannedPath") or []
    if not path:
        raise ValueError("fixture has no retained planned path goal")
    trajectory = summary.get("trajectory") or []
    post_result = [sample for sample in trajectory if sample.get("phase") == "post_result"]
    if not post_result:
        raise ValueError("fixture has no post-result measured trajectory")

    goal = path[-1]
    return_pose = summary["actionResultPose"]
    final_pose = summary["finalPose"]
    summary_hash = sha256_bytes(raw)
    config_hash = sha256_bytes(config_bytes)
    evidence_ids = (
        f"fixture-summary:sha256:{summary_hash}",
        "odom:action-result-pose-and-speed",
        "odom:post-result-trajectory",
        "task-contract:xy-acceptance-tolerance",
        f"nav2-config:sha256:{config_hash}",
    )
    observation = GoalTerminationObservation(
        episode_id=summary_path.parent.name,
        evidence_ids=evidence_ids,
        frame="odom",
        action_status=summary["status"],
        configured_goal_tolerance_m=config_value(config_text, "xy_goal_tolerance"),
        configured_stopped_speed_mps=config_value(config_text, "trans_stopped_velocity"),
        task_acceptance_tolerance_m=task_tolerance_m,
        action_return_error_m=pose_error(return_pose, goal),
        measured_speed_at_return_mps=summary["motionAtActionResult"]["bodySpeedMetersPerSecond"],
        post_result_coast_m=summary["postResultCoastDistanceMeters"],
        settled_error_m=pose_error(final_pose, goal),
        action_return_timestamp_s=post_result[0]["simSeconds"],
        settled_timestamp_s=post_result[-1]["simSeconds"],
        source_anchor_ids=("nav2-stopped-goal-checker-config",),
    )
    result = diagnose_terminal_stopping_margin(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    return {
        "schema": "crane-terminal-margin-development-export-v1",
        "study_status": "DEVELOPMENT_ONLY_NOT_CONFIRMATORY",
        "episode_id": observation.episode_id,
        "evidence_boundary": {
            "classification": "robot_visible_declared_diagnostic_interface",
            "included": [
                "NavigateToPose/FollowPath result status",
                "goal pose from the supplied path",
                "delivered odometry-derived pose and body speed",
                "declared task acceptance tolerance",
                "exact Nav2 goal-checker configuration",
            ],
            "excluded": [
                "independent docking success label",
                "hidden simulator state",
                "environment force decomposition",
                "matched-intervention outcome",
            ],
            "consumption_limit": (
                "Delivered odometry supports the physical diagnostic but is not by itself proof "
                "of every value consumed internally by Nav2."
            ),
        },
        "source": {
            "fixture_summary": source_reference,
            "fixture_summary_sha256": summary_hash,
            "config_repository": "https://github.com/1unarzDev/crane_ml.git",
            "config_commit": config_commit,
            "config_path": config_path,
            "config_sha256": config_hash,
        },
        "observation": {
            "episode_id": observation.episode_id,
            "frame": observation.frame,
            "evidence_ids": observation.evidence_ids,
            "action_status": observation.action_status,
            "configured_goal_tolerance_m": observation.configured_goal_tolerance_m,
            "configured_stopped_speed_mps": observation.configured_stopped_speed_mps,
            "task_acceptance_tolerance_m": observation.task_acceptance_tolerance_m,
            "goal_pose": goal,
            "action_result_pose": return_pose,
            "action_return_error_m": observation.action_return_error_m,
            "measured_speed_at_return_mps": observation.measured_speed_at_return_mps,
            "post_result_coast_m": observation.post_result_coast_m,
            "final_pose": final_pose,
            "settled_error_m": observation.settled_error_m,
            "action_return_timestamp_s": observation.action_return_timestamp_s,
            "settled_timestamp_s": observation.settled_timestamp_s,
            "source_anchor_ids": observation.source_anchor_ids,
        },
        "diagnostic_result": result.to_dict(),
        "checked_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "method": "exact-deterministic-render-v1",
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--config-repository", type=Path, required=True)
    parser.add_argument("--config-commit", required=True)
    parser.add_argument(
        "--config-path", default="Tools/Performance/nav2_controller_fixture.yaml"
    )
    parser.add_argument("--task-tolerance-m", type=float, required=True)
    parser.add_argument("--source-reference", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_export(
        args.summary,
        args.config_repository,
        args.config_commit,
        args.config_path,
        args.task_tolerance_m,
        args.source_reference,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
