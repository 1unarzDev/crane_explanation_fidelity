"""Development local repair for nonterminal outcomes and partial measured recovery."""
from evidence_calibration_io import canonical_sha256
from evaluate_command_motion_requirements import evaluate
from maximal_supported_diagnosis import diagnose
from realize_evidence_calibrated_explanation_v5 import realize as previous

VERSION = "v6-development-nonterminal-and-partial-recovery-2"


def realize(ontology, entry, question_contract):
    evidence = entry["method_packet"]["evidence"]
    action = evidence.get("navigate_to_pose_result", {})
    active = (action.get("action_status") == "remained active at the observation cutoff"
              and action.get("terminal_result_observed") is False
              and action.get("observation_cutoff", {}).get("basis") ==
              "accepted_goal_wall_time_plus_runtime_manifest_action_duration")
    try:
        output = previous(ontology, entry, question_contract)
    except ValueError as exc:
        # The original contract realizer requires a supported terminal-outcome claim.
        # Permit a factual active-state answer only when it has no deeper approved claim.
        if str(exc) != "a claim-aware response cannot be empty" or not active: raise
        result = diagnose(ontology, entry, evaluate(ontology, entry, question_contract))
        if result["approved_claim_ids"]: raise
        output = dict(method="B4", development_only=True, condition_id=result["condition_id"],
                      method_packet_sha256=entry["condition"]["method_packet_sha256"],
                      diagnosis=result, clauses=[], model_calls=0,
                      endpoint_status="UNSCORED_REQUIRES_METHOD_INDEPENDENT_SCORING")
        for identifier, text in [
            ("missing-motion-limitation", "The available evidence lacks measured motion needed to establish a command-motion discrepancy or measured response recovery."),
            ("missing-trace-limitation", "The available evidence does not establish whether recovery ran."),
            ("hidden-cause-limitation", "The available evidence does not identify a hidden physical cause.")]:
            output["clauses"].append(dict(clause_id=identifier,contract_id=identifier,
                kind="PACKET_DERIVED",text=text,support_references=[]))
    if active:
        output["clauses"].insert(0,dict(clause_id="observed-active-outcome",contract_id="observed-active-outcome",
            kind="PACKET_DERIVED",support_references=["action-result"],
            text="The navigation action remained active at the declared observation cutoff; its eventual outcome was not observed."))
    measurements = {r["id"]:r for r in evidence.get("command_motion_computation", {}).get("measurements", [])}
    recovered = measurements.get("recovered_measured_planar_speed")
    healthy = measurements.get("calibrated_healthy_planar_speed")
    if recovered and healthy and recovered["value"] < .95 * healthy["value"]:
        output["clauses"].append(dict(clause_id="partial-recovery-limitation",contract_id="partial-recovery-limitation",
            kind="PACKET_DERIVED",support_references=["command-motion-computation"],
            text="The later response exceeds the registered recovery threshold but remains below the healthy comparator; this does not establish full restoration of command tracking."))
    output.update(version=VERSION,schema="crane-evidence-calibration-b4-development-output/v6",
                  ontology_sha256=canonical_sha256(ontology),
                  development_change="Local handling of observed nonterminal action state and partial measured recovery",
                  answer=" ".join(c["text"] for c in output["clauses"]))
    return output
