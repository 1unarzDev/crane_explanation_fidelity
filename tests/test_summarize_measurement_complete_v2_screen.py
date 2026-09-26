from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from summarize_measurement_complete_v2_screen import (  # noqa: E402
    DEFAULT_ANNOTATION_ROOT,
    DEFAULT_PACKET_FREEZE,
    DEFAULT_PREDECLARATION,
    aggregate,
)


def test_frozen_screen_result_is_favorable_but_fails_exact_coverage_gate() -> None:
    result = aggregate(
        DEFAULT_PREDECLARATION,
        DEFAULT_PACKET_FREEZE,
        DEFAULT_ANNOTATION_ROOT,
    )
    assert result["valid_judgments"] == result["planned_judgments"] == 36
    assert result["retained_call_failures"] == []
    assert result["confirmatory_alpha_consumed"] == 0.0
    assert result["primary_endpoint_by_pass"] == {
        "pass-1": {
            "P": {"successes": 4, "total": 4},
            "R": {"successes": 1, "total": 4},
            "p_minus_r": 0.75,
        },
        "pass-2": {
            "P": {"successes": 4, "total": 4},
            "R": {"successes": 1, "total": 4},
            "p_minus_r": 0.75,
        },
    }
    assert result["condition_metrics"]["P"] == {
        "judgments": 18,
        "material_errors": 0,
        "material_error_rate": 0.0,
        "causal_overclaims": 0,
        "required_units_covered": 108,
        "required_units_total": 126,
        "required_unit_coverage": 108 / 126,
    }
    assert result["condition_metrics"]["R"]["material_errors"] == 14
    assert result["condition_metrics"]["R"]["causal_overclaims"] == 1
    assert result["condition_metrics"]["R"]["required_units_covered"] == 113
    assert result["condition_metrics"]["R"]["required_units_total"] == 126
    assert result["readiness_gates"] == {
        "fixed_screen_completed_without_missing_judgments": True,
        "positive_advantage_recurs_across_independent_clusters": True,
        "positive_advantage_in_at_least_two_mechanism_families": True,
        "no_material_error_excess": True,
        "no_required_unit_coverage_degradation": False,
        "masked_ambiguous_and_false_premise_qualification": True,
        "information_parity": True,
    }
    assert result["candidate_ready_for_confirmation"] is False
    assert result["status"] == "DEVELOPMENT_ONLY_CANDIDATE_REJECTED_COVERAGE_GATE"


def test_cluster_consensus_has_three_p_wins_one_tie_across_two_families() -> None:
    result = aggregate(
        DEFAULT_PREDECLARATION,
        DEFAULT_PACKET_FREEZE,
        DEFAULT_ANNOTATION_ROOT,
    )
    cases = result["primary_endpoint_by_cluster"]
    wins = [item for item in cases if item["P"] is True and item["R"] is False]
    ties = [item for item in cases if item["P"] is True and item["R"] is True]
    assert len(wins) == 3
    assert len(ties) == 1
    assert len({item["cluster_id"] for item in wins}) == 3
    assert {item["family"] for item in wins} == {
        "bounded_geometric_restriction",
        "persistent_execution_discrepancy_mixed_layout",
        "successful_command_motion_compensation",
    }
