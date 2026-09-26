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
COMPLETE_ENDPOINT_QUALIFICATION = ROOT / (
    "manifests/annotation/luna-model-judge-v12-complete-endpoint-extension-v1.json"
)
ELIGIBILITY_AMENDMENT = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-eligibility-amendment-1.json"
)
FIRST_RUN = ROOT / "manifests/data/fsdc-land-geometry-001-disposition.json"
SECOND_RUN = ROOT / "manifests/data/fsdc-land-geometry-002-disposition.json"
THIRD_RUN = ROOT / "manifests/data/fsdc-land-geometry-003-disposition.json"
FOURTH_RUN = ROOT / "manifests/data/fsdc-land-geometry-004-disposition.json"
FIFTH_RUN = ROOT / "manifests/data/cm-land-conf-041-disposition.json"
SIXTH_RUN = ROOT / "manifests/data/cm-land-conf-042-disposition.json"
SEVENTH_RUN = ROOT / "manifests/data/cm-land-conf-043-disposition.json"
EIGHTH_RUN = ROOT / "manifests/data/cm-land-conf-044-disposition.json"
NINTH_RUN = ROOT / "manifests/data/cm-land-conf-045-disposition.json"
TENTH_RUN = ROOT / "manifests/data/cm-land-conf-046-disposition.json"
ELEVENTH_RUN = ROOT / "manifests/data/cm-land-conf-047-disposition.json"
TWELFTH_RUN = ROOT / "manifests/data/cm-land-conf-048-disposition.json"
THIRTEENTH_RUN = ROOT / "manifests/data/cm-land-conf-049-disposition.json"
FOURTEENTH_RUN = ROOT / "manifests/data/cm-land-conf-050-disposition.json"
FIFTEENTH_RUN = ROOT / "manifests/data/cm-land-conf-051-disposition.json"
SIXTEENTH_ATTEMPT = ROOT / "manifests/data/cm-land-conf-052-disposition.json"
SEVENTEENTH_ATTEMPT = ROOT / "manifests/data/cm-land-conf-053-disposition.json"
EIGHTEENTH_ATTEMPT = ROOT / "manifests/data/cm-land-conf-054-disposition.json"
NINETEENTH_ATTEMPT = ROOT / "manifests/data/cm-land-conf-055-disposition.json"
TWENTIETH_ATTEMPT = ROOT / "manifests/data/cm-land-conf-056-disposition.json"
TWENTY_FIRST_ATTEMPT = ROOT / "manifests/data/cm-land-conf-057-disposition.json"
TWENTY_SECOND_ATTEMPT = ROOT / "manifests/data/cm-land-conf-058-disposition.json"


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


def test_focused_alpha_is_explicitly_and_permanently_bound_before_responses():
    protocol = load(PROTOCOL)
    ledger = load(LEDGER)
    allocation_id = protocol["inference"]["discovery_allocation"]

    allocations = ledger.get("allocations", ledger.get("error_budget", {}).get("allocations", []))
    allocation = next(item for item in allocations if item.get("allocation_id", item.get("id")) == allocation_id)
    assert allocation["alpha"] == protocol["inference"]["discovery_alpha"]
    assert allocation["status"] == "CONSUMED"
    assert allocation["campaign_id"] == "focused-supported-diagnostic-communication-v1-confirmation"
    assert ledger["consumed_alpha"] == 0.02
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


def test_complete_endpoint_extension_qualifies_without_study_scoring():
    result = load(COMPLETE_ENDPOINT_QUALIFICATION)

    assert result["status"] == "HELDOUT_QUALIFIED"
    assert result["study_evaluation_allowed"] is True
    assert all(item["complete_endpoint_correct"] == 18 for item in result["passes"].values())
    assert all(item["unit_coverage_correct"] == 72 for item in result["passes"].values())
    assert result["study_responses_scored"] == 0
    assert result["confirmatory_alpha_consumed"] == 0.0


def test_preactivation_exposure_is_excluded_with_fixed_family_matched_replacement():
    amendment = load(ELIGIBILITY_AMENDMENT)
    excluded = amendment["excluded_from_semantic_confirmation"]
    replacement = amendment["prospectively_fixed_replacement"]

    assert amendment["status"].startswith("FROZEN_BEFORE_REPLACEMENT_PHYSICAL_OUTCOME")
    assert excluded["run_id"] == "cm-land-conf-042"
    assert excluded["independent_confirmatory_semantic_increment"] == 0
    assert replacement["focused_family"] == excluded["family"]
    assert replacement["attempt_rule"].startswith("one attempt")
    assert amendment["uniformity"]["observed_method_comparison_used"] is False
    assert amendment["uniformity"]["alpha_consumed"] == 0.0


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


def test_third_focused_run_repeats_bounded_geometry_support_without_causal_overreach():
    run = load(THIRD_RUN)

    assert run["admission"]["attempt_count"] == 1
    assert run["independent_reference"]["direct_route_restriction_supported"] is True
    assert run["independent_reference"]["unique_physical_obstacle_supported"] is False
    assert run["independent_reference"]["controller_consumption_proven"] is False
    assert run["independent_reference"]["costmap_caused_plan_change_proven"] is False
    assert run["study_effect"]["primary_semantic_cluster_increment"] == 0


def test_added_geometry_block_closes_with_second_retained_insufficiency_case():
    run = load(FOURTH_RUN)

    assert run["admission"]["attempt_count"] == 1
    assert run["independent_reference"]["direct_route_restriction_supported"] is False
    assert run["robot_visible_diagnostic"]["registered_primary_mechanism_established"] is False
    assert run["study_effect"]["outcome_dependent_replacement_performed"] is False
    assert run["next_fixed_run"] == "cm-land-conf-041"


def test_first_reassigned_run_uses_only_masked_ambiguity_condition_for_methods():
    run = load(FIFTH_RUN)

    assert run["attempt_count"] == 1
    assert run["raw_physical_reference"]["disposition"] == "supported"
    assert run["method_visible_reference"]["mask_adapter"] == "remove-delivered-odometry-v1"
    assert run["method_visible_reference"]["odometry_samples"] == 0
    assert run["method_visible_reference"]["disposition"] == "insufficient"
    assert run["method_visible_reference"]["primary_endpoint_eligible"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["semantic_boundary"]["confirmatory_alpha_consumed"] == 0.0


def test_second_reassigned_run_is_bounded_primary_discrepancy():
    run = load(SIXTH_RUN)

    assert run["attempt_count"] == 1
    assert run["method_visible_reference"]["primary_endpoint_eligible"] is True
    assert run["method_visible_reference"]["disposition"] == "supported"
    assert run["method_visible_reference"]["response_ratio"] == 0.0
    assert run["method_visible_reference"]["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["semantic_boundary"]["confirmatory_alpha_consumed"] == 0.0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-043"


def test_transient_run_preserves_recovery_and_success_without_unique_cause():
    run = load(SEVENTH_RUN)

    reference = run["method_visible_reference"]
    assert run["attempt_count"] == 1
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert reference["recovered_response_ratio"] == 1.0
    assert reference["unique_physical_cause_supported"] is False
    assert run["observed"]["navigation_status"] == "succeeded"
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["semantic_boundary"]["confirmatory_alpha_consumed"] == 0.0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-044"


def test_second_transient_configuration_remains_one_independent_unit():
    run = load(EIGHTH_RUN)

    reference = run["method_visible_reference"]
    assert run["attempt_count"] == 1
    assert reference["independent_cluster_increment"] == 1
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["recovered_response_ratio"] == 1.0
    assert reference["unique_physical_cause_supported"] is False
    assert run["observed"]["navigation_status"] == "succeeded"
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["semantic_boundary"]["confirmatory_alpha_consumed"] == 0.0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-045"


def test_connected_detour_persistent_run_is_bounded_and_retained():
    run = load(NINTH_RUN)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["confirmatory_alpha_consumed"] == 0.0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-046"


def test_second_connected_detour_persistent_run_is_independent_and_bounded():
    run = load(TENTH_RUN)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert reference["independent_cluster_increment"] == 1
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["confirmatory_alpha_consumed"] == 0.0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-047"


def test_response_recovery_then_abort_remains_primary_and_causally_bounded():
    run = load(ELEVENTH_RUN)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["observed"]["navigation_status"] == "aborted"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert 0.95 < reference["recovered_response_ratio"] < 1.0
    assert reference["recovery_caused_outcome_supported"] is False
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["semantic_boundary"]["program_alpha_consumed"] == 0.02
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-048"


def test_second_masked_ambiguity_run_withholds_unobserved_motion_mechanism():
    run = load(TWELFTH_RUN)
    raw = run["raw_physical_reference"]
    masked = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert raw["disposition"] == "supported"
    assert raw["response_ratio"] == 0.0
    assert masked["mask_adapter"] == "remove-delivered-odometry-v1"
    assert masked["primary_endpoint_eligible"] is False
    assert masked["disposition"] == "insufficient"
    assert masked["odometry_samples"] == 0
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["semantic_boundary"]["program_alpha_consumed"] == 0.02
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-049"


def test_third_response_recovery_run_preserves_success_and_causal_limit():
    run = load(THIRTEENTH_RUN)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["observed"]["navigation_status"] == "succeeded"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["response_ratio"] == 0.0
    assert 0.95 < reference["recovered_response_ratio"] < 1.0
    assert reference["recovery_caused_outcome_supported"] is False
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-050"


def test_third_masked_ambiguity_run_is_retained_after_unexpected_abort():
    run = load(FOURTEENTH_RUN)
    raw = run["raw_physical_reference"]
    masked = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["admission"]["unexpected_navigation_outcome_retained"] is True
    assert raw["disposition"] == "supported"
    assert raw["response_ratio"] == 0.0
    assert masked["primary_endpoint_eligible"] is False
    assert masked["disposition"] == "insufficient"
    assert masked["command_samples"] == 399
    assert masked["odometry_samples"] == 0
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-051"


def test_fourth_response_recovery_run_preserves_success_and_causal_limit():
    run = load(FIFTEENTH_RUN)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["observed"]["navigation_status"] == "succeeded"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["response_ratio"] == 0.0
    assert 0.95 < reference["recovered_response_ratio"] < 1.0
    assert reference["recovery_caused_outcome_supported"] is False
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["next_fixed_run_id"].startswith("cm-land-conf-052")


def test_geometry_run_with_endpoint_error_is_retained_invalid_without_semantic_use():
    run = load(SIXTEENTH_ATTEMPT)
    admission = run["admission"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["status"] == "RETAINED_INVALID_RECORDING_TRANSPORT_GATE_NO_SEMANTIC_RESPONSE"
    assert admission["unity_worker_result_valid"] is True
    assert admission["shared_fixture_valid"] is False
    assert admission["failed_gate"] == "ros_tcp_endpoint_errors_zero"
    assert admission["failed_gate_measurements"]["endpoint_errors"] == 1
    assert run["retention"]["diagnostic_exports_created"] is False
    assert run["retention"]["independent_references_run"] is False
    assert run["retention"]["P_responses"] == 0
    assert run["retention"]["R_responses"] == 0
    assert run["retention"]["Luna_calls"] == 0
    assert run["retention"]["confirmatory_cluster_increment"] == 0
    assert run["focused_progress"]["valid_physical_configurations"] == 15
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-053"


def test_fifth_response_recovery_run_preserves_success_and_causal_limit():
    run = load(SEVENTEENTH_ATTEMPT)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["admission"]["recording_valid_under_frozen_worker_result_gate"] is True
    assert run["admission"]["focused_registry_exact_reference_dry_run_passed"] is True
    assert run["observed"]["navigation_status"] == "succeeded"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert reference["recovered_response_ratio"] == 1.0
    assert reference["recovery_caused_outcome_supported"] is False
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["physical_configurations_collected"] == 16
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-054"


def test_nominal_control_rejects_false_premise_without_entering_primary_n():
    run = load(EIGHTEENTH_ATTEMPT)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["admission"]["recording_valid_under_frozen_worker_result_gate"] is True
    assert run["admission"]["coordinator_v3_nominal_unit_binding_passed"] is True
    assert run["observed"]["navigation_status"] == "succeeded"
    assert run["observed"]["follow_path_failures"] == 0
    assert reference["primary_endpoint_eligible"] is False
    assert reference["disposition"] == "not_triggered"
    assert reference["command_motion_discrepancy_supported"] is False
    assert reference["obstacle_cause_supported"] is False
    assert reference["exact_nav2_consumption_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["primary_diagnosable_references"] == 11
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-055"


def test_sixth_response_recovery_run_preserves_success_and_causal_limit():
    run = load(NINETEENTH_ATTEMPT)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["admission"]["recording_valid_under_frozen_worker_result_gate"] is True
    assert run["admission"]["focused_registry_exact_reference_dry_run_passed"] is True
    assert run["observed"]["navigation_status"] == "succeeded"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert reference["recovered_response_ratio"] == 1.0
    assert reference["recovery_caused_outcome_supported"] is False
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["primary_diagnosable_references"] == 12
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-056"


def test_connected_detour_persistent_discrepancy_retains_unexpected_abort():
    run = load(TWENTIETH_ATTEMPT)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["admission"]["unexpected_navigation_outcome_retained"] is True
    assert run["admission"]["recording_valid_under_frozen_worker_result_gate"] is True
    assert run["observed"]["navigation_status"] == "aborted"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["response_ratio"] == 0.0
    assert reference["response_recovery_interval_s"] is None
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["primary_diagnosable_references"] == 13
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-057"


def test_later_window_response_recovery_preserves_measurements_and_causal_limit():
    run = load(TWENTY_FIRST_ATTEMPT)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["observed"]["navigation_status"] == "succeeded"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["discrepancy_interval_s"] == [18.0, 27.0]
    assert reference["response_recovery_interval_s"] == [30.0, 31.0]
    assert reference["recovered_response_ratio"] == 1.0
    assert reference["recovery_caused_outcome_supported"] is False
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["primary_diagnosable_references"] == 14
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-058"


def test_later_window_persistent_discrepancy_retains_unexpected_abort():
    run = load(TWENTY_SECOND_ATTEMPT)
    reference = run["method_visible_reference"]

    assert run["attempt_count"] == 1
    assert run["retry_or_replacement_performed"] is False
    assert run["admission"]["unexpected_navigation_outcome_retained"] is True
    assert run["observed"]["navigation_status"] == "aborted"
    assert reference["primary_endpoint_eligible"] is True
    assert reference["disposition"] == "supported"
    assert reference["discrepancy_interval_s"] == [18.0, 28.0]
    assert reference["response_recovery_interval_s"] is None
    assert reference["unique_physical_cause_supported"] is False
    assert run["semantic_boundary"]["P_responses"] == 0
    assert run["semantic_boundary"]["R_responses"] == 0
    assert run["focused_progress"]["primary_diagnosable_references"] == 15
    assert run["focused_progress"]["next_fixed_run_id"] == "cm-land-conf-059"
