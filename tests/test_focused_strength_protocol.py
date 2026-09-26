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
SCHEDULE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-schedule.json"
)
OLD_SCHEDULE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "land-command-motion-physical-schedule-v1.json"
)
QUESTIONS = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-questions.json"
)
BUILD_AMENDMENT = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-build-amendment-1.json"
)
BUILD_MANIFEST = ROOT / "manifests/data/fsdc-v1-player-build-1.evaluator-only.json"
FIRST_RUN = ROOT / "manifests/data/fsdc-land-geometry-001-disposition.json"
SECOND_RUN = ROOT / "manifests/data/fsdc-land-geometry-002-disposition.json"


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
    counts = protocol["families"]["fixed_discovery_counts"]

    assert sum(counts.values()) == 64
    assert sum(counts[name] for name in protocol["families"]["primary"]) == 47
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


def test_focused_schedule_reassigns_every_unattempted_configuration_without_selection():
    schedule = load(SCHEDULE)
    old = load(OLD_SCHEDULE)
    confirmation = next(
        item for item in old["cohorts"] if item["cohort"] == "confirmation-physical"
    )
    remaining = [item for item in confirmation["runs"] if 41 <= item["order"] <= 100]

    assert len(remaining) == schedule["prior_physical_schedule"]["reassigned_count"] == 60
    assert [item["order"] for item in remaining] == list(range(41, 101))
    assert len(schedule["added_geometry_configurations"]) == 4
    assert schedule["fixed_counts"]["total_independent_configurations"] == 64
    assert schedule["fixed_counts"]["primary_eligible_if_independently_supported"] == 47


def test_question_registry_matches_focused_families_and_marks_essentials():
    protocol = load(PROTOCOL)
    registry = load(QUESTIONS)
    rows = {item["family"]: item for item in registry["questions"]}
    expected = set(protocol["families"]["primary"] + protocol["families"]["controls"])

    assert set(rows) == expected
    assert all(item["essential_units"] for item in rows.values())
    assert all(rows[name]["primary_endpoint_eligible"] for name in protocol["families"]["primary"])
    assert not any(
        rows[name]["primary_endpoint_eligible"] for name in protocol["families"]["controls"]
    )


def test_focused_player_build_is_hash_bound_without_retaining_large_player():
    amendment = load(BUILD_AMENDMENT)
    manifest = load(BUILD_MANIFEST)
    build = amendment["build"]

    assert amendment["protocol_id"] == "focused-supported-diagnostic-communication-v1"
    assert amendment["status"] == "FROZEN_BEFORE_FIRST_FOCUSED_PHYSICAL_LAUNCH"
    assert build["source_commit_proven"] is True
    assert build["audit_accepted"] is True
    assert build["audit_failed_checks"] == []
    assert build["large_player_retained_in_dvc"] is False
    assert manifest["file_count"] == 2
    hashes = {item["sha256"] for item in manifest["files"]}
    assert build["provenance_sha256"] in hashes
    assert build["audit_sha256"] in hashes


def test_first_focused_physical_run_is_retained_without_semantic_or_alpha_increment():
    run = load(FIRST_RUN)

    assert run["admission"]["attempt_count"] == 1
    assert run["admission"]["retry_performed"] is False
    assert run["admission"]["scenario_binding_checks_passed"] == 14
    assert run["independent_reference"]["direct_route_restriction_supported"] is True
    assert run["independent_reference"]["costmap_caused_plan_change_proven"] is False
    assert run["study_effect"]["prospective_physical_configuration_increment"] == 1
    assert run["study_effect"]["primary_semantic_cluster_increment"] == 0
    assert run["study_effect"]["model_response_increment"] == 0
    assert run["study_effect"]["luna_judgment_increment"] == 0
    assert run["study_effect"]["confirmatory_alpha_consumed"] == 0.0


def test_unfavorable_geometry_induction_is_retained_without_replacement_or_primary_count():
    run = load(SECOND_RUN)

    assert run["admission"]["attempt_count"] == 1
    assert run["admission"]["replacement_layout_used"] is False
    assert run["independent_reference"]["direct_route_restriction_supported"] is False
    assert run["independent_reference"]["direct_route_fully_covered"] is False
    assert run["robot_visible_diagnostic"]["registered_primary_mechanism_established"] is False
    assert run["study_effect"]["primary_semantic_cluster_increment"] == 0
    assert run["study_effect"]["outcome_dependent_replacement_performed"] is False
