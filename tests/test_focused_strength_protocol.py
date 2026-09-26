import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1.json"
)
AUDIT = ROOT / (
    "research/explanation_fidelity/experiment_configs/development/"
    "measurement-complete-v2-focused-audit-v1.json"
)
LEDGER = ROOT / "manifests/study/diagnostic-sequential-error-ledger-v2.json"
JUDGE = ROOT / "manifests/annotation/luna-model-judge-v1-heldout-v12-final.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def test_focused_protocol_is_prospective_and_has_zero_results():
    protocol = load(PROTOCOL)
    state = protocol["current_state"]

    assert protocol["status"] == "REGISTERED_PREACTIVATION_NO_CAMPAIGN_ACTIVE"
    assert protocol["applies_to_legacy"] is False
    assert state == {
        "confirmatory_semantic_clusters": 0,
        "effect_estimate_exists": False,
        "confidence_sequence_exists": False,
        "statistical_significance_exists": False,
        "replication_result_exists": False,
        "alpha_consumed": 0.0,
    }


def test_focused_mixture_counts_independent_clusters_only():
    protocol = load(PROTOCOL)
    block = protocol["families"]["block_of_8"]

    assert sum(block.values()) == 8
    assert sum(block[name] for name in protocol["families"]["primary"]) == 6
    assert "evidence_mask" in protocol["zero_increment_relations"]
    assert "luna_pass" in protocol["zero_increment_relations"]


def test_focused_alpha_is_available_and_not_silently_bound():
    protocol = load(PROTOCOL)
    ledger = load(LEDGER)
    allocation_id = protocol["inference"]["discovery_allocation"]

    allocations = ledger.get("allocations", ledger.get("error_budget", {}).get("allocations", []))
    allocation = next(item for item in allocations if item.get("allocation_id", item.get("id")) == allocation_id)
    assert allocation["alpha"] == protocol["inference"]["discovery_alpha"]
    assert allocation["status"] == "AVAILABLE"
    assert protocol["inference"]["allocation_status"] == "AVAILABLE_NOT_BOUND"


def test_selected_candidate_audit_and_judge_are_explicitly_bounded():
    protocol = load(PROTOCOL)
    audit = load(AUDIT)
    judge = load(JUDGE)

    assert audit["selection"]["selected_candidate"] == protocol["candidate"]["id"]
    assert audit["selection"]["repair_performed"] is False
    assert audit["fairness_audit"]["judge_evidence_parity"] == "FAIL"
    assert protocol["judge"]["evidence_complete_packet_required"] is True
    assert judge["status"] == "HELDOUT_QUALIFIED"


def test_level_a_does_not_require_level_b_or_secondary_tradeoff_success():
    protocol = load(PROTOCOL)
    inference = protocol["inference"]

    assert inference["level_A_threshold"] == 0.0
    assert inference["level_B_minimum_worthwhile_improvement"] == 0.1
    assert inference["level_C_is_secondary_tradeoff_conclusion"] is True
    assert "supplemental_information_coverage" in protocol["secondary_not_level_A_gates"]
