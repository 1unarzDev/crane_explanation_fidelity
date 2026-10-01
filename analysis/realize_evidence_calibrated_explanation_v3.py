"""Development B4: retain supported software facts alongside calibrated motion claims.

This extends the existing contract engine with local, packet-derived clauses. It reads
no evaluator reference, physical intervention label, or previous method answer.
The inherited false-premise clause is scoped to the registered motion diagnostic.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from evidence_calibration_io import canonical_sha256
from evaluate_command_motion_requirements import evaluate
from maximal_supported_diagnosis import diagnose
from realize_evidence_calibrated_explanation_v2 import realize as realize_base

VERSION = "v3-development-supported-software-facts"


def realize(ontology: dict, entry: dict, question_contract: dict) -> dict:
    facts = evaluate(ontology, entry, question_contract)
    result = diagnose(ontology, entry, facts)
    nodes = {row["node_id"]: row for row in ontology["diagnostic_nodes"]}
    required = sorted({claim for node in result["maximal_node_ids"]
                       for claim in nodes[node]["claim_ids"]})
    evidence = entry["method_packet"]["evidence"]
    computation = evidence.get("command_motion_computation", {})
    measurements = {row["id"]: row for row in computation.get("measurements", [])}
    numeric = []
    if "claim-command-motion-discrepancy" in required:
        command = measurements["discrepancy_commanded_planar_speed"]
        measured = measurements["discrepancy_measured_planar_speed"]
        for slot, value, unit in [("commanded_speed", command["value"], command["unit"]),
                                  ("measured_speed", measured["value"], measured["unit"]),
                                  ("interval_start", command["interval_s"][0], "s"),
                                  ("interval_end", command["interval_s"][1], "s")]:
            numeric.append(dict(claim_id="claim-command-motion-discrepancy", slot_id=slot,
                                value=value, unit=unit, support_reference="command-motion-computation"))
    plan = dict(schema="crane-claim-realization-plan/v1", plan_id=result["condition_id"] + "-B4-" + VERSION,
                diagnostic_result_sha256=canonical_sha256(result), required_claim_ids=required,
                optional_claim_ids=[], required_non_entailment_ids=result["required_non_entailment_ids"],
                approved_numeric_values=numeric)
    candidate = dict(schema="crane-claim-realization-candidate/v1", response_id=plan["plan_id"],
                     plan_sha256=canonical_sha256(plan), clauses=[])
    base = realize_base(ontology, result, plan, candidate)
    clauses = []
    for clause in base["final_clauses"]:
        if clause["contract_id"] == "claim-false-premise-success":
            clause = {**clause, "text": "The recorded action succeeded and the registered command-motion diagnostic did not trigger; this does not rule out intermediate software action failures."}
        clauses.append(clause)

    def add(identifier: str, text: str, support: list[str]) -> None:
        clauses.append(dict(clause_id=identifier, kind="PACKET_DERIVED", contract_id=identifier,
                            text=text, support_references=support))

    action = evidence.get("navigate_to_pose_result", {})
    code = action.get("action_error_code")
    if action.get("action_status") == "aborted" and code == 105:
        # Nav2's public error-code convention, the same repository-aware knowledge
        # available to B2. This reports the error and never infers physical motion.
        add("reported-progress-failure", "The action reports a controller failure to make progress (error code 105); this is a reported software failure, not a measured physical cause.", ["action-result"])
    elif action.get("action_status") == "aborted" and isinstance(code, int):
        add("reported-action-error", f"The action reports error code {code}.", ["action-result"])

    trace = evidence.get("behavior_tree_transitions", {}).get("execution_sequence")
    anchors = evidence.get("source_anchors", {})
    if trace and anchors:
        classifier = trace.get("recovery_node_classifier", {})
        counts = [trace.get(k) for k in ("follow_path_attempt_count", "follow_path_failure_count", "source_qualified_wait_recovery_count")]
        if (all(type(x) is int and x >= 0 for x in counts)
                and counts[1] <= counts[0]
                and classifier.get("policy_sha256") == anchors.get("bt_policy_sha256")
                and classifier.get("node_name") == "Wait"):
            add("software-execution-trace", f"The retained trace records {counts[0]} FollowPath attempts, {counts[1]} FollowPath failures, and {counts[2]} source-qualified Wait recovery invocations. These records do not identify a physical cause or prove that waiting caused a later outcome.", ["recovery-trace", "source-anchors"])

    if "claim-measured-response-recovered" in result["approved_claim_ids"]:
        recovery = measurements.get("recovered_measured_planar_speed")
        if (recovery and recovery.get("unit") == "m/s"
                and type(recovery.get("value")) in (int, float)
                and math.isfinite(recovery["value"])
                and isinstance(recovery.get("interval_s"), list)
                and len(recovery["interval_s"]) == 2
                and all(type(x) in (int, float) and math.isfinite(x) for x in recovery["interval_s"])
                and recovery["interval_s"][0] < recovery["interval_s"][1]):
            start, end = recovery["interval_s"]
            add("measured-recovery-interval", f"Measured response recovered to {recovery['value']:.12g} {recovery['unit']} in the later {start:.12g}–{end:.12g} s interval.", ["command-motion-computation"])

    if "delivered_command_stream" in evidence:
        add("command-acceptance-limitation", "Delivered commands do not establish actuator acceptance.", ["delivered-command-stream"])
    if "delivered_odometry_stream" in evidence:
        add("odometry-consumption-limitation", "Delivered odometry does not establish Nav2 consumption.", ["delivered-odometry-stream"])
    else:
        add("missing-motion-limitation", "The available evidence lacks measured motion needed to establish a command-motion discrepancy or measured response recovery.", [])
    if not trace:
        add("missing-trace-limitation", "The available evidence does not establish whether recovery ran.", [])
    add("hidden-cause-limitation", "The available evidence does not identify a hidden physical cause.", [])

    return dict(schema="crane-evidence-calibration-b4-development-output/v3", method="B4",
                development_only=True, version=VERSION, condition_id=result["condition_id"],
                method_packet_sha256=entry["condition"]["method_packet_sha256"],
                diagnosis=result, plan=plan, base_realization=base, clauses=clauses,
                answer=" ".join(row["text"] for row in clauses), model_calls=0,
                endpoint_status="UNSCORED_REQUIRES_METHOD_INDEPENDENT_SCORING")


if __name__ == "__main__":
    from run_evidence_calibration_b2_pilot import ROOT, _materialize
    pilot = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
    schedule = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    validation = json.loads((ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json").read_text())
    ontology = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
    out = ROOT / "model_outputs/evidence-calibration-b2-b4-development-v3/b4"
    out.mkdir(parents=True, exist_ok=True)
    for episode in validation["episodes"]:
        for condition_id in episode["condition_ids"]:
            entry, _, family = _materialize(ROOT, pilot, schedule, condition_id)
            contract = dict(question_id=family + "-question-v1-development", failure_premise=True,
                            required_mechanism_families=["false_premise"] if family == "nominal_false_premise" else ["command_motion"])
            answer = realize(ontology, entry, contract)
            answer["family"] = family
            path = out / (condition_id + ".json")
            raw = json.dumps(answer, indent=2, sort_keys=True, allow_nan=False) + "\n"
            if path.exists() and path.read_text() != raw:
                raise ValueError("refusing to replace retained development output")
            if not path.exists():
                path.write_text(raw)
    print(json.dumps(dict(development_outputs=60, model_calls=0, output_root=str(out))))
