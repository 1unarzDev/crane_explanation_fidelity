#!/usr/bin/env python3
"""Add a systematic, response-independent raw-evidence closure to a v5 judge reference."""

from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from reference_land_geometric import bresenham, cell_center, cell_cost, decode_grid, world_to_cell


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "crane-raw-baseline-v5-judge-evidence-closure/v1"


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sample_summary(samples: list[dict[str, Any]]) -> dict[str, Any]:
    if not samples:
        return {
            "count": 0,
            "canonical_sha256": _canonical_sha256(samples),
            "first": None,
            "last": None,
            "minimum_speed_sample": None,
            "maximum_speed_sample": None,
            "exact_speed_frequencies": [],
            "frequency_omission": None,
        }
    minimum = min(samples, key=lambda item: (float(item["planar_speed_mps"]), float(item["offset_s"])))
    maximum = max(samples, key=lambda item: (float(item["planar_speed_mps"]), -float(item["offset_s"])))
    counts = Counter(float(item["planar_speed_mps"]) for item in samples)
    frequencies = (
        [{"planar_speed_mps": value, "count": counts[value]} for value in sorted(counts)]
        if len(counts) <= 64
        else []
    )
    return {
        "count": len(samples),
        "canonical_sha256": _canonical_sha256(samples),
        "first": copy.deepcopy(samples[0]),
        "last": copy.deepcopy(samples[-1]),
        "minimum_speed_sample": copy.deepcopy(minimum),
        "maximum_speed_sample": copy.deepcopy(maximum),
        "exact_speed_frequencies": frequencies,
        "frequency_omission": (
            None
            if frequencies
            else f"{len(counts)} unique values exceed the fixed 64-value closure limit"
        ),
    }


def _command_closure(raw: dict[str, Any]) -> dict[str, Any]:
    method = raw["method_input"]
    configuration = {
        key: copy.deepcopy(value)
        for key, value in method.items()
        if key not in {"command_samples", "odometry_samples"}
    }
    return {
        "family": "command_motion",
        "source": copy.deepcopy(raw["source"]),
        "evidence_boundary": copy.deepcopy(raw["evidence_boundary"]),
        "evidence_mask": copy.deepcopy(raw.get("evidence_mask")),
        "method_configuration_and_execution": configuration,
        "command_samples": _sample_summary(method.get("command_samples") or []),
        "odometry_samples": _sample_summary(method.get("odometry_samples") or []),
    }


def _extreme(samples: list[dict[str, Any]], key: str, maximum: bool) -> dict[str, Any] | None:
    if not samples:
        return None
    chooser = max if maximum else min
    return copy.deepcopy(chooser(samples, key=lambda item: float(item[key])))


def _trajectory_closure(raw: dict[str, Any]) -> dict[str, Any]:
    samples = raw.get("trajectory") or []
    initial = raw["initialPose"]
    goal = raw["goal"]["position"]
    start_x, start_y = float(initial["x"]), float(initial["y"])
    route_dx = float(goal["x"]) - start_x
    route_dy = float(goal["y"]) - start_y
    route_length = math.hypot(route_dx, route_dy)
    augmented = []
    for item in samples:
        dx = float(item["x"]) - start_x
        dy = float(item["y"]) - start_y
        augmented.append(
            {
                "sample": item,
                "signed_lateral_deviation_m": (route_dx * dy - route_dy * dx) / route_length,
                "forward_progress_m": (dx * route_dx + dy * route_dy) / route_length,
            }
        )

    def selected(key: str, maximum: bool) -> dict[str, Any] | None:
        if not augmented:
            return None
        chooser = max if maximum else min
        item = chooser(augmented, key=lambda value: float(value[key]))
        return copy.deepcopy(item)

    return {
        "count": len(samples),
        "canonical_sha256": _canonical_sha256(samples),
        "first": copy.deepcopy(samples[0]) if samples else None,
        "last": copy.deepcopy(samples[-1]) if samples else None,
        "minimum_x": _extreme(samples, "x", False),
        "maximum_x": _extreme(samples, "x", True),
        "minimum_y": _extreme(samples, "y", False),
        "maximum_y": _extreme(samples, "y", True),
        "minimum_signed_lateral_deviation": selected("signed_lateral_deviation_m", False),
        "maximum_signed_lateral_deviation": selected("signed_lateral_deviation_m", True),
        "maximum_forward_progress": selected("forward_progress_m", True),
    }


def _costmap_closure(raw: dict[str, Any]) -> dict[str, Any]:
    snapshot = raw["latestCostmapSnapshot"]
    grid = decode_grid(snapshot)
    metadata = {key: copy.deepcopy(value) for key, value in snapshot.items() if key != "data"}
    initial = (float(raw["initialPose"]["x"]), float(raw["initialPose"]["y"]))
    goal = (
        float(raw["goal"]["position"]["x"]),
        float(raw["goal"]["position"]["y"]),
    )
    start_cell = world_to_cell(snapshot, initial)
    goal_cell = world_to_cell(snapshot, goal)
    direct_cells = []
    for cell in bresenham(start_cell, goal_cell):
        cost = cell_cost(snapshot, grid, cell) if grid is not None else None
        center = cell_center(snapshot, cell)
        direct_cells.append(
            {
                "cell": list(cell),
                "center_x_m": center[0],
                "center_y_m": center[1],
                "cost": cost,
                "inside_retained_grid": cost is not None,
            }
        )
    histogram = (
        [{"cost": value, "count": count} for value, count in sorted(Counter(grid).items())]
        if grid is not None
        else None
    )
    return {
        "metadata": metadata,
        "cell_payload_available": grid is not None,
        "full_grid_cost_histogram": histogram,
        "requested_direct_route_start_cell": list(start_cell),
        "requested_direct_route_goal_cell": list(goal_cell),
        "requested_direct_route_cells": direct_cells,
        "first_direct_route_cost_at_least_253": next(
            (item for item in direct_cells if item["cost"] is not None and item["cost"] >= 253),
            None,
        ),
        "first_direct_route_cost_254": next(
            (item for item in direct_cells if item["cost"] == 254),
            None,
        ),
    }


def _geometry_closure(raw: dict[str, Any]) -> dict[str, Any]:
    plans = []
    for plan in raw.get("planHistory") or []:
        summary = {key: copy.deepcopy(value) for key, value in plan.items() if key != "poses"}
        summary["poses_canonical_sha256"] = _canonical_sha256(plan.get("poses") or [])
        summary["first_pose"] = copy.deepcopy((plan.get("poses") or [None])[0])
        summary["last_pose"] = copy.deepcopy((plan.get("poses") or [None])[-1])
        plans.append(summary)
    goal = raw["goal"]["position"]
    result = raw.get("actionResultPose") or raw["finalPose"]
    distance = math.hypot(float(goal["x"]) - float(result["x"]), float(goal["y"]) - float(result["y"]))
    return {
        "family": "geometry",
        "declared_diagnostic_configuration": copy.deepcopy(
            raw["declared_diagnostic_configuration"]
        ),
        "configuration_source_sha256": raw["configuration_source_sha256"],
        "action": {
            "status": raw["status"],
            "wall_seconds": raw["wallSeconds"],
            "initial_pose": copy.deepcopy(raw["initialPose"]),
            "goal": copy.deepcopy(raw["goal"]),
            "action_result_pose": copy.deepcopy(raw.get("actionResultPose")),
            "final_pose": copy.deepcopy(raw["finalPose"]),
            "action_result_distance_to_goal_m": distance,
        },
        "costmap": _costmap_closure(raw),
        "plans": plans,
        "plan_history_provenance": copy.deepcopy(raw["planHistoryProvenance"]),
        "trajectory": _trajectory_closure(raw),
        "trajectory_provenance": copy.deepcopy(raw["trajectoryProvenance"]),
        "behavior_tree_capture": copy.deepcopy(raw["behaviorTreeCapture"]),
        "behavior_tree_transition_counts": copy.deepcopy(raw["behaviorTreeTransitionCounts"]),
    }


def build(reference: dict[str, Any], raw: dict[str, Any], raw_sha256: str) -> dict[str, Any]:
    if raw.get("visibility") != "robot_visible":
        raise ValueError("raw evidence is not robot-visible")
    closure = _command_closure(raw) if "method_input" in raw else _geometry_closure(raw)
    closure.update(
        {
            "schema": SCHEMA,
            "episode_id": raw["episode_id"],
            "raw_evidence_sha256": raw_sha256,
            "selection_rule": (
                "Fields are selected by the fixed raw schema and declared deterministic tools: "
                "source/configuration and execution metadata; exact low-cardinality sample "
                "frequencies; sample extrema and boundaries; complete plan summaries; trajectory "
                "extrema; complete BT transitions; and every requested-direct-route costmap cell."
            ),
            "claim_scope_rule": (
                "A candidate detail outside this closure is not thereby false. If it cannot be "
                "checked from the independent computations or closure, mark it ambiguous/unresolved "
                "or evidence_problem rather than unsupported."
            ),
        }
    )
    result = copy.deepcopy(reference)
    allowed = result["allowed_evidence"]
    allowed["raw_evidence_closure"] = closure
    allowed["raw_robot_visible_evidence_binding"]["systematic_closure_available_to_judge"] = True
    result["evidence_completeness"] = (
        "The packet contains independent endpoint computations plus a response-independent closure "
        "of robot-visible raw facts exposed by the permitted tools. Raw arrays and compressed cells "
        "are represented by hashes and systematic summaries rather than embedded wholesale. A claim "
        "outside the closure must be unresolved, not presumed false. Evaluator truth and P's checked "
        "diagnosis, certificate, plan, verifier, and answer remain excluded."
    )
    result["completeness_audit"]["systematic_raw_evidence_closure"] = True
    result["evidence_closure_revision"] = {
        "amendment": (
            "research/explanation_fidelity/experiment_configs/development/"
            "raw-baseline-v5-language-screen-v1-annotation-amendment-1.json"
        ),
        "method_response_content_changed": False,
        "required_units_changed": False,
        "prohibited_claims_changed": False,
        "raw_evidence_sha256": raw_sha256,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--raw-evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    raw_bytes = args.raw_evidence.read_bytes()
    result = build(
        json.loads(args.reference.read_text(encoding="utf-8")),
        json.loads(raw_bytes),
        hashlib.sha256(raw_bytes).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
