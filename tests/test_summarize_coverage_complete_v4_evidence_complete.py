from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from summarize_coverage_complete_v4_screen import aggregate  # noqa: E402


PREDECLARATION = (
    ROOT
    / "manifests/annotation/luna-coverage-complete-v4-evidence-complete-v2-predeclaration.json"
)
ANNOTATION_ROOT = ROOT / (
    "model_outputs/automated_annotations/luna-model-judge-v1/"
    "coverage-complete-v4-language-screen-v1-evidence-complete-v2"
)


def _result():
    return aggregate(PREDECLARATION, ANNOTATION_ROOT)


def test_fair_evidence_reevaluation_rejects_candidate_advantage():
    result = _result()
    assert result["valid_judgments"] == result["planned_judgments"] == 28
    assert result["retained_call_failures"] == []
    assert result["condition_metrics"] == {
        "P": {
            "judgments": 14,
            "material_errors": 1,
            "material_error_rate": 1 / 14,
            "causal_overclaims": 0,
            "required_units_covered": 104,
            "required_units_total": 104,
            "required_unit_coverage": 1.0,
        },
        "R": {
            "judgments": 14,
            "material_errors": 1,
            "material_error_rate": 1 / 14,
            "causal_overclaims": 0,
            "required_units_covered": 99,
            "required_units_total": 104,
            "required_unit_coverage": 99 / 104,
        },
    }
    assert result["primary_endpoint_by_pass"] == {
        "pass-1": {
            "P": {"successes": 5, "total": 5},
            "R": {"successes": 5, "total": 5},
            "p_minus_r": 0.0,
        },
        "pass-2": {
            "P": {"successes": 5, "total": 5},
            "R": {"successes": 4, "total": 5},
            "p_minus_r": 0.2,
        },
    }
    assert result["readiness_gates"]["judge_received_same_permitted_evidence_as_R"] is True
    assert result["readiness_gates"]["positive_advantage_recurs_across_independent_clusters"] is False
    assert result["readiness_gates"]["positive_advantage_in_at_least_two_mechanism_families"] is False
    assert result["readiness_gates"]["masked_evidence_qualification"] is False
    assert result["candidate_ready_for_prospective_freeze"] is False
    assert result["status"] == "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_FROZEN_GATE"
    assert result["confirmatory_semantic_n"] == 0
    assert result["confirmatory_alpha_consumed"] == 0.0


def test_no_cluster_has_consensus_p_advantage_over_r():
    result = _result()
    advantages = [
        item
        for item in result["primary_endpoint_by_cluster"]
        if item["P"] is True and item["R"] is False
    ]
    assert advantages == []
    assert all(item["P"] is True for item in result["primary_endpoint_by_cluster"])
    geometry_three = next(
        item
        for item in result["primary_endpoint_by_cluster"]
        if item["case_id"] == "ccv4-geometry-003"
    )
    assert geometry_three["R"] is None
    assert geometry_three["R_pass_values"] == [True, False]
