#!/usr/bin/env python3
"""Build an evidence-complete v5 judge reference without treating P's diagnosis as gold."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import run_measurement_complete_v2_development as base
from build_checked_composition_annotation_reference import load_inventory
from run_raw_baseline_v5_development import _reference


ROOT = Path(__file__).resolve().parents[1]


def _raw_binding(raw: dict[str, Any], sha256: str) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "schema": raw.get("schema"),
        "visibility": raw.get("visibility"),
        "episode_id": raw.get("episode_id"),
        "raw_evidence_sha256": sha256,
        "treatment_boundary": raw.get("treatment_boundary"),
    }
    for field in (
        "source",
        "evidence_boundary",
        "evidence_mask",
        "declared_diagnostic_configuration",
        "configuration_source_sha256",
    ):
        if field in raw:
            binding[field] = copy.deepcopy(raw[field])
    method = raw.get("method_input")
    if isinstance(method, dict):
        binding["raw_stream_and_execution_inventory"] = {
            "action_status": method.get("action_status"),
            "action_error_code": method.get("action_error_code"),
            "analysis_duration_s": method.get("analysis_duration_s"),
            "command_frame": method.get("command_frame"),
            "measured_frame": method.get("measured_frame"),
            "command_sample_count": len(method.get("command_samples") or []),
            "odometry_sample_count": len(method.get("odometry_samples") or []),
            "command_provenance": method.get("command_provenance"),
            "odometry_provenance": method.get("odometry_provenance"),
            "windowing": copy.deepcopy(method.get("windowing")),
            "execution_sequence": copy.deepcopy(method.get("execution_sequence")),
        }
    else:
        binding["raw_geometry_inventory"] = {
            "status": raw.get("status"),
            "wall_seconds": raw.get("wallSeconds"),
            "initial_pose": copy.deepcopy(raw.get("initialPose")),
            "goal": copy.deepcopy(raw.get("goal")),
            "action_result_pose": copy.deepcopy(raw.get("actionResultPose")),
            "costmap_metadata": {
                key: copy.deepcopy(value)
                for key, value in (raw.get("latestCostmapSnapshot") or {}).items()
                if key != "data"
            },
            "costmap_cell_payload_present": "data" in (raw.get("latestCostmapSnapshot") or {}),
            "delivered_plan_count": len(raw.get("planHistory") or []),
            "trajectory_sample_count": len(raw.get("trajectory") or []),
            "plan_history_provenance": copy.deepcopy(raw.get("planHistoryProvenance")),
            "trajectory_provenance": copy.deepcopy(raw.get("trajectoryProvenance")),
            "behavior_tree_capture": copy.deepcopy(raw.get("behaviorTreeCapture")),
            "behavior_tree_transition_counts": copy.deepcopy(
                raw.get("behaviorTreeTransitionCounts")
            ),
        }
    return binding


def build(contract: dict[str, Any], result: dict[str, Any], case_id: str) -> dict[str, Any]:
    cases = {item["case_id"]: item for item in contract.get("cases", [])}
    if len(cases) != len(contract.get("cases", [])) or case_id not in cases:
        raise ValueError("contract has duplicate or missing case")
    case = cases[case_id]
    if result.get("case_id") != case_id:
        raise ValueError("contract/result case mismatch")
    diagnostic = json.loads((ROOT / case["diagnostic_path"]).read_text(encoding="utf-8"))
    inventory = load_inventory(ROOT / contract["reference_inventory"])
    reference = _reference(case, diagnostic, inventory)
    inherited_hash = base.sha256_json(reference)
    if inherited_hash != result.get("inputs", {}).get("annotation_reference_sha256"):
        raise ValueError("result is not bound to the independently checked reference")

    raw_path = ROOT / case["baseline_evidence_path"]
    raw_hash = base.sha256_path(raw_path)
    if raw_hash != case["baseline_evidence_sha256"]:
        raise ValueError("raw baseline evidence hash mismatch")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    if raw.get("visibility") != "robot_visible":
        raise ValueError("raw baseline evidence is not robot-visible")

    allowed = reference["allowed_evidence"]
    allowed.pop("primitive_diagnostic", None)
    allowed["raw_robot_visible_evidence_binding"] = _raw_binding(raw, raw_hash)
    allowed["gold_boundary"] = (
        "Required units and independent calculations were constructed from retained evidence; "
        "the proposed method's checked diagnostic, plan, verifier, and answer are not gold. The "
        "independent computations establish only their declared predicates."
    )
    reference["reference_status"] = (
        "DEVELOPMENT_PRE_JUDGE_INDEPENDENT_REFERENCE_NOT_HUMAN_GOLD"
    )
    reference["evidence_completeness"] = (
        "The packet contains independently recomputed facts, raw-evidence provenance and source/"
        "configuration bindings needed for the declared units. It excludes evaluator intervention "
        "identity and P's checked diagnostic, certificate, answer plan, verifier, and answer."
    )
    reference["completeness_audit"].update(
        {
            "raw_baseline_hash_verified": True,
            "proposed_diagnostic_excluded_from_gold": True,
            "evaluator_truth_excluded": True,
        }
    )
    reference["transport_binding"] = {
        "screen_id": contract["screen_id"],
        "case_id": case_id,
        "inherited_validated_reference_sha256": inherited_hash,
        "raw_evidence_sha256": raw_hash,
        "scientific_units_changed": False,
    }
    return reference


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    reference = build(contract, result, args.case_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reference, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
