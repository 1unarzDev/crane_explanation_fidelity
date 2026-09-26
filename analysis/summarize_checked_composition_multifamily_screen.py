#!/usr/bin/env python3
"""Aggregate the frozen checked-composition development screen without rejudging it."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDECLARATION = (
    ROOT
    / "manifests/annotation/luna-checked-composition-multifamily-screen-v1-predeclaration.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def metric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [row for row in rows if row["judgment_status"] == "valid"]
    errors = sum(row["material_error"] is True for row in valid)
    covered = sum(row["required_units_covered"] for row in valid)
    units = sum(row["required_units_total"] for row in valid)
    return {
        "valid_judgments": len(valid),
        "material_errors": errors,
        "material_error_rate": errors / len(valid) if valid else None,
        "required_units_covered": covered,
        "required_units_total": units,
        "required_unit_coverage": covered / units if units else None,
        "causal_overclaims": sum(row["causal_overclaim"] is True for row in valid),
        "correct_abstentions": sum(row["correct_abstention"] is True for row in valid),
    }


def aggregate(predeclaration_path: Path, annotation_root: Path) -> dict[str, Any]:
    predeclaration = load(predeclaration_path)
    if predeclaration.get("status") != "FROZEN_BEFORE_ANY_LUNA_STUDY_CALL":
        raise ValueError("screen was not frozen before Luna study calls")
    rows: list[dict[str, Any]] = []
    case_reports: list[dict[str, Any]] = []
    call_failures: list[dict[str, Any]] = []
    for artifact in predeclaration["artifacts"]:
        case_id = artifact["case_id"]
        case_root = annotation_root / case_id
        summary_path = case_root / "development-summary.json"
        summary = load(summary_path)
        key_path = (
            ROOT
            / "data/evaluator_only/dev/diagnostic-checked-composition-multifamily-screen-v1"
            / "annotation_keys"
            / f"{case_id}.json"
        )
        key = load(key_path)
        response_for = {entry["condition"]: entry["response_id"] for entry in key["entries"]}
        if set(response_for) != {"R", "P"}:
            raise ValueError(f"{case_id}: condition inventory differs from frozen R/P comparison")
        case_rows: list[dict[str, Any]] = []
        for pass_id in ("pass-1", "pass-2"):
            for condition in ("R", "P"):
                response_id = response_for[condition]
                cache_key = summary["cache_keys"].get(pass_id, {}).get(response_id)
                base = {
                    "case_id": case_id,
                    "pass_id": pass_id,
                    "condition": condition,
                    "response_id": response_id,
                }
                if cache_key is None:
                    row = {
                        **base,
                        "judgment_status": "missing_due_to_retained_call_failure",
                        "material_error": None,
                        "material_error_categories": [],
                        "required_units_covered": 0,
                        "required_units_total": 0,
                        "omitted_or_incorrect_units": [],
                        "mechanism_identification": None,
                        "correct_abstention": None,
                        "causal_overclaim": None,
                        "supported_diagnostic_success": None,
                    }
                else:
                    call_path = case_root / "calls" / "high" / pass_id / f"{cache_key}.json"
                    call = load(call_path)
                    if call.get("status") != "VALID":
                        raise ValueError(f"{case_id}/{pass_id}/{condition}: indexed call is not valid")
                    judgment = call["judgment"]
                    units = judgment["required_units"]
                    row = {
                        **base,
                        "judgment_status": "valid",
                        "call_sha256": sha256(call_path),
                        "material_error": judgment["material_error"],
                        "material_error_categories": judgment["material_error_categories"],
                        "required_units_covered": sum(
                            unit["status"] == "covered" for unit in units
                        ),
                        "required_units_total": len(units),
                        "omitted_or_incorrect_units": [
                            {"unit_id": unit["unit_id"], "status": unit["status"]}
                            for unit in units
                            if unit["status"] != "covered"
                        ],
                        "mechanism_identification": judgment["mechanism_identification"],
                        "correct_abstention": judgment["correct_abstention"],
                        "causal_overclaim": judgment["causal_overclaim"],
                        "supported_diagnostic_success": summary["passes"][pass_id][condition][
                            "supported_diagnostic_success"
                        ],
                    }
                rows.append(row)
                case_rows.append(row)
        for failure in summary["call_failures"]:
            call_failures.append({"case_id": case_id, **failure})
        case_reports.append(
            {
                "case_id": case_id,
                "summary_sha256": sha256(summary_path),
                "complete": not summary["call_failures"],
                "judgments": case_rows,
            }
        )

    paired_case_passes = {
        (row["case_id"], row["pass_id"])
        for row in rows
        if row["judgment_status"] == "valid"
    }
    paired_case_passes = {
        pair
        for pair in paired_case_passes
        if all(
            any(
                row["case_id"] == pair[0]
                and row["pass_id"] == pair[1]
                and row["condition"] == condition
                and row["judgment_status"] == "valid"
                for row in rows
            )
            for condition in ("R", "P")
        )
    }
    paired = [row for row in rows if (row["case_id"], row["pass_id"]) in paired_case_passes]

    endpoint_cases = set(predeclaration["scoring"]["primary_endpoint_cases"])
    endpoint_by_pass: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        report: dict[str, Any] = {}
        for condition in ("R", "P"):
            selected = [
                row
                for row in rows
                if row["case_id"] in endpoint_cases
                and row["pass_id"] == pass_id
                and row["condition"] == condition
                and row["judgment_status"] == "valid"
            ]
            successes = sum(row["supported_diagnostic_success"] is True for row in selected)
            report[condition] = {"successes": successes, "total": len(selected)}
        if report["R"]["total"] == report["P"]["total"] and report["R"]["total"]:
            total = report["R"]["total"]
            report["p_minus_r"] = (
                report["P"]["successes"] - report["R"]["successes"]
            ) / total
        else:
            report["p_minus_r"] = None
        endpoint_by_pass[pass_id] = report

    endpoint_consensus: list[dict[str, Any]] = []
    for case_id in sorted(endpoint_cases):
        record: dict[str, Any] = {"case_id": case_id}
        for condition in ("R", "P"):
            values = [
                row["supported_diagnostic_success"]
                for row in rows
                if row["case_id"] == case_id
                and row["condition"] == condition
                and row["judgment_status"] == "valid"
            ]
            record[condition] = values[0] if len(values) == 2 and len(set(values)) == 1 else None
            record[f"{condition}_pass_values"] = values
        endpoint_consensus.append(record)

    per_condition_all = {condition: metric([r for r in rows if r["condition"] == condition]) for condition in ("R", "P")}
    per_condition_paired = {condition: metric([r for r in paired if r["condition"] == condition]) for condition in ("R", "P")}
    p_paired = per_condition_paired["P"]
    r_paired = per_condition_paired["R"]
    readiness = {
        "fixed_screen_completed_without_missing_judgments": not call_failures,
        "recurring_positive_advantage_in_two_mechanism_families": False,
        "no_material_error_excess": p_paired["material_errors"] <= r_paired["material_errors"],
        "no_required_unit_coverage_degradation": (
            p_paired["required_unit_coverage"] >= r_paired["required_unit_coverage"]
        ),
        "all_missing_and_ambiguous_cases_appropriately_qualified": False,
        "fresh_positive_geometry_configuration_present": False,
        "fresh_visible_not_consumed_configuration_present": False,
        "fresh_out_of_model_configuration_present": False,
    }
    return {
        "schema": "crane-checked-composition-multifamily-screen-result/v1",
        "status": "DEVELOPMENT_ONLY_CANDIDATE_REJECTED",
        "predeclaration": str(predeclaration_path.relative_to(ROOT)),
        "predeclaration_sha256": sha256(predeclaration_path),
        "planned_judgments": predeclaration["judge_execution"]["planned_judgments"],
        "valid_judgments": sum(row["judgment_status"] == "valid" for row in rows),
        "retained_call_failures": call_failures,
        "statistical_boundary": predeclaration["statistical_boundary"],
        "condition_metrics_all_valid": per_condition_all,
        "condition_metrics_paired_valid": per_condition_paired,
        "primary_endpoint_by_judge_pass": endpoint_by_pass,
        "primary_endpoint_cluster_consensus": endpoint_consensus,
        "readiness_gates": readiness,
        "candidate_ready_for_confirmation": all(readiness.values()),
        "interpretation": "P did not pass the frozen development readiness gate: it had more material errors and lower required-unit coverage than R on paired valid judgments, endpoint advantage was not resolved across both Luna passes, two masked-case R judgments were invalid and retained, and the required fresh mechanism/control configurations are absent. No confirmatory effect, confidence sequence, significance result, or replication result exists.",
        "confirmatory_alpha_consumed": 0.0,
        "cases": case_reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predeclaration", type=Path, default=DEFAULT_PREDECLARATION)
    parser.add_argument(
        "--annotation-root",
        type=Path,
        default=(
            ROOT
            / "model_outputs/automated_annotations/luna-model-judge-v1"
            / "checked-composition-multifamily-screen-v1"
        ),
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = aggregate(args.predeclaration.resolve(strict=True), args.annotation_root.resolve(strict=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": result["status"],
                "valid_judgments": result["valid_judgments"],
                "candidate_ready_for_confirmation": result["candidate_ready_for_confirmation"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
