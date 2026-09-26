from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from summarize_coverage_complete_v4_screen import (  # noqa: E402
    DEFAULT_ANNOTATION_ROOT,
    DEFAULT_PREDECLARATION,
    aggregate,
)


def _result():
    return aggregate(DEFAULT_PREDECLARATION, DEFAULT_ANNOTATION_ROOT)


def test_frozen_v4_screen_is_not_promotable_when_judge_evidence_is_incomplete():
    result = _result()
    assert result["valid_judgments"] == result["planned_judgments"] == 28
    assert result["retained_call_failures"] == []
    assert result["confirmatory_semantic_n"] == 0
    assert result["confirmatory_alpha_consumed"] == 0.0
    assert result["condition_metrics"] == {
        "P": {
            "judgments": 14,
            "material_errors": 0,
            "material_error_rate": 0.0,
            "causal_overclaims": 0,
            "required_units_covered": 104,
            "required_units_total": 104,
            "required_unit_coverage": 1.0,
        },
        "R": {
            "judgments": 14,
            "material_errors": 9,
            "material_error_rate": 9 / 14,
            "causal_overclaims": 1,
            "required_units_covered": 104,
            "required_units_total": 104,
            "required_unit_coverage": 1.0,
        },
    }
    assert result["primary_endpoint_by_pass"] == {
        "pass-1": {
            "P": {"successes": 5, "total": 5},
            "R": {"successes": 3, "total": 5},
            "p_minus_r": 0.4,
        },
        "pass-2": {
            "P": {"successes": 5, "total": 5},
            "R": {"successes": 2, "total": 5},
            "p_minus_r": 0.6,
        },
    }
    assert result["readiness_gates"]["judge_received_same_permitted_evidence_as_R"] is False
    assert all(
        value
        for key, value in result["readiness_gates"].items()
        if key != "judge_received_same_permitted_evidence_as_R"
    )
    assert result["candidate_ready_for_prospective_freeze"] is False
    assert result["status"] == "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_FROZEN_GATE"


def test_consensus_advantage_recurs_across_geometry_and_execution_clusters():
    result = _result()
    advantages = [
        item
        for item in result["primary_endpoint_by_cluster"]
        if item["P"] is True and item["R"] is False
    ]
    assert {item["cluster_id"] for item in advantages} == {
        "mccv4-land-003",
        "mccv4-land-004",
    }
    assert {item["family"] for item in advantages} == {
        "visible_obstacle_consumption_guardrail",
        "persistent_command_motion_discrepancy",
    }
    compensation = next(
        item
        for item in result["primary_endpoint_by_cluster"]
        if item["case_id"] == "ccv4-compensation-005"
    )
    assert compensation["P"] is True
    assert compensation["R"] is None
    assert compensation["R_pass_values"] == [True, False]
