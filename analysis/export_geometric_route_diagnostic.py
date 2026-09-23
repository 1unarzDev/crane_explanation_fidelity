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


def summarize_delivered_plans(fixture: dict) -> dict | None:
    plans = fixture.get("planHistory") or []
    if not plans:
        return None
    initial = fixture["initialPose"]
    goal = fixture["goal"]["position"]
    start_x, start_y = float(initial["x"]), float(initial["y"])
    route_dx = float(goal["x"]) - start_x
    route_dy = float(goal["y"]) - start_y
    route_length = math.hypot(route_dx, route_dy)
    if route_length <= 1e-9:
        raise ValueError("requested start and goal must be distinct")
    summaries = []
    for index, plan in enumerate(plans):
        points = plan.get("poses")
        if not points:
            return None
        canonical = json.dumps(points, sort_keys=True, separators=(",", ":")).encode("utf-8")
        path_id = f"sha256:{hashlib.sha256(canonical).hexdigest()}"
        length = sum(
            math.hypot(float(end["x"]) - float(start["x"]),
                       float(end["y"]) - float(start["y"]))
            for start, end in zip(points, points[1:])
        )
        signed = [
            (
                route_dx * (float(point["y"]) - start_y)
                - route_dy * (float(point["x"]) - start_x)
            ) / route_length
            for point in points
        ]
        computed = {
            "path_id": path_id,
            "planned_length_m": length,
            "minimum_signed_lateral_deviation_m": min(signed),
            "maximum_signed_lateral_deviation_m": max(signed),
            "maximum_absolute_lateral_deviation_m": max(map(abs, signed)),
        }
        expected = {
            "pathId": path_id,
            "poseCount": len(points),
            "plannedLengthMeters": length,
            "minimumSignedLateralDeviationFromRequestedRouteMeters": min(signed),
            "maximumSignedLateralDeviationFromRequestedRouteMeters": max(signed),
            "maximumAbsLateralDeviationFromRequestedRouteMeters": max(map(abs, signed)),
        }
        for key, value in expected.items():
            retained = plan.get(key)
            matches = (
                math.isclose(float(retained), float(value), rel_tol=1e-12, abs_tol=1e-12)
                if isinstance(value, float) and isinstance(retained, (int, float))
                else retained == value
            )
            if not matches:
                raise ValueError(f"plan {index} retained summary mismatch for {key}")
        summaries.append(computed)
    return {
        "delivered_plan_count": len(summaries),
        "unique_delivered_plan_count": len({item["path_id"] for item in summaries}),
        "first_plan_maximum_lateral_deviation_m": summaries[0][
            "maximum_absolute_lateral_deviation_m"
        ],
        "all_plans_minimum_signed_lateral_deviation_m": min(
            item["minimum_signed_lateral_deviation_m"] for item in summaries
        ),
        "all_plans_maximum_signed_lateral_deviation_m": max(
            item["maximum_signed_lateral_deviation_m"] for item in summaries
        ),
        "all_plans_maximum_lateral_deviation_m": max(
            item["maximum_absolute_lateral_deviation_m"] for item in summaries
        ),
        "summary_parity_passed": True,
        "provenance": fixture.get("planHistoryProvenance"),
    }


def export(
    fixture_path: Path,
    episode_id: str,
    nav2_config: Path,
    bt_xml: Path,
    *,
    robot_radius_m: float,
    inflation_radius_m: float,
    deadline_seconds: float,
    computation_version: str = "geometric-route-restriction-v1",
) -> dict:
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    goal = fixture["goal"]["position"]
    initial = fixture["initialPose"]
    goal_distance = math.hypot(float(goal["x"]) - float(initial["x"]),
                               float(goal["y"]) - float(initial["y"]))
    snapshot = fixture["latestCostmapSnapshot"]
    costmap_payload_available = bool(snapshot.get("data"))
    clearance = None
    lethal_samples = None
    first_lethal = None
    direct_route_fully_covered = None
    direct_route_has_lethal_cell = None
    direct_route_minimum_clearance_m = None
    if costmap_payload_available:
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
        route_samples = clearance["approach"]["samples"]
        lethal_samples = [
            sample for sample in route_samples
            if sample["cost"] is not None and int(sample["cost"]) >= 253
        ]
        direct_route_fully_covered = all(
            sample["cost"] is not None for sample in route_samples
        )
        # One observed lethal cell is sufficient to establish a restriction on the sampled route.
        # Conversely, no lethal sampled cell establishes a clear direct route only when the
        # retained grid covers every sample.  Fail closed for rolling/partial grids.
        direct_route_has_lethal_cell = (
            True if lethal_samples else (False if direct_route_fully_covered else None)
        )
        if lethal_samples or direct_route_fully_covered:
            direct_route_minimum_clearance_m = clearance["approach"][
                "minimumLethalClearanceMeters"
            ]
        # approach samples are indexed from goal backwards; the largest distance-before-goal is
        # the first lethal sample encountered from the retained start toward the goal.
        first_lethal = max(
            lethal_samples,
            key=lambda sample: sample["distanceBeforeGoal"],
            default=None,
        )
    trajectory = fixture.get("trajectory") or []
    max_lateral = max((abs(float(sample["y"]) - float(initial["y"]))
                       for sample in trajectory), default=None)
    max_forward = max((float(sample["x"]) - float(initial["x"])
                       for sample in trajectory), default=None)
    plan_successes = int(fixture.get("behaviorTreeTransitionCounts", {}).get(
        "ComputePathToPose:RUNNING->SUCCESS", 0))
    fixture_sha = sha256(fixture_path)
    nav2_sha = sha256(nav2_config)
    bt_sha = sha256(bt_xml)
    evidence_ids = (
        f"fixture-summary-sha256:{fixture_sha}",
        (
            f"costmap-data-sha256:{snapshot['dataSha256']}"
            if costmap_payload_available
            else f"costmap-metadata-declared-data-sha256:{snapshot['dataSha256']}"
        ),
        f"nav2-config-sha256:{nav2_sha}",
        f"bt-xml-sha256:{bt_sha}",
    )
    completeness = fixture.get("behaviorTreeCapture", {}).get("completeness", {})
    plan_geometry = summarize_delivered_plans(fixture)
    if computation_version == "geometric-route-restriction-v2" and plan_geometry is None:
        raise ValueError("v2 geometric diagnosis requires retained delivered plan poses")
    observation = GeometricRouteObservation(
        episode_id=episode_id,
        evidence_ids=evidence_ids,
        frame=str(snapshot["frameId"]),
        action_status=str(fixture["status"]),
        direct_route_has_lethal_cell=direct_route_has_lethal_cell,
        direct_route_minimum_clearance_m=direct_route_minimum_clearance_m,
        direct_route_first_lethal_x_m=(float(first_lethal["x"]) if first_lethal else None),
        direct_route_first_lethal_y_m=(float(first_lethal["y"]) if first_lethal else None),
        grid_connected=(clearance["connectedBelowCost253"] if clearance else None),
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
        delivered_plan_count=(
            plan_geometry["delivered_plan_count"] if plan_geometry else None
        ),
        unique_delivered_plan_count=(
            plan_geometry["unique_delivered_plan_count"] if plan_geometry else None
        ),
        first_plan_maximum_lateral_deviation_m=(
            plan_geometry["first_plan_maximum_lateral_deviation_m"]
            if plan_geometry else None
        ),
        all_plans_minimum_signed_lateral_deviation_m=(
            plan_geometry["all_plans_minimum_signed_lateral_deviation_m"]
            if plan_geometry else None
        ),
        all_plans_maximum_signed_lateral_deviation_m=(
            plan_geometry["all_plans_maximum_signed_lateral_deviation_m"]
            if plan_geometry else None
        ),
        all_plans_maximum_lateral_deviation_m=(
            plan_geometry["all_plans_maximum_lateral_deviation_m"]
            if plan_geometry else None
        ),
        computation_version=computation_version,
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
            "costmap_data_sha256_verified": costmap_payload_available,
            "costmap_payload_available": costmap_payload_available,
            "costmap_frame": snapshot["frameId"],
            "costmap_stamp": snapshot["stamp"],
            "nav2_config_sha256": nav2_sha,
            "bt_xml_sha256": bt_sha,
            "robot_radius_m": robot_radius_m,
            "inflation_radius_m": inflation_radius_m,
            "deadline_seconds": deadline_seconds,
            "computation_version": computation_version,
            "delivered_plan_geometry": plan_geometry,
        },
        "reference_computation": (
            {
                "schema": clearance["schema"],
                "status": "completed",
                "snapshot": clearance["snapshot"],
                "direct_route": {
                    "has_lethal_cell": direct_route_has_lethal_cell,
                    "fully_covered": direct_route_fully_covered,
                    "first_lethal_sample_from_start": first_lethal,
                    "minimum_lethal_clearance_m": direct_route_minimum_clearance_m,
                },
                "connected_below_cost_253": clearance["connectedBelowCost253"],
                "connectivity_origin": "action-result-pose",
            }
            if clearance
            else {
                "schema": "crane-nav2-costmap-clearance-audit-v1",
                "status": "not_run_missing_costmap_cell_payload",
                "missing": ["latestCostmapSnapshot.data"],
                "declared_data_sha256": snapshot["dataSha256"],
            }
        ),
        "diagnostic_result": result.to_dict(),
        "final_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "policy": "exact-checked-deterministic-rendering",
        },
        "evidence_boundary": {
            "included": [
                (
                    "delivered global Nav2 costmap snapshot"
                    if costmap_payload_available
                    else "delivered global Nav2 costmap metadata without cell payload"
                ),
                "delivered odometry trajectory",
                "delivered Nav2 global-plan geometry",
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
    parser.add_argument(
        "--computation-version",
        choices=("geometric-route-restriction-v1", "geometric-route-restriction-v2"),
        default="geometric-route-restriction-v1",
    )
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
        computation_version=args.computation_version,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
