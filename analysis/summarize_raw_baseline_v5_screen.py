#!/usr/bin/env python3
"""Aggregate the frozen raw-baseline-v5 Luna arm without rejudging responses."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PREDECLARATION = ROOT / (
    "manifests/annotation/luna-raw-baseline-v5-language-screen-v1-predeclaration.json"
)
DEFAULT_ANNOTATION_ROOT = ROOT / (
    "model_outputs/automated_annotations/luna-model-judge-v1/"
    "raw-baseline-v5-language-screen-v1"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def _verify_file_manifest(path: Path, expected_sha256: str, count_field: str, count: int) -> None:
    if digest(path) != expected_sha256:
        raise ValueError(f"frozen manifest hash mismatch: {path}")
    manifest = load(path)
    entries = manifest[count_field]
    if entries != count:
        raise ValueError(f"frozen manifest count mismatch: {path}")
    items = manifest.get("artifacts", manifest.get("files", []))
    for item in items:
        artifact = ROOT / item["path"]
        if artifact.stat().st_size != item["bytes"] or digest(artifact) != item["sha256"]:
            raise ValueError(f"frozen artifact differs: {item['path']}")


def _metric(rows: list[dict[str, Any]]) -> dict[str, Any]:
    covered = sum(row["required_units_covered"] for row in rows)
    total = sum(row["required_units_total"] for row in rows)
    return {
        "judgments": len(rows),
        "material_errors": sum(row["material_error"] is True for row in rows),
        "material_error_rate": (
            sum(row["material_error"] is True for row in rows) / len(rows) if rows else None
        ),
        "causal_overclaims": sum(row["causal_overclaim"] is True for row in rows),
        "evidence_problems": sum(row["evidence_problem"] is True for row in rows),
        "judge_unresolved_fields": sum(len(row["unresolved_fields"]) for row in rows),
        "required_units_covered": covered,
        "required_units_total": total,
        "required_unit_coverage": covered / total if total else None,
    }


def aggregate(predeclaration_path: Path, annotation_root: Path) -> dict[str, Any]:
    predeclaration = load(predeclaration_path)
    if predeclaration.get("status") != "FROZEN_BEFORE_ANY_LUNA_STUDY_CALL":
        raise ValueError("Luna arm was not frozen before calls")
    frozen = predeclaration["frozen_artifacts"]
    _verify_file_manifest(
        ROOT / frozen["results_references_packets_manifest"],
        frozen["results_references_packets_manifest_sha256"],
        "artifact_count",
        frozen["artifact_count"],
    )
    _verify_file_manifest(
        ROOT / frozen["condition_key_manifest"],
        frozen["condition_key_manifest_sha256"],
        "file_count",
        frozen["condition_key_count"],
    )

    contract = load(ROOT / predeclaration["treatment_contract"]["path"])
    treatment_cases = {item["case_id"]: item for item in contract["cases"]}
    declared = {item["case_id"]: item for item in predeclaration["cases"]}
    if len(declared) != len(predeclaration["cases"]) or set(declared) != set(treatment_cases):
        raise ValueError("treatment and annotation case inventories differ")

    arm_id = predeclaration["arm_id"]
    key_root = ROOT / f"data/evaluator_only/dev/{arm_id}/annotation_keys"
    reference_root = ROOT / f"model_outputs/dev/{arm_id}/references"
    result_root = ROOT / f"model_outputs/dev/{arm_id}/results"
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    summary_hashes: dict[str, str] = {}
    for case_id, case in declared.items():
        key = load(key_root / f"{case_id}.json")
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
                        "mechanism_unit_id": case.get("mechanism_unit_id"),
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
                        "evidence_problem": judgment["evidence_problem"],
                        "unresolved_fields": judgment["unresolved_fields"],
                        "required_units_covered": sum(item["status"] == "covered" for item in units),
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
        record: dict[str, Any] = {
            "case_id": case_id,
            "cluster_id": declared[case_id]["cluster_id"],
            "family": treatment_cases[case_id]["family"],
            "mechanism_unit_id": declared[case_id]["mechanism_unit_id"],
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
    advantages = [item for item in endpoint_by_cluster if item["P"] is True and item["R"] is False]

    guardrail_cases = set(predeclaration["scoring"]["guardrail_cases"])
    p_guardrails = [
        row for row in rows if row["condition"] == "P" and row["case_id"] in guardrail_cases
    ]
    p_false_premise = [
        row
        for row in rows
        if row["condition"] == "P" and row["case_id"] == "ccv5-compensation-005"
    ]
    information_parity = True
    judge_evidence_parity = True
    for case_id in declared:
        parity = load(result_root / f"{case_id}.json")["information_parity"]
        information_parity = information_parity and all(
            parity[key] is True
            for key in (
                "same_underlying_robot_visible_observations",
                "same_relevant_source_and_configuration",
                "same_executable_diagnostic_tools",
                "baseline_receives_raw_observations",
            )
        )
        information_parity = information_parity and all(
            parity[key] is False
            for key in (
                "precomputed_diagnostic_visible_to_R",
                "precomputed_reference_computation_visible_to_R",
                "episode_certificate_visible_to_R",
                "checked_answer_plan_visible_to_R",
                "candidate_final_answer_visible_to_R",
                "evaluator_truth_visible",
            )
        )
        information_parity = information_parity and bool(parity["baseline_deterministic_tools"])
        reference = load(reference_root / f"{case_id}.json")
        audit = reference.get("completeness_audit", {})
        allowed = reference.get("allowed_evidence", {})
        raw_binding = allowed.get("raw_robot_visible_evidence_binding", {})
        judge_evidence_parity = judge_evidence_parity and all(
            audit.get(field) is True
            for field in (
                "raw_baseline_hash_verified",
                "proposed_diagnostic_excluded_from_gold",
                "evaluator_truth_excluded",
                "independent_measurements_matched",
            )
        )
        # A content hash and compact inventory do not let the judge verify arbitrary
        # measurements that R legitimately computed from the full raw samples/cells.
        judge_evidence_parity = judge_evidence_parity and (
            raw_binding.get("complete_raw_observations_available_to_judge") is True
        )
        judge_evidence_parity = judge_evidence_parity and all(
            field in allowed
            for field in (
                "independent_reference_computations",
                "raw_robot_visible_evidence_binding",
            )
        )

    readiness = {
        "fixed_screen_completed_without_missing_judgments": len(rows) == 28 and not failures,
        "positive_advantage_recurs_across_independent_clusters": len(
            {item["cluster_id"] for item in advantages}
        )
        >= 2,
        "positive_advantage_in_at_least_two_mechanism_families": len(
            {item["mechanism_unit_id"] for item in advantages}
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
        "judge_evidence_parity": judge_evidence_parity,
        "no_judge_evidence_problem": metrics["P"]["evidence_problems"] == 0
        and metrics["R"]["evidence_problems"] == 0,
    }
    accepted = all(readiness.values())
    return {
        "schema": "crane-raw-baseline-v5-language-screen-result/v1",
        "status": (
            "DEVELOPMENT_ONLY_CANDIDATE_PASSED_FROZEN_GATE"
            if accepted
            else "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_FROZEN_GATE"
        ),
        "predeclaration": predeclaration_path.relative_to(ROOT).as_posix(),
        "predeclaration_sha256": digest(predeclaration_path),
        "planned_judgments": predeclaration["judge_execution"]["planned_judgments"],
        "valid_judgments": len(rows),
        "retained_call_failures": failures,
        "condition_metrics": metrics,
        "primary_endpoint_by_pass": endpoint_by_pass,
        "primary_endpoint_by_cluster": endpoint_by_cluster,
        "consensus_p_advantage_clusters": advantages,
        "readiness_gates": readiness,
        "candidate_ready_for_prospective_freeze": accepted,
        "interpretation": (
            "The candidate passed every frozen development gate. This authorizes only a fresh "
            "prospective method freeze and confirmation plan; these reused development clusters "
            "are not confirmatory evidence, statistical significance, or replication."
            if accepted
            else (
                "The candidate failed at least one frozen development gate. In this arm Luna "
                "received independent endpoint computations and a compact raw-evidence binding, "
                "but not every raw observation R was permitted to inspect. Claims that Luna called "
                "unsupported may be independently checkable from omitted raw samples or cells. "
                "Retain the judgments, repair judge evidence parity prospectively, and do not "
                "activate confirmation or claim a diagnostic advantage from this result."
            )
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
