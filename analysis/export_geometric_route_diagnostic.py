#!/usr/bin/env python3
"""Export a bounded robot-visible geometric-route diagnosis from a Nav2 fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"
TOOLS = ROOT / "packages" / "crane_ml" / "Tools" / "Performance"
sys.path.insert(0, str(CORE))
sys.path.insert(0, str(TOOLS))

from audit_nav2_costmap_clearance import audit  # noqa: E402
from crane_explain.diagnostics import (  # noqa: E402
    GeometricRouteObservation,
    diagnose_geometric_route_restriction,
    render_diagnostic,
    verify_diagnostic_text,
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stamp_seconds(stamp: dict) -> float:
    return float(stamp["sec"]) + float(stamp["nanosec"]) / 1_000_000_000.0


def export(
    fixture_path: Path,
    episode_id: str,
    nav2_config: Path,
    bt_xml: Path,
    *,
    robot_radius_m: float,
    inflation_radius_m: float,
    deadline_seconds: float,
) -> dict:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    goal = fixture["goal"]["position"]
    initial = fixture["initialPose"]
    goal_distance = math.hypot(float(goal["x"]) - float(initial["x"]),
                               float(goal["y"]) - float(initial["y"]))
    clearance = audit(
        fixture,
        float(goal["x"]),
        float(goal["y"]),
        float(fixture["goal"]["yaw"]),
        goal_distance,
        robot_radius_m,
        robot_radius_m,
        inflation_radius_m,
    )
    lethal_samples = [
        sample for sample in clearance["approach"]["samples"]
        if sample["cost"] is not None and int(sample["cost"]) >= 253
    ]
    # approach samples are indexed from goal backwards; the largest distance-before-goal is the
    # first lethal sample encountered when traveling from the retained start toward the goal.
    first_lethal = max(lethal_samples, key=lambda sample: sample["distanceBeforeGoal"], default=None)
    trajectory = fixture.get("trajectory") or []
    max_lateral = max((abs(float(sample["y"]) - float(initial["y"]))
                       for sample in trajectory), default=None)
    max_forward = max((float(sample["x"]) - float(initial["x"])
                       for sample in trajectory), default=None)
    plan_successes = int(fixture.get("behaviorTreeTransitionCounts", {}).get(
        "ComputePathToPose:RUNNING->SUCCESS", 0))
    snapshot = fixture["latestCostmapSnapshot"]
    fixture_sha = sha256(fixture_path)
    nav2_sha = sha256(nav2_config)
    bt_sha = sha256(bt_xml)
    evidence_ids = (
        f"fixture-summary-sha256:{fixture_sha}",
        f"costmap-data-sha256:{snapshot['dataSha256']}",
        f"nav2-config-sha256:{nav2_sha}",
        f"bt-xml-sha256:{bt_sha}",
    )
    completeness = fixture.get("behaviorTreeCapture", {}).get("completeness", {})
    observation = GeometricRouteObservation(
        episode_id=episode_id,
        evidence_ids=evidence_ids,
        frame=str(snapshot["frameId"]),
        action_status=str(fixture["status"]),
        direct_route_has_lethal_cell=bool(lethal_samples),
        direct_route_minimum_clearance_m=clearance["approach"]["minimumLethalClearanceMeters"],
        direct_route_first_lethal_x_m=(float(first_lethal["x"]) if first_lethal else None),
        direct_route_first_lethal_y_m=(float(first_lethal["y"]) if first_lethal else None),
        grid_connected=clearance["connectedBelowCost253"],
        connectivity_origin="action-result-pose",
        maximum_lateral_deviation_m=max_lateral,
        maximum_forward_progress_m=max_forward,
        goal_distance_m=goal_distance,
        successful_plan_count=plan_successes,
        action_wall_seconds=float(fixture["wallSeconds"]),
        configured_deadline_seconds=deadline_seconds,
        configured_robot_radius_m=robot_radius_m,
        configured_inflation_radius_m=inflation_radius_m,
        costmap_resolution_m=float(snapshot["resolution"]),
        costmap_snapshot_sha256=str(snapshot["dataSha256"]),
        costmap_snapshot_timestamp_s=stamp_seconds(snapshot["stamp"]),
        terminal_transition_observed=bool(completeness.get("terminalTransitionObserved", False)),
        source_anchor_ids=(
            f"nav2-config-sha256:{nav2_sha}",
            f"bt-xml-sha256:{bt_sha}",
        ),
    )
    result = diagnose_geometric_route_restriction(observation)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    if not verification.accepted:
        raise RuntimeError("deterministic diagnostic rendering failed verification")
    return {
        "schema": "crane-geometric-route-diagnostic-export-v1",
        "episode_id": episode_id,
        "visibility": "robot_visible",
        "development_only": True,
        "method_input": {
            "fixture_summary_sha256": fixture_sha,
            "costmap_data_sha256": snapshot["dataSha256"],
            "costmap_frame": snapshot["frameId"],
            "costmap_stamp": snapshot["stamp"],
            "nav2_config_sha256": nav2_sha,
            "bt_xml_sha256": bt_sha,
            "robot_radius_m": robot_radius_m,
            "inflation_radius_m": inflation_radius_m,
            "deadline_seconds": deadline_seconds,
        },
        "reference_computation": {
            "schema": clearance["schema"],
            "snapshot": clearance["snapshot"],
            "direct_route": {
                "has_lethal_cell": bool(lethal_samples),
                "first_lethal_sample_from_start": first_lethal,
                "minimum_lethal_clearance_m": clearance["approach"]["minimumLethalClearanceMeters"],
            },
            "connected_below_cost_253": clearance["connectedBelowCost253"],
            "connectivity_origin": "action-result-pose",
        },
        "diagnostic_result": result.to_dict(),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "policy": "exact-checked-deterministic-rendering",
        },
        "evidence_boundary": {
            "included": [
                "delivered global Nav2 costmap snapshot",
                "delivered odometry trajectory",
                "NavigateToPose result status and timing",
                "exact Nav2 configuration and BT source hashes",
            ],
            "excluded": [
                "evaluator-only layout identity and obstacle semantic IDs",
                "simulator geometry and collision truth",
                "claims that every retained value was consumed by Nav2",
                "global physical infeasibility",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--nav2-config", type=Path, required=True)
    parser.add_argument("--bt-xml", type=Path, required=True)
    parser.add_argument("--robot-radius", type=float, required=True)
    parser.add_argument("--inflation-radius", type=float, required=True)
    parser.add_argument("--deadline-seconds", type=float, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = export(
        args.fixture,
        args.episode_id,
        args.nav2_config,
        args.bt_xml,
        robot_radius_m=args.robot_radius,
        inflation_radius_m=args.inflation_radius,
        deadline_seconds=args.deadline_seconds,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
