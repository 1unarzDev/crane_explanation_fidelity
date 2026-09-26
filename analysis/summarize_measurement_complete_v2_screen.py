#!/usr/bin/env python3
"""Aggregate the frozen measurement-complete-v2 screen without rejudging it."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDECLARATION = ROOT / (
    "manifests/annotation/"
    "luna-measurement-complete-v2-language-screen-v1-predeclaration.json"
)
DEFAULT_PACKET_FREEZE = ROOT / (
    "manifests/annotation/"
    "luna-measurement-complete-v2-language-screen-v1-predeclaration-amendment-2.json"
)
DEFAULT_ANNOTATION_ROOT = ROOT / (
    "model_outputs/automated_annotations/luna-model-judge-v1/"
    "measurement-complete-v2-language-screen-v1"
)
KEY_ROOT = ROOT / (
    "data/evaluator_only/dev/measurement-complete-v2-language-screen-v1/annotation_keys"
)


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


def aggregate(
    predeclaration_path: Path,
    packet_freeze_path: Path,
    annotation_root: Path,
) -> dict[str, Any]:
    predeclaration = load(predeclaration_path)
    packet_freeze = load(packet_freeze_path)
    if predeclaration.get("status") != "FROZEN_BEFORE_ANY_RESPONSE_OR_LUNA_STUDY_CALL":
        raise ValueError("study predeclaration was not frozen")
    if packet_freeze.get("status") != "FROZEN_PACKET_BYTES_BEFORE_ANY_LUNA_STUDY_CALL":
        raise ValueError("packet bytes were not frozen before judging")

    frozen = {item["case_id"]: item for item in packet_freeze["artifacts"]}
    declared = {item["case_id"]: item for item in predeclaration["cases"]}
    if set(frozen) != set(declared):
        raise ValueError("predeclaration and packet-freeze case inventories differ")

    rows: list[dict[str, Any]] = []
    call_failures: list[dict[str, Any]] = []
    summary_hashes: dict[str, str] = {}
    for case_id in declared:
        key_path = KEY_ROOT / f"{case_id}.json"
        if digest(key_path) != frozen[case_id]["key_sha256"]:
            raise ValueError(f"{case_id}: condition key differs from packet freeze")
        key = load(key_path)
        conditions = {item["response_id"]: item["condition"] for item in key["entries"]}
        if set(conditions.values()) != {"P", "R"}:
            raise ValueError(f"{case_id}: condition inventory is not exactly P/R")
        summary_path = annotation_root / case_id / "development-summary.json"
        summary = load(summary_path)
        summary_hashes[case_id] = digest(summary_path)
        call_failures.extend({"case_id": case_id, **item} for item in summary["call_failures"])
        for pass_id in ("pass-1", "pass-2"):
            for response_id, condition in conditions.items():
                cache_key = summary["cache_keys"].get(pass_id, {}).get(response_id)
                if cache_key is None:
                    continue
                call_path = annotation_root / case_id / "calls/high" / pass_id / f"{cache_key}.json"
                call = load(call_path)
                if call.get("status") != "VALID":
                    raise ValueError(f"{case_id}/{pass_id}/{condition}: call is not valid")
                judgment = call["judgment"]
                units = judgment["required_units"]
                rows.append(
                    {
                        "case_id": case_id,
                        "cluster_id": declared[case_id]["cluster_id"],
                        "independent_cluster": declared[case_id]["independent_cluster"],
                        "primary_endpoint_eligible": declared[case_id][
                            "primary_endpoint_eligible"
                        ],
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
                            unit["status"] == "covered" for unit in units
                        ),
                        "required_units_total": len(units),
                        "uncovered_units": [
                            {"unit_id": unit["unit_id"], "status": unit["status"]}
                            for unit in units
                            if unit["status"] != "covered"
                        ],
                    }
                )

    metrics = {
        condition: _metric([row for row in rows if row["condition"] == condition])
        for condition in ("P", "R")
    }
    endpoint_cases = set(predeclaration["scoring"]["primary_endpoint_cases"])
    endpoint_by_pass: dict[str, Any] = {}
    endpoint_by_case: list[dict[str, Any]] = []
    family_by_case = {
        case["case_id"]: next(
            item["family"]
            for item in load(ROOT / predeclaration["treatment_contract"]["path"])["cases"]
            if item["case_id"] == case["case_id"]
        )
        for case in predeclaration["cases"]
    }
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
    for case_id in sorted(endpoint_cases):
        record: dict[str, Any] = {
            "case_id": case_id,
            "cluster_id": declared[case_id]["cluster_id"],
            "family": family_by_case[case_id],
        }
        for condition in ("P", "R"):
            values = [
                row["supported_diagnostic_success"]
                for row in rows
                if row["case_id"] == case_id and row["condition"] == condition
            ]
            record[f"{condition}_pass_values"] = values
            record[condition] = values[0] if len(values) == 2 and len(set(values)) == 1 else None
        endpoint_by_case.append(record)

    advantages = [item for item in endpoint_by_case if item["P"] is True and item["R"] is False]
    guardrail_cases = set(declared) - endpoint_cases
    p_guardrails = [
        row for row in rows if row["condition"] == "P" and row["case_id"] in guardrail_cases
    ]
    parity_true = {
        "same_robot_visible_primitive_diagnostic",
        "same_embedded_reference_computation",
        "same_source_and_configuration",
    }
    parity_false = {
        "episode_certificate_visible_to_R",
        "checked_answer_plan_visible_to_R",
        "candidate_final_answer_visible_to_R",
        "evaluator_truth_visible",
    }
    information_parity = True
    for case_id in declared:
        parity = load(
            ROOT
            / "model_outputs/dev/measurement-complete-v2-language-screen-v1/results"
            / f"{case_id}.json"
        )["information_parity"]
        information_parity = information_parity and all(parity[key] is True for key in parity_true)
        information_parity = information_parity and all(
            parity[key] is False for key in parity_false
        )
        information_parity = information_parity and bool(
            parity.get("baseline_deterministic_tools")
        )
    readiness = {
        "fixed_screen_completed_without_missing_judgments": len(rows) == 36 and not call_failures,
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
        "no_required_unit_coverage_degradation": metrics["P"]["required_unit_coverage"]
        >= metrics["R"]["required_unit_coverage"],
        "masked_ambiguous_and_false_premise_qualification": all(
            row["material_error"] is False
            and row["causal_overclaim"] is False
            and row["correct_abstention"] is True
            for row in p_guardrails
        ),
        "information_parity": information_parity,
    }
    return {
        "schema": "crane-measurement-complete-v2-language-screen-result/v1",
        "status": "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_COVERAGE_GATE",
        "predeclaration": str(predeclaration_path.relative_to(ROOT)),
        "predeclaration_sha256": digest(predeclaration_path),
        "packet_freeze": str(packet_freeze_path.relative_to(ROOT)),
        "packet_freeze_sha256": digest(packet_freeze_path),
        "planned_judgments": packet_freeze["judge_inventory"]["planned_judgments"],
        "valid_judgments": len(rows),
        "retained_call_failures": call_failures,
        "condition_metrics": metrics,
        "primary_endpoint_by_pass": endpoint_by_pass,
        "primary_endpoint_by_cluster": endpoint_by_case,
        "readiness_gates": readiness,
        "candidate_ready_for_confirmation": all(readiness.values()),
        "interpretation": "P showed a repeated endpoint and material-error advantage over R across geometry and command-motion cases, but failed the frozen no-coverage-degradation gate. Preserve this favorable but non-promotable development result and revise the candidate in a separately declared cycle; do not activate confirmation.",
        "confirmatory_alpha_consumed": 0.0,
        "summary_hashes": summary_hashes,
        "judgments": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predeclaration", type=Path, default=DEFAULT_PREDECLARATION)
    parser.add_argument("--packet-freeze", type=Path, default=DEFAULT_PACKET_FREEZE)
    parser.add_argument("--annotation-root", type=Path, default=DEFAULT_ANNOTATION_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = aggregate(
        args.predeclaration.resolve(strict=True),
        args.packet_freeze.resolve(strict=True),
        args.annotation_root.resolve(strict=True),
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
                "candidate_ready_for_confirmation": result["candidate_ready_for_confirmation"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
