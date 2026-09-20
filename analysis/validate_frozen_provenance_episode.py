#!/usr/bin/env python3
"""Apply frozen, answer-blind inclusion gates to one sealed provenance episode."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_blob(checkout: Path, commit: str, repository_path: str) -> bytes:
    return subprocess.check_output(
        ("git", "-C", str(checkout), "show", f"{commit}:{repository_path}")
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_id")
    parser.add_argument("--structured-episode", required=True, type=Path)
    parser.add_argument("--recovery-parity-audit", required=True, type=Path)
    parser.add_argument("--cause-parity-audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing validation output: {args.output}")
    root = Path(__file__).resolve().parent.parent
    split = load_json(
        root / "research/explanation_fidelity/dataset_splits/provenance-final-v1.json"
    )
    amendment = load_json(
        root
        / "research/explanation_fidelity/experiment_configs/frozen/"
        "provenance-study-v1-amendment-1.json"
    )
    matches = [item for item in split["instances"] if item["opaque_episode_id"] == args.episode_id]
    require(len(matches) == 1, "episode is not a unique frozen split entry")
    instance = matches[0]
    robot_root = root / "data/robot_visible/final" / args.episode_id
    evaluator_root = root / "data/evaluator_only/final" / args.episode_id
    capture = robot_root / "capture"
    capture_manifest = load_json(capture / "manifest.json")
    runtime_payload = (capture / "runtime_manifest.json").read_bytes()
    runtime = json.loads(runtime_payload)
    records = [json.loads(line) for line in (capture / "events.jsonl").read_text().splitlines()]
    episode = load_json(args.structured_episode)
    recovery_parity = load_json(args.recovery_parity_audit)
    cause_parity = load_json(args.cause_parity_audit)
    fixture = load_json(evaluator_root / "fixture-summary.json")

    expected_episode_id = f"{args.episode_id}-worker-0"
    require(records[0]["type"] == "capture_started", "missing capture start boundary")
    require(records[-1]["type"] == "capture_stopped", "missing capture stop boundary")
    require(capture_manifest["run_id"] == args.episode_id, "capture run ID mismatch")
    require(capture_manifest["episode_id"] == expected_episode_id, "capture episode ID mismatch")
    require(runtime["run_id"] == args.episode_id, "runtime-manifest run ID mismatch")
    require(
        capture_manifest["runtime_manifest_sha256"] == sha256(runtime_payload),
        "runtime-manifest retained hash mismatch",
    )
    require(episode["episode_id"] == expected_episode_id, "structured episode ID mismatch")

    harness = [record["event"] for record in records if record["type"] == "harness_event"]
    goals = [event for event in harness if event["type"] == "navigate_to_pose_goal"]
    results = [event for event in harness if event["type"] == "navigate_to_pose_result"]
    require(len(goals) == 1 and len(results) == 1, "requires one accepted goal and one result")
    require(goals[0]["goal_id"] == results[0]["goal_id"], "goal/result identity mismatch")
    require(recovery_parity.get("accepted") is True, "recovery parity audit rejected")
    require(cause_parity.get("accepted") is True, "cause parity audit rejected")
    require(
        recovery_parity["episode_id"] == cause_parity["episode_id"] == expected_episode_id,
        "parity episode mismatch",
    )

    constants = amendment["launch_constants"]
    launch = runtime["launch_contract"]
    for key in ("scene", "platform", "command_flag", "lidar_frame"):
        require(launch[key] == constants[key], f"launch mismatch: {key}")
    require(launch["goal_distance_m"] == float(instance["goal_distance_m"]), "goal mismatch")
    require(
        launch["action_duration_s"] == float(constants["action_duration_s"]),
        "action duration mismatch",
    )

    repositories = {
        "capture_orchestrator": root,
        "runtime_manifest_builder": root,
        "behavior_tree_xml": root / "packages/crane_ml",
        "nav2_parameter_file": root / "packages/crane_ml",
        "land_fixture_entrypoint": root / "packages/crane_ml",
        "nav2_fixture_entrypoint": root / "packages/crane_ml",
    }
    for artifact in runtime["artifacts"]:
        committed = git_blob(
            repositories[artifact["role"]],
            artifact["repository_commit"],
            artifact["repository_path"],
        )
        require(artifact["byte_identical_to_git_object"] is True, "artifact equality false")
        require(artifact["content_sha256"] == sha256(committed), "artifact hash mismatch")

    evidence = {item["id"]: item for item in episode["evidence"]}
    recovery_count = evidence["recovery-count"]["value"]
    attempts = [
        event for event in episode["outcome"]["events"] if event["kind"] == "recovery_attempt"
    ]
    require(len({event["attempt_id"] for event in attempts}) == len(attempts), "duplicate attempt ID")
    require(recovery_count == len(attempts), "feedback/BT recovery-count mismatch")
    require(episode["outcome"]["recovery_history_complete"] is True, "recovery history incomplete")
    expected_terminal = (
        "succeeded"
        if instance["scenario_family"] == "recovery_followed_by_success"
        else "aborted"
    )
    expected_attempts = 1 if expected_terminal == "succeeded" else 2
    require(episode["outcome"]["terminal_status"] == expected_terminal, "family terminal mismatch")
    require(len(attempts) == expected_attempts, "family recovery activation mismatch")
    require(fixture["status"] == expected_terminal, "fixture terminal mismatch")
    require(fixture["goalAttempts"] == 1, "fixture accepted multiple goals")
    require(fixture["costmapObservations"] > 0, "no costmap observations")
    require(fixture["maximumOccupiedCostmapCells"] > 0, "empty costmap evidence")

    subprocess.run(
        (str(root / "analysis/scan_robot_visible_leakage.py"), str(robot_root)),
        check=True,
        capture_output=True,
        text=True,
    )
    result = {
        "schema": "crane-provenance-episode-inclusion/v1",
        "status": "INCLUDED",
        "episode_id": args.episode_id,
        "scenario_family": instance["scenario_family"],
        "answer_outputs_inspected": False,
        "terminal_status": expected_terminal,
        "unique_wait_invocations": len(attempts),
        "costmap_observations": fixture["costmapObservations"],
        "maximum_occupied_costmap_cells": fixture["maximumOccupiedCostmapCells"],
        "runtime_manifest_sha256": sha256(runtime_payload),
        "recovery_parity_units": len(recovery_parity["units"]),
        "cause_parity_units": len(cause_parity["units"]),
        "checks": [
            "capture boundaries and matching goal/result",
            "runtime manifest hash and effective launch contract",
            "source artifacts equal exact Git objects",
            "complete unique recovery invocation history",
            "predeclared family activation",
            "populated costmap evidence",
            "accepted F/G/H parity audits",
            "robot-visible evaluator-leakage scan",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
