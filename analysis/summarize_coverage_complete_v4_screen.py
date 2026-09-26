#!/usr/bin/env python3
"""Aggregate the frozen coverage-complete-v4 screen without rejudging it."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDECLARATION = ROOT / (
    "manifests/annotation/"
    "luna-coverage-complete-v4-language-screen-v1-predeclaration.json"
)
DEFAULT_ANNOTATION_ROOT = ROOT / (
    "model_outputs/automated_annotations/luna-model-judge-v1/"
    "coverage-complete-v4-language-screen-v1"
)
KEY_ROOT = ROOT / (
    "data/evaluator_only/dev/coverage-complete-v4-language-screen-v1/annotation_keys"
)
RESULT_ROOT = ROOT / "model_outputs/dev/coverage-complete-v4-language-screen-v1/results"
REFERENCE_ROOT = ROOT / "model_outputs/dev/coverage-complete-v4-language-screen-v1/references"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def _metric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    covered = sum(row["required_units_covered"] for row in rows)
    total = sum(row["required_units_total"] for row in rows)
    return {
        "judgments": len(rows),
        "material_errors": sum(row["material_error"] is True for row in rows),
        "material_error_rate": sum(row["material_error"] is True for row in rows) / len(rows),
        "causal_overclaims": sum(row["causal_overclaim"] is True for row in rows),
        "required_units_covered": covered,
        "required_units_total": total,
        "required_unit_coverage": covered / total,
    }


def _verify_artifact_inventory(predeclaration: dict[str, Any]) -> None:
    frozen = predeclaration["frozen_artifacts"]
    manifest_field = (
        "results_references_packets_manifest"
        if "results_references_packets_manifest" in frozen
        else "references_and_packets_manifest"
    )
    manifest_hash_field = f"{manifest_field}_sha256"
    manifest_path = ROOT / frozen[manifest_field]
    if digest(manifest_path) != frozen[manifest_hash_field]:
        raise ValueError("frozen result/reference/packet manifest hash mismatch")
    manifest = load(manifest_path)
    if len(manifest.get("artifacts", [])) != frozen["artifact_count"]:
        raise ValueError("frozen artifact count mismatch")
    for item in manifest["artifacts"]:
        path = ROOT / item["path"]
        if path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            raise ValueError(f"frozen artifact differs: {item['path']}")

    key_manifest_path = ROOT / frozen["condition_key_manifest"]
    if digest(key_manifest_path) != frozen["condition_key_manifest_sha256"]:
        raise ValueError("condition-key manifest hash mismatch")
    key_manifest = load(key_manifest_path)
    if key_manifest.get("file_count") != frozen["condition_key_count"]:
        raise ValueError("condition-key count mismatch")
    for item in key_manifest["files"]:
        path = ROOT / item["path"]
        if path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
            raise ValueError(f"condition key differs: {item['path']}")


def aggregate(predeclaration_path: Path, annotation_root: Path) -> dict[str, Any]:
    predeclaration = load(predeclaration_path)
    if predeclaration.get("status") not in {
        "FROZEN_AFTER_RESPONSES_BEFORE_ANY_LUNA_STUDY_CALL",
        "FROZEN_BEFORE_ANY_REVISED_LUNA_CALL",
    }:
        raise ValueError("study annotation predeclaration was not frozen before Luna calls")
    _verify_artifact_inventory(predeclaration)

    revised_arm = predeclaration.get("arm_id")
    key_root = (
        ROOT / f"data/evaluator_only/dev/{revised_arm}/annotation_keys"
        if revised_arm
        else KEY_ROOT
    )
    reference_root = (
        ROOT / f"model_outputs/dev/{revised_arm}/references"
        if revised_arm
        else REFERENCE_ROOT
    )

    declared = {item["case_id"]: item for item in predeclaration["cases"]}
    if len(declared) != len(predeclaration["cases"]):
        raise ValueError("duplicate declared case IDs")
    if "treatment_contract" in predeclaration:
        treatment_path = ROOT / predeclaration["treatment_contract"]["path"]
    else:
        original = load(
            ROOT
            / "manifests/annotation/"
            "luna-coverage-complete-v4-language-screen-v1-predeclaration.json"
        )
        treatment_path = ROOT / original["treatment_contract"]["path"]
    treatment = load(treatment_path)
    treatment_cases = {item["case_id"]: item for item in treatment["cases"]}
    if set(declared) != set(treatment_cases):
        raise ValueError("treatment and annotation case inventories differ")

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    summary_hashes: dict[str, str] = {}
    for case_id, case in declared.items():
        key_path = key_root / f"{case_id}.json"
        key = load(key_path)
        conditions = {item["response_id"]: item["condition"] for item in key["entries"]}
        if set(conditions.values()) != {"P", "R"}:
            raise ValueError(f"{case_id}: condition inventory is not exactly P/R")
        summary_path = annotation_root / case_id / "development-summary.json"
        summary = load(summary_path)
        summary_hashes[case_id] = digest(summary_path)
        failures.extend({"case_id": case_id, **item} for item in summary["call_failures"])
        for pass_id in ("pass-1", "pass-2"):
            for response_id, condition in conditions.items():
                cache_key = summary["cache_keys"].get(pass_id, {}).get(response_id)
                if cache_key is None:
                    continue
                call_path = annotation_root / case_id / "calls/high" / pass_id / f"{cache_key}.json"
                call = load(call_path)
                if call.get("status") != "VALID":
                    raise ValueError(f"{case_id}/{pass_id}/{condition}: invalid call")
                judgment = call["judgment"]
                units = judgment["required_units"]
                if len({item["unit_id"] for item in units}) != len(units):
                    raise ValueError(f"{case_id}/{pass_id}/{condition}: duplicate unit judgment")
                rows.append(
                    {
                        "case_id": case_id,
                        "cluster_id": case["cluster_id"],
                        "family": treatment_cases[case_id]["family"],
                        "independent_cluster": case["independent_cluster"],
                        "primary_endpoint_eligible": case["primary_endpoint_eligible"],
                        "pass_id": pass_id,
                        "condition": condition,
                        "response_id": response_id,
                        "call_sha256": digest(call_path),
                        "supported_diagnostic_success": summary["passes"][pass_id][condition][
                            "supported_diagnostic_success"
                        ],
                        "material_error": judgment["material_error"],
                        "material_error_categories": judgment["material_error_categories"],
                        "causal_overclaim": judgment["causal_overclaim"],
                        "correct_abstention": judgment["correct_abstention"],
                        "required_units_covered": sum(
                            item["status"] == "covered" for item in units
                        ),
                        "required_units_total": len(units),
                        "unit_status": {item["unit_id"]: item["status"] for item in units},
                        "uncovered_units": [
                            {"unit_id": item["unit_id"], "status": item["status"]}
                            for item in units
                            if item["status"] != "covered"
                        ],
                    }
                )

    metrics = {
        condition: _metric([row for row in rows if row["condition"] == condition])
        for condition in ("P", "R")
    }
    endpoint_cases = set(predeclaration["scoring"]["primary_endpoint_cases"])
    endpoint_by_pass: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        report: dict[str, Any] = {}
        for condition in ("P", "R"):
            selected = [
                row
                for row in rows
                if row["pass_id"] == pass_id
                and row["condition"] == condition
                and row["case_id"] in endpoint_cases
            ]
            report[condition] = {
                "successes": sum(row["supported_diagnostic_success"] is True for row in selected),
                "total": len(selected),
            }
        total = report["P"]["total"]
        report["p_minus_r"] = (
            (report["P"]["successes"] - report["R"]["successes"]) / total
            if total and total == report["R"]["total"]
            else None
        )
        endpoint_by_pass[pass_id] = report

    endpoint_by_cluster: list[dict[str, Any]] = []
    for case_id in sorted(endpoint_cases):
        record = {
            "case_id": case_id,
            "cluster_id": declared[case_id]["cluster_id"],
            "family": treatment_cases[case_id]["family"],
        }
        for condition in ("P", "R"):
            values = [
                row["supported_diagnostic_success"]
                for row in rows
                if row["case_id"] == case_id and row["condition"] == condition
            ]
            record[f"{condition}_pass_values"] = values
            record[condition] = values[0] if len(values) == 2 and len(set(values)) == 1 else None
        endpoint_by_cluster.append(record)
    advantages = [
        item for item in endpoint_by_cluster if item["P"] is True and item["R"] is False
    ]

    p_guardrails = [
        row
        for row in rows
        if row["condition"] == "P"
        and row["case_id"] in set(predeclaration["scoring"]["guardrail_cases"])
    ]
    p_false_premise = [
        row
        for row in rows
        if row["condition"] == "P" and row["case_id"] == "ccv4-compensation-005"
    ]
    information_parity = True
    judge_evidence_parity = True
    for case_id in declared:
        parity = load(RESULT_ROOT / f"{case_id}.json")["information_parity"]
        information_parity = information_parity and all(
            parity[key] is True
            for key in (
                "same_robot_visible_primitive_diagnostic",
                "same_embedded_reference_computation",
                "same_source_and_configuration",
            )
        )
        information_parity = information_parity and all(
            parity[key] is False
            for key in (
                "episode_certificate_visible_to_R",
                "checked_answer_plan_visible_to_R",
                "candidate_final_answer_visible_to_R",
                "evaluator_truth_visible",
            )
        )
        information_parity = information_parity and bool(parity["baseline_deterministic_tools"])
        reference = load(reference_root / f"{case_id}.json")
        allowed = reference.get("allowed_evidence", {})
        primitive = allowed.get("primitive_diagnostic", {})
        # R was explicitly allowed the complete primitive plus relevant source/configuration.
        # A judge packet lacking either cannot validly turn uncheckable R details into errors.
        judge_evidence_parity = judge_evidence_parity and isinstance(
            primitive.get("method_input"), dict
        )
        excerpts = allowed.get("source_and_config_excerpts")
        judge_evidence_parity = (
            judge_evidence_parity and isinstance(excerpts, list) and bool(excerpts)
        )

    readiness = {
        "fixed_screen_completed_without_missing_judgments": len(rows) == 28 and not failures,
        "positive_advantage_recurs_across_independent_clusters": len(
            {item["cluster_id"] for item in advantages}
        )
        >= 2,
        "positive_advantage_in_at_least_two_mechanism_families": len(
            {item["family"] for item in advantages}
        )
        >= 2,
        "no_material_error_excess": metrics["P"]["material_errors"]
        <= metrics["R"]["material_errors"],
        "no_causal_overclaim_excess": metrics["P"]["causal_overclaims"]
        <= metrics["R"]["causal_overclaims"],
        "no_required_unit_coverage_degradation": metrics["P"]["required_unit_coverage"]
        >= metrics["R"]["required_unit_coverage"],
        "masked_evidence_qualification": all(
            row["material_error"] is False
            and row["causal_overclaim"] is False
            and row["correct_abstention"] is True
            for row in p_guardrails
        ),
        "false_premise_and_causation_handling": all(
            row["material_error"] is False
            and row["causal_overclaim"] is False
            and row["unit_status"].get("outcome") == "covered"
            and row["unit_status"].get("causation-limit") == "covered"
            for row in p_false_premise
        ),
        "information_parity": information_parity,
        "judge_received_same_permitted_evidence_as_R": judge_evidence_parity,
    }
    accepted = all(readiness.values())
    return {
        "schema": "crane-coverage-complete-v4-language-screen-result/v1",
        "status": (
            "DEVELOPMENT_ONLY_CANDIDATE_PASSED_FROZEN_GATE"
            if accepted
            else "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_FROZEN_GATE"
        ),
        "predeclaration": str(predeclaration_path.relative_to(ROOT)),
        "predeclaration_sha256": digest(predeclaration_path),
        "planned_judgments": predeclaration["judge_execution"]["planned_judgments"],
        "valid_judgments": len(rows),
        "retained_call_failures": failures,
        "condition_metrics": metrics,
        "primary_endpoint_by_pass": endpoint_by_pass,
        "primary_endpoint_by_cluster": endpoint_by_cluster,
        "readiness_gates": readiness,
        "candidate_ready_for_prospective_freeze": accepted,
        "interpretation": (
            "The candidate passed every prospectively frozen development gate. This authorizes "
            "prospective method and confirmation planning only; it is not confirmatory evidence, "
            "statistical significance, or replication."
            if accepted
            else "The candidate failed at least one prospectively frozen development gate. In this "
            "arm the judge lacked robot-visible primitive fields and source/configuration material "
            "that R was permitted to inspect, so R error labels cannot support promotion. Retain "
            "the judgments, repair packet evidence parity prospectively, and do not activate "
            "confirmation from this result."
        ),
        "confirmatory_semantic_n": 0,
        "confirmatory_alpha_consumed": 0.0,
        "summary_hashes": summary_hashes,
        "judgments": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predeclaration", type=Path, default=DEFAULT_PREDECLARATION)
    parser.add_argument("--annotation-root", type=Path, default=DEFAULT_ANNOTATION_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = aggregate(
        args.predeclaration.resolve(strict=True), args.annotation_root.resolve(strict=True)
    )
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "valid_judgments": result["valid_judgments"],
                "candidate_ready_for_prospective_freeze": result[
                    "candidate_ready_for_prospective_freeze"
                ],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
