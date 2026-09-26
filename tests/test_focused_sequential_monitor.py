import copy
import hashlib
import json
from pathlib import Path

import pytest

from focused_sequential_monitor import analyze, validate_inputs
from run_focused_response_pair import verify_freeze


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1.json"
FREEZE_PATH = ROOT / "research/explanation_fidelity/experiment_configs/prospective/focused-supported-diagnostic-communication-v1-resource-freeze.json"
LEDGER_PATH = ROOT / "manifests/study/diagnostic-sequential-error-ledger-v2.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def payload() -> dict:
    return {
        "schema": "crane-focused-supported-diagnostic-results/v1",
        "campaign_id": "focused-supported-diagnostic-communication-v1-confirmation",
        "protocol_id": "focused-supported-diagnostic-communication-v1",
        "protocol_sha256": hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest(),
        "resource_freeze_sha256": hashlib.sha256(FREEZE_PATH.read_bytes()).hexdigest(),
        "development_or_legacy_data_included": False,
        "sampling_rule_changed_after_outcomes": False,
        "judge": {
            "qualification_id": "luna-model-judge-v12-complete-endpoint-extension-v1",
            "two_isolated_passes": True,
        },
        "clusters": [],
    }


def row(index: int, family: str = "persistent_command_motion_discrepancy") -> dict:
    return {
        "cluster_id": f"focused-{index:03d}",
        "configuration_id": f"configuration-{index:03d}",
        "sequence_index": index,
        "independent_scenario_configuration": True,
        "family": family,
        "primary_endpoint_eligible": True,
        "complete_supported_diagnostic_communication_p": 1,
        "complete_supported_diagnostic_communication_r": 0,
        "material_error_p": 0,
        "material_error_r": 0,
        "mechanism_correct_p": 1,
        "mechanism_correct_r": 0,
        "measurement_correct_p": 1,
        "measurement_correct_r": 0,
        "causal_limit_preserved_p": 1,
        "causal_limit_preserved_r": 1,
        "essential_unit_total": 4,
        "essential_units_covered_p": 4,
        "essential_units_covered_r": 2,
    }


def bound_ledger(payload_value: dict) -> dict:
    ledger = load(LEDGER_PATH)
    allocation = next(x for x in ledger["allocations"] if x["allocation_id"] == "candidate-v1-confirmation")
    allocation.update(status="CONSUMED", campaign_id=payload_value["campaign_id"], consumed_at="2026-09-26T00:00:00Z")
    ledger["consumed_alpha"] = 0.02
    return ledger


def test_empty_dry_run_is_valid_without_consuming_alpha():
    value = payload()
    result = analyze(value, load(PROTOCOL_PATH), load(LEDGER_PATH), load(FREEZE_PATH))
    assert result["status"] == "CONTINUE"
    assert result["primary_eligible_count"] == 0
    assert result["allowed_conclusion"] == "focused_benefit_not_established"


def test_frozen_resource_inventory_and_exact_runner_are_present():
    freeze = load(FREEZE_PATH)
    verify_freeze(freeze)
    assert freeze["baseline"]["requested_model_id"] == "gpt-6-sol"
    assert freeze["baseline"]["reasoning_effort"] == "high"
    assert freeze["baseline"]["substitution_allowed"] is False
    assert freeze["repositories"]["crane_ml"]["commit"] == "05a1161e4b5a3ad6bbefe1c635507e7061ea8d58"
    assert freeze["repositories"]["astro_dock_diagnostic_core"]["commit"] == "bea12562324fa2caf9290698cfadddcb22bd8a8b"
    assert "response_pair_runner" in freeze["artifact_sha256"]


def test_nonempty_results_require_atomic_alpha_binding():
    value = payload()
    value["clusters"] = [row(1)]
    with pytest.raises(ValueError, match="atomically bound"):
        validate_inputs(value, load(PROTOCOL_PATH), load(LEDGER_PATH), load(FREEZE_PATH))


def test_complete_endpoint_fails_closed_on_missing_component():
    value = payload()
    bad = row(1)
    bad["measurement_correct_p"] = 0
    value["clusters"] = [bad]
    with pytest.raises(ValueError, match="component fields"):
        validate_inputs(value, load(PROTOCOL_PATH), bound_ledger(value), load(FREEZE_PATH))


def test_variants_or_reused_configurations_cannot_increment_n():
    value = payload()
    value["clusters"] = [row(1), row(2)]
    value["clusters"][1]["configuration_id"] = value["clusters"][0]["configuration_id"]
    with pytest.raises(ValueError, match="configuration IDs"):
        validate_inputs(value, load(PROTOCOL_PATH), bound_ledger(value), load(FREEZE_PATH))


def test_level_a_is_not_blocked_by_secondary_tradeoff_metrics(monkeypatch):
    value = payload()
    families = [
        "bounded_geometric_restriction",
        "persistent_command_motion_discrepancy",
        "measured_response_recovery",
    ]
    value["clusters"] = [row(i + 1, families[i % 3]) for i in range(24)]
    for item in value["clusters"]:
        item["material_error_p"] = 0
        item["essential_units_covered_p"] = 4
    monkeypatch.setattr("focused_sequential_monitor.lower_confidence_bound", lambda *args: 0.05)
    monkeypatch.setattr("focused_sequential_monitor.upper_confidence_bound", lambda *args: 0.3)
    result = analyze(value, load(PROTOCOL_PATH), bound_ledger(value), load(FREEZE_PATH))
    assert result["status"] == "LEVEL_A"
    assert result["primary"]["level_A_positive_benefit"] is True
    assert result["primary"]["level_B_exceeds_0_10"] is False


def test_unregistered_interim_look_cannot_claim_success(monkeypatch):
    value = payload()
    families = [
        "bounded_geometric_restriction",
        "persistent_command_motion_discrepancy",
        "measured_response_recovery",
    ]
    value["clusters"] = [row(i + 1, families[i % 3]) for i in range(25)]
    monkeypatch.setattr("focused_sequential_monitor.lower_confidence_bound", lambda *args: 0.5)
    result = analyze(value, load(PROTOCOL_PATH), bound_ledger(value), load(FREEZE_PATH))
    assert result["status"] == "CONTINUE"
    assert result["primary"]["level_A_positive_benefit"] is False
