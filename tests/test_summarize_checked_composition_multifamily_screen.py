from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis/summarize_checked_composition_multifamily_screen.py"
SPEC = importlib.util.spec_from_file_location("summarize_checked_screen", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_retained_screen_rejects_candidate_without_inflating_n() -> None:
    result = MODULE.aggregate(
        MODULE.DEFAULT_PREDECLARATION,
        ROOT
        / "model_outputs/automated_annotations/luna-model-judge-v1"
        / "checked-composition-multifamily-screen-v1",
    )
    assert result["status"] == "DEVELOPMENT_ONLY_CANDIDATE_REJECTED"
    assert result["valid_judgments"] == 26
    assert len(result["retained_call_failures"]) == 2
    assert result["statistical_boundary"]["independent_clusters"] == 6
    assert result["statistical_boundary"]["paired_masks_add_clusters"] == 0
    assert result["confirmatory_alpha_consumed"] == 0.0
    assert result["candidate_ready_for_confirmation"] is False


def test_retained_screen_reports_risk_and_coverage_without_hiding_missing_labels() -> None:
    result = MODULE.aggregate(
        MODULE.DEFAULT_PREDECLARATION,
        ROOT
        / "model_outputs/automated_annotations/luna-model-judge-v1"
        / "checked-composition-multifamily-screen-v1",
    )
    paired = result["condition_metrics_paired_valid"]
    assert paired["R"]["valid_judgments"] == 12
    assert paired["P"]["valid_judgments"] == 12
    assert paired["R"]["material_errors"] == 8
    assert paired["P"]["material_errors"] == 10
    assert paired["R"]["required_units_covered"] == 86
    assert paired["P"]["required_units_covered"] == 84
    assert paired["R"]["required_units_total"] == 92
    assert paired["P"]["required_units_total"] == 92
    assert result["readiness_gates"]["no_material_error_excess"] is False
    assert result["readiness_gates"]["no_required_unit_coverage_degradation"] is False


def test_endpoint_is_pass_specific_and_disagreement_stays_unresolved() -> None:
    result = MODULE.aggregate(
        MODULE.DEFAULT_PREDECLARATION,
        ROOT
        / "model_outputs/automated_annotations/luna-model-judge-v1"
        / "checked-composition-multifamily-screen-v1",
    )
    by_pass = result["primary_endpoint_by_judge_pass"]
    assert by_pass["pass-1"]["p_minus_r"] == 0.0
    assert by_pass["pass-2"]["p_minus_r"] == 0.5
    compensation = next(
        row
        for row in result["primary_endpoint_cluster_consensus"]
        if row["case_id"] == "ccdev-compensation-002"
    )
    assert compensation["P"] is None
    assert compensation["P_pass_values"] == [False, True]


def test_result_manifest_pins_retained_aggregate() -> None:
    manifest_path = (
        ROOT
        / "manifests/annotation/luna-checked-composition-multifamily-screen-v1-result.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result_path = ROOT / manifest["result"]
    assert manifest["result_sha256"] == hashlib.sha256(result_path.read_bytes()).hexdigest()
    assert manifest["status"] == "DEVELOPMENT_ONLY_CANDIDATE_REJECTED"
    assert manifest["execution"]["independent_scenario_clusters"] == 6
    assert manifest["execution"]["paired_masks_add_clusters"] == 0
    assert manifest["readiness"]["candidate_ready_for_confirmation"] is False
    assert manifest["confirmatory_semantic_n"] == 0
    assert manifest["confirmatory_alpha_consumed"] == 0.0
