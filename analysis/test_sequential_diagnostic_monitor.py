import copy
import json
import math
from pathlib import Path

import pytest

from sequential_diagnostic_monitor import (
    analyze,
    log_mixture_e_value,
    lower_confidence_bound,
    protocol_sha256,
    upper_confidence_bound,
    validate_ledger,
    validate_protocol,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads(
    (
        ROOT
        / "research/explanation_fidelity/experiment_configs/prospective/"
        "diagnostic-sequential-protocol-v2.json"
    ).read_text(encoding="utf-8")
)
LEDGER = json.loads(
    (ROOT / "manifests/study/diagnostic-sequential-error-ledger-v2.json").read_text(
        encoding="utf-8"
    )
)
BET_FRACTIONS = tuple(PROTOCOL["analysis"]["betting_fractions"])


def _row(index: int, *, ambiguous: bool = False) -> dict:
    stratum = "land-motion-ambiguous" if ambiguous else "land-motion-adverse"
    probability = 0.08 if ambiguous else 0.16
    return {
        "cluster_id": f"new-cluster-{index:04d}",
        "configuration_id": f"new-configuration-{index:04d}",
        "sequence_index": index + 1,
        "independent_cluster": True,
        "stratum_id": stratum,
        "declared_sampling_probability": probability,
        "answerability": "ambiguous" if ambiguous else "diagnosable",
        "supported_diagnostic_success_p": 1,
        "supported_diagnostic_success_r": 0,
        "material_error_p": 0,
        "material_error_r": 1,
        "useful_coverage_p": 1.0,
        "useful_coverage_r": 0.0,
        "correct_ambiguity_handling_p": 1,
        "correct_ambiguity_handling_r": 0,
    }


def _payload(count: int = 120) -> dict:
    rows = [_row(index, ambiguous=index % 5 == 0) for index in range(count)]
    return {
        "schema": "crane-diagnostic-sequential-results/v1",
        "campaign_id": "diagnostic-seq-test-v1",
        "protocol_id": PROTOCOL["protocol_id"],
        "protocol_sha256": protocol_sha256(PROTOCOL),
        "alpha_allocation_id": "candidate-v1-confirmation",
        "development_or_legacy_data_included": False,
        "outcomes_inspected_before_freeze": False,
        "sampling_rule_changed_after_outcomes": False,
        "campaign_registration": {
            "registered_before_outcomes": True,
            "information_tool_resource_parity_audited": True,
            "frozen_hashes": {
                key: "a" * 64
                for key in (
                    "proposed_method",
                    "baseline",
                    "evidence_contract",
                    "target_sampler",
                    "question_references",
                    "luna_judge",
                    "analysis_code",
                )
            },
        },
        "judge_quality": {
            "heldout_qualification_passed": True,
            "frozen_configuration_used": True,
            "qualification_manifest_sha256": "b" * 64,
            "two_isolated_passes_completed": True,
            "unresolved_labels": 0,
            "maximum_allowed_unresolved_labels": 0,
        },
        "clusters": rows,
    }


def _analyze(payload: dict) -> dict:
    ledger = copy.deepcopy(LEDGER)
    if payload["clusters"]:
        allocation = next(
            item
            for item in ledger["allocations"]
            if item["allocation_id"] == payload["alpha_allocation_id"]
        )
        allocation["status"] = "CONSUMED"
        allocation["campaign_id"] = payload["campaign_id"]
        allocation["consumed_at"] = "2026-09-23T12:00:00Z"
        ledger["consumed_alpha"] = allocation["alpha"]
    return analyze(payload, PROTOCOL, ledger)


def test_protocol_alpha_and_target_distribution_are_closed():
    validate_protocol(PROTOCOL)
    validate_ledger(LEDGER, PROTOCOL)
    assert sum(item["alpha"] for item in PROTOCOL["error_budget_ledger"]["allocations"]) == 0.05
    assert math.isclose(
        sum(item["probability"] for item in PROTOCOL["target_distribution"]["strata"]),
        1.0,
    )


def test_tracked_empty_dry_run_reproduces_not_ready_state():
    payload = json.loads(
        (ROOT / "configs/fixtures/diagnostic-sequential-empty-dry-run.json").read_text(
            encoding="utf-8"
        )
    )
    result = _analyze(payload)
    assert result["status"] == "CONTINUE"
    assert result["allowed_conclusion"] == "meaningful_advantage_not_established"
    assert result["independent_clusters"] == 0
    assert result["judge_ready"] is False


def test_one_step_mixture_is_supermartingale_under_boundary_null():
    # Exhaustive support {-1, 0, 1}; this checks the implementation identity for several null
    # distributions.  The mathematical guarantee still comes from the nonnegative-factor proof,
    # not from this finite test.
    null_mean = 0.15
    for plus, minus in ((0.15, 0.0), (0.3, 0.15), (0.05, 0.0)):
        zero = 1.0 - plus - minus
        expected = sum(
            probability
            * math.exp(log_mixture_e_value([value], null_mean, BET_FRACTIONS))
            for value, probability in ((1.0, plus), (-1.0, minus), (0.0, zero))
        )
        assert expected <= 1.0 + 1e-12


def test_bounds_tighten_in_the_supported_direction():
    favorable = [1.0] * 200
    assert lower_confidence_bound(favorable, 0.005, BET_FRACTIONS) > 0.15
    assert (
        upper_confidence_bound(
            [-item for item in favorable], 0.005, BET_FRACTIONS
        )
        < -0.15
    )


def test_zero_differences_can_establish_declared_guardrails_before_maximum():
    values = [0.0] * 800
    assert upper_confidence_bound(values, 0.005, BET_FRACTIONS) < 0.02
    assert lower_confidence_bound(values[:160], 0.005, BET_FRACTIONS) > -0.05


def test_out_of_range_observations_are_rejected_not_clipped():
    with pytest.raises(ValueError, match="observations must be"):
        log_mixture_e_value([1.01], 0.15, BET_FRACTIONS)


def test_all_corrected_gates_are_required_for_success():
    result = _analyze(_payload())
    assert result["status"] == "SUCCESS"
    assert all(item["passed"] for item in result["endpoints"].values())
    assert result["per_gate_intersection_union_alpha"] == 0.02

    failed = _payload()
    for row in failed["clusters"]:
        row["material_error_p"] = 1
        row["material_error_r"] = 0
    result = _analyze(failed)
    assert not result["endpoints"]["material_error_difference"]["passed"]
    assert result["status"] != "SUCCESS"


def test_judge_failure_blocks_success_even_when_outcomes_are_favorable():
    payload = _payload()
    payload["judge_quality"]["heldout_qualification_passed"] = False
    result = _analyze(payload)
    assert result["judge_ready"] is False
    assert result["status"] != "SUCCESS"


def test_legacy_development_duplicates_and_adaptive_sampling_fail_closed():
    payload = _payload()
    payload["campaign_id"] = "legacy-fgh-retrofit"
    with pytest.raises(ValueError, match="new diagnostic-seq namespace"):
        _analyze(payload)

    payload = _payload()
    payload["clusters"][1]["cluster_id"] = payload["clusters"][0]["cluster_id"]
    with pytest.raises(ValueError, match="duplicate cluster"):
        _analyze(payload)

    payload = _payload()
    payload["sampling_rule_changed_after_outcomes"] = True
    with pytest.raises(ValueError, match="outcome-adaptive"):
        _analyze(payload)


def test_duplicate_configuration_bad_order_and_answerability_fail_closed():
    payload = _payload()
    payload["clusters"][1]["configuration_id"] = payload["clusters"][0]["configuration_id"]
    with pytest.raises(ValueError, match="configuration reuse"):
        _analyze(payload)

    payload = _payload()
    payload["clusters"][1]["sequence_index"] = 99
    with pytest.raises(ValueError, match="chronological sequence"):
        _analyze(payload)

    payload = _payload()
    payload["clusters"][0]["answerability"] = "diagnosable"
    assert payload["clusters"][0]["stratum_id"].endswith("-ambiguous")
    with pytest.raises(ValueError, match="answerability disagrees"):
        _analyze(payload)


def test_protocol_hash_freeze_and_resource_parity_fail_closed():
    payload = _payload()
    payload["protocol_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="protocol hash"):
        _analyze(payload)

    payload = _payload()
    payload["campaign_registration"]["information_tool_resource_parity_audited"] = False
    with pytest.raises(ValueError, match="resource parity"):
        _analyze(payload)


def test_replication_requires_fresh_configurations_and_same_frozen_method():
    payload = _payload()
    payload["alpha_allocation_id"] = "selected-method-replication"
    payload["replication"] = {
        "same_frozen_method_and_baseline": True,
        "fresh_configuration_overlap_count": 0,
        "discovery_response_reuse_count": 0,
    }
    assert _analyze(payload)["status"] == "SUCCESS"

    changed = copy.deepcopy(payload)
    changed["replication"]["fresh_configuration_overlap_count"] = 1
    result = _analyze(changed)
    assert result["replication_requirements_met"] is False
    assert result["status"] != "SUCCESS"


def test_alpha_ledger_overallocation_is_rejected():
    changed = copy.deepcopy(PROTOCOL)
    changed["error_budget_ledger"]["allocations"][0]["alpha"] = 0.5
    with pytest.raises(ValueError, match="exceeds program alpha"):
        validate_protocol(changed)


def test_nonempty_campaign_requires_irrevocably_bound_alpha():
    payload = _payload()
    with pytest.raises(ValueError, match="consumed by this campaign"):
        analyze(payload, PROTOCOL, LEDGER)

    changed = copy.deepcopy(LEDGER)
    changed["allocations"][0]["status"] = "CONSUMED"
    changed["allocations"][0]["campaign_id"] = "different-campaign"
    changed["allocations"][0]["consumed_at"] = "2026-09-23T12:00:00Z"
    changed["consumed_alpha"] = 0.02
    with pytest.raises(ValueError, match="consumed by this campaign"):
        analyze(payload, PROTOCOL, changed)


def test_cumulative_ledger_cannot_refund_or_misstate_consumed_alpha():
    changed = copy.deepcopy(LEDGER)
    changed["allocations"][0]["status"] = "CONSUMED"
    changed["allocations"][0]["campaign_id"] = "diagnostic-seq-failed-v1"
    changed["allocations"][0]["consumed_at"] = "2026-09-23T12:00:00Z"
    with pytest.raises(ValueError, match="consumed alpha is inconsistent"):
        validate_ledger(changed, PROTOCOL)
