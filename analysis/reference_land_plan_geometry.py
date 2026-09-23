#!/usr/bin/env python3
"""Independent reference for retained Nav2 plan geometry.

This evaluator-side implementation imports neither the fixture's plan-summary helper nor the
proposed diagnostic core. It recomputes each retained path hash, length, and signed deviation from
the requested start--goal line and fails closed if the recorded summaries disagree. A delivered
path is not proof that the controller consumed it or that a particular costmap caused its shape.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def path_sha256(points: list[dict[str, Any]]) -> str:
    payload = json.dumps(points, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def calculate(fixture: dict[str, Any], *, episode_id: str | None = None) -> dict[str, Any]:
    initial = fixture["initialPose"]
    goal = fixture["goal"]["position"]
    start_x, start_y = float(initial["x"]), float(initial["y"])
    route_dx = float(goal["x"]) - start_x
    route_dy = float(goal["y"]) - start_y
    route_length = math.hypot(route_dx, route_dy)
    if route_length <= 1e-9:
        raise ValueError("requested start and goal must be distinct")

    recomputed: list[dict[str, Any]] = []
    mismatches: list[str] = []
    for index, plan in enumerate(fixture.get("planHistory") or []):
        points = plan.get("poses")
        if not points:
            mismatches.append(f"plan {index} lacks retained poses")
            continue
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
        values = {
            "path_id": path_sha256(points),
            "planned_length_m": length,
            "minimum_signed_lateral_deviation_m": min(signed),
            "maximum_signed_lateral_deviation_m": max(signed),
            "maximum_absolute_lateral_deviation_m": max(map(abs, signed)),
            "wall_seconds": float(plan["wallSeconds"]),
        }
        recomputed.append(values)
        comparisons = (
            ("pathId", values["path_id"]),
            ("poseCount", len(points)),
            ("plannedLengthMeters", length),
            (
                "minimumSignedLateralDeviationFromRequestedRouteMeters",
                values["minimum_signed_lateral_deviation_m"],
            ),
            (
                "maximumSignedLateralDeviationFromRequestedRouteMeters",
                values["maximum_signed_lateral_deviation_m"],
            ),
            (
                "maximumAbsLateralDeviationFromRequestedRouteMeters",
                values["maximum_absolute_lateral_deviation_m"],
            ),
        )
        for key, expected in comparisons:
            actual = plan.get(key)
            if isinstance(expected, float):
                matches = isinstance(actual, (int, float)) and math.isclose(
                    float(actual), expected, rel_tol=1e-12, abs_tol=1e-12
                )
            else:
                matches = actual == expected
            if not matches:
                mismatches.append(f"plan {index} {key}: {actual!r} != {expected!r}")

    if not recomputed:
        raise ValueError("no delivered plans with retained poses")
    min_signed = min(item["minimum_signed_lateral_deviation_m"] for item in recomputed)
    max_signed = max(item["maximum_signed_lateral_deviation_m"] for item in recomputed)
    max_absolute = max(item["maximum_absolute_lateral_deviation_m"] for item in recomputed)
    first_absolute = recomputed[0]["maximum_absolute_lateral_deviation_m"]
    return {
        "schema": "crane-land-plan-geometry-independent-reference/v1",
        "status": "DEVELOPMENT_REFERENCE_NOT_CONFIRMATORY",
        "episode_id": episode_id or fixture.get("runId") or fixture.get("scope"),
        "implementation_independence": {
            "imports_fixture_summary_helper": False,
            "imports_proposed_diagnostic_core": False,
            "human_label": False,
        },
        "measurements": {
            "delivered_plan_count": len(recomputed),
            "unique_plan_hash_count": len({item["path_id"] for item in recomputed}),
            "first_plan_maximum_absolute_lateral_deviation_m": first_absolute,
            "all_plans_minimum_signed_lateral_deviation_m": min_signed,
            "all_plans_maximum_signed_lateral_deviation_m": max_signed,
            "all_plans_maximum_absolute_lateral_deviation_m": max_absolute,
            "action_status": str(fixture.get("status", "unknown")).lower(),
            "summary_mismatches": mismatches,
        },
        "reference_findings": {
            "summary_parity_passed": not mismatches,
            "multiple_distinct_delivered_plans": len(
                {item["path_id"] for item in recomputed}
            ) > 1,
            "substantial_plan_deviation_observed": max_absolute > 0.5,
            "plans_observed_on_both_sides_of_requested_route": (
                min_signed < -0.5 and max_signed > 0.5
            ),
            "controller_consumption_proven": False,
            "costmap_caused_plan_change_proven": False,
            "physical_obstacle_identity_supported": False,
        },
        "required_withholding": [
            "Delivered plan geometry does not prove controller consumption.",
            "The retained plans and costmaps do not prove that a specific snapshot caused a path change.",
            "Evaluator-only obstacle identity is unavailable to explanation methods.",
            "Temporal association does not establish physical causation.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = calculate(
        json.loads(args.fixture.read_text(encoding="utf-8")),
        episode_id=args.episode_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
