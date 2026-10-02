from copy import deepcopy
from test_claim_aware_realization_v3 import inputs
from realize_evidence_calibrated_explanation_v6 import realize
from evidence_calibration_io import canonical_sha256


def test_nonterminal_shallow_answer_preserves_outcome_uncertainty_and_missing_motion():
    ontology, entry, contract = inputs("cm-land-conf-047-E0")
    action = entry["method_packet"]["evidence"]["navigate_to_pose_result"]
    action.update(action_status="remained active at the observation cutoff",
                  action_error_code=None, terminal_result_observed=False,
                  observation_cutoff=dict(basis="accepted_goal_wall_time_plus_runtime_manifest_action_duration"))
    entry["condition"]["method_packet_sha256"] = canonical_sha256(entry["method_packet"])
    before = deepcopy(entry)
    output = realize(ontology, entry, contract)
    assert entry == before
    assert "eventual outcome was not observed" in output["answer"]
    assert "lacks measured motion" in output["answer"]
    assert not output["diagnosis"]["approved_claim_ids"]
    assert "action aborted" not in output["answer"]


def test_partial_recovery_does_not_imply_full_command_tracking():
    ontology, entry, contract = inputs("cm-land-conf-047-E3")
    values = {m["id"]:m for m in entry["method_packet"]["evidence"]["command_motion_computation"]["measurements"]}
    values["recovered_measured_planar_speed"]["value"] = .6 * values["calibrated_healthy_planar_speed"]["value"]
    entry["condition"]["method_packet_sha256"] = canonical_sha256(entry["method_packet"])
    output = realize(ontology, entry, contract)
    assert "does not establish full restoration of command tracking" in output["answer"]
    assert "Measured response recovered" in output["answer"]
    assert "does not establish the eventual task outcome or whether it caused" in output["answer"]


def test_v7_nonterminal_fallback_retains_zero_observed_waits():
    from realize_evidence_calibrated_explanation_v7 import realize as latest
    ontology, entry, contract = inputs("cm-land-conf-047-E1")
    evidence = entry["method_packet"]["evidence"]
    evidence["navigate_to_pose_result"].update(
        action_status="remained active at the observation cutoff", action_error_code=None,
        terminal_result_observed=False,
        observation_cutoff=dict(basis="accepted_goal_wall_time_plus_runtime_manifest_action_duration"))
    trace = evidence["behavior_tree_transitions"]["execution_sequence"]
    trace.update(follow_path_attempt_count=1,follow_path_failure_count=0,source_qualified_wait_recovery_count=0)
    entry["condition"]["method_packet_sha256"] = canonical_sha256(entry["method_packet"])
    output = latest(ontology,entry,contract)
    assert "0 source-qualified Wait recovery invocations" in output["answer"]
    assert "does not establish whether recovery ran" not in output["answer"]
    assert "do not prove the unobserved history" in output["answer"]
