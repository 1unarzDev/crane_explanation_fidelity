#!/usr/bin/env python3
"""Evaluate public command-motion requirements from one exact visible condition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_calibration import evidence_ids_by_role
from evidence_calibration_io import canonical_json_bytes, ontology_from_dict
from maximal_supported_diagnosis import FACT_SCHEMA


EVALUATOR_ID = "command-motion-requirement-evaluator"
EVALUATOR_VERSION = "v1-development"


def evaluate(ontology_dict: dict[str, Any], condition_entry: dict[str, Any],
             question_contract: dict[str, Any]) -> dict[str, Any]:
    ontology = ontology_from_dict(ontology_dict)
    condition, packet = condition_entry["condition"], condition_entry["method_packet"]
    role_ids = evidence_ids_by_role(packet)
    evidence = packet["evidence"]

    def refs(*roles: str) -> list[str]:
        return sorted({item for role in roles for item in role_ids.get(role, set())})

    def row(identifier: str, status: str, support: list[str], detail: str) -> dict[str, Any]:
        return {"requirement_id": identifier, "status": status,
                "support_references": support, "detail": detail}

    result: dict[str, dict[str, Any]] = {}
    action = evidence.get("navigate_to_pose_result")
    if action:
        action_refs = refs("navigate_to_pose_result")
        valid = bool(action.get("accepted_goal_record_id") and action.get("action_result_record_id"))
        result["req-action-result-valid"] = row("req-action-result-valid", "SATISFIED" if valid else "INVALID", action_refs if valid else [], "goal-bounded retained action result")
        for identifier, expected in (("req-action-succeeded", "succeeded"), ("req-action-aborted", "aborted")):
            result[identifier] = row(identifier, "SATISFIED" if action["action_status"] == expected else "CONTRADICTED", action_refs, f"action status is {action['action_status']}")

    recovery = evidence.get("behavior_tree_transitions")
    anchors = evidence.get("source_anchors")
    if recovery and anchors:
        recovery_refs = refs("behavior_tree_transitions", "source_anchors")
        sequence = recovery["execution_sequence"]
        valid = bool(sequence.get("recovery_node_classifier"))
        invoked = sequence.get("source_qualified_wait_recovery_count", 0) > 0
        result["req-recovery-trace-valid"] = row("req-recovery-trace-valid", "SATISFIED" if valid else "INVALID", recovery_refs if valid else [], "source-qualified goal-bounded recovery trace")
        result["req-recovery-invoked"] = row("req-recovery-invoked", "SATISFIED" if invoked else "CONTRADICTED", recovery_refs, f"qualified recovery count={sequence.get('source_qualified_wait_recovery_count', 0)}")

    command = evidence.get("delivered_command_stream")
    odometry = evidence.get("delivered_odometry_stream")
    computation = evidence.get("command_motion_computation")
    if command:
        valid = bool(command.get("samples") and command.get("provenance"))
        result["req-command-stream-valid"] = row("req-command-stream-valid", "SATISFIED" if valid else "INVALID", refs("delivered_command_stream") if valid else [], "retained delivered command stream")
    if odometry:
        valid = bool(odometry.get("samples") and odometry.get("provenance"))
        result["req-odometry-stream-valid"] = row("req-odometry-stream-valid", "SATISFIED" if valid else "INVALID", refs("delivered_odometry_stream") if valid else [], "retained delivered odometry stream")
    if command and odometry:
        synchronized = computation is not None
        result["req-command-odometry-synchronized"] = row(
            "req-command-odometry-synchronized", "SATISFIED" if synchronized else "INVALID",
            refs("delivered_command_stream", "delivered_odometry_stream") if synchronized else [],
            "registered computation covers aligned command and odometry intervals" if synchronized else "aligned computation absent",
        )

    if computation:
        comp_refs = refs("command_motion_computation")
        measurements = {item["id"]: item for item in computation["measurements"]}
        discrepancy_ids = {
            "req-command-above-threshold": "discrepancy_commanded_planar_speed",
            "req-interval-duration-sufficient": "sustained_discrepancy_duration",
            "req-measured-response-low": "discrepancy_measured_planar_speed",
        }
        for identifier, measurement_id in discrepancy_ids.items():
            present = measurement_id in measurements
            result[identifier] = row(identifier, "SATISFIED" if present else "CONTRADICTED", comp_refs,
                                     f"registered measurement {measurement_id} {'present' if present else 'absent'}")
        recovered = "recovered_measured_planar_speed" in measurements
        result["req-measured-response-recovered"] = row(
            "req-measured-response-recovered", "SATISFIED" if recovered else "CONTRADICTED",
            comp_refs, "later recovered-response measurement present" if recovered else "no registered recovered-response measurement",
        )
        no_failure = computation["diagnostic_disposition"] == "not_triggered"
        result["req-no-failure-triggered"] = row(
            "req-no-failure-triggered", "SATISFIED" if no_failure else "CONTRADICTED",
            comp_refs, f"command-motion diagnostic disposition={computation['diagnostic_disposition']}",
        )

    evaluations = []
    for requirement in ontology.evidence_requirements:
        evaluations.append(result.get(requirement.requirement_id, row(
            requirement.requirement_id, "ABSENT", [], "required visible role or computation absent"
        )))
    return {
        "schema": FACT_SCHEMA, "condition_id": condition["condition_id"],
        "method_packet_sha256": condition["method_packet_sha256"],
        "question_contract": question_contract, "requirement_evaluations": evaluations,
        "ambiguity_node_ids": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", type=Path, required=True)
    parser.add_argument("--condition-entry", type=Path, required=True)
    parser.add_argument("--question-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = evaluate(json.loads(args.ontology.read_text()), json.loads(args.condition_entry.read_text()),
                      json.loads(args.question_contract.read_text()))
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
