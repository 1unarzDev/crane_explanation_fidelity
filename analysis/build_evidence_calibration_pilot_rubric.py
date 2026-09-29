#!/usr/bin/env python3
"""Build a method-blind development rubric from independent physical references.

The rubric is evaluator-only until copied into a blinded annotation packet. It never reads B2 or
B4 answer text and never exposes intervention identity to the annotator.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
from pathlib import Path

from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from run_evidence_calibration_b2_pilot import _materialize


ROOT = Path(__file__).resolve().parents[1]
LEVELS = [
    "task_outcome", "software_action_failure", "recovery_mechanism",
    "command_motion_discrepancy", "physical_execution_mechanism", "specific_physical_cause",
]


def build(condition_id: str, blinding_salt: str, root: Path = ROOT) -> tuple[dict, dict]:
    if len(blinding_salt) < 16:
        raise ValueError("blinding salt must contain at least 16 characters")
    pilot = json.loads((root / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json").read_text())
    schedule = json.loads((root / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    validation = json.loads((root / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json").read_text())
    entry, _, family = _materialize(root, pilot, schedule, condition_id)
    row = next(item for item in validation["episodes"] if condition_id in item["condition_ids"])
    index = row["condition_ids"].index(condition_id)
    if entry["condition"]["method_packet_sha256"] != row["condition_packet_sha256s"][index]:
        raise ValueError("condition packet differs from the pinned pilot")
    run_id = row["run_id"]
    reference_path = root / f"data/evaluator_only/dev/{run_id}/command-motion-independent-reference-v1.json"
    reference_bytes = reference_path.read_bytes()
    reference = json.loads(reference_bytes)
    if (reference.get("status") != "DEVELOPMENT_REFERENCE_NOT_CONFIRMATORY"
            or reference.get("implementation_independence", {}).get("imports_proposed_diagnostic_core") is not False
            or reference.get("implementation_independence", {}).get("imports_proposed_exporter") is not False):
        raise ValueError("independent evaluator reference is unavailable")
    result = reference["result"]
    disposition = result["disposition"]
    if disposition not in {"supported", "not_triggered"}:
        raise ValueError("pilot reference disposition is outside the declared families")
    if (family == "nominal_false_premise") != (disposition == "not_triggered"):
        raise ValueError("independent reference disagrees with declared nominal family")
    evidence = entry["method_packet"]["evidence"]
    outcome = evidence["navigate_to_pose_result"]["action_status"]
    if outcome != reference["execution_basis"]["action_status"]:
        raise ValueError("independent reference and masked outcome disagree")
    units = ["state the recorded navigation action outcome"]
    limits = ["do not identify a unique hidden physical cause from this evidence"]
    if "behavior_tree_transitions" in evidence:
        units.append("state the retained source-qualified recovery sequence")
        limits.append("recovery ordering alone does not prove it caused the task outcome")
    if "delivered_command_stream" in evidence:
        units.append("state the delivered command observation")
        if "delivered_odometry_stream" not in evidence:
            limits.append("delivered command alone does not establish measured motion")
    if "command_motion_computation" in evidence:
        if disposition == "supported":
            units.append("state the supported command-to-measured-motion discrepancy and interval")
            if result["response_recovery_interval_s"] is not None:
                units.append("state the later measured-response recovery when supported")
                limits.append("measured recovery before the outcome does not prove outcome causation")
        else:
            units.append("state that the registered command-motion discrepancy did not trigger")
    if family == "missing_decisive_evidence" and "delivered_command_stream" in evidence:
        limits.append("missing odometry prevents an odometry-dependent motion diagnosis")

    independent_facts = [
        {"independent_action_status": outcome},
        {"independent_command_motion_disposition": disposition},
    ]
    if disposition == "supported":
        independent_facts.append({
            "independently_measured_discrepancy_interval_s": result["interval_s"],
            "independently_measured_command_mps": result["discrepancy_commanded_planar_speed_mps"],
            "independently_measured_motion_mps": result["discrepancy_measured_planar_speed_mps"],
            "independently_measured_recovery_interval_s": result["response_recovery_interval_s"],
        })
    opaque = hmac.new(blinding_salt.encode(), condition_id.encode(), hashlib.sha256).hexdigest()[:24]
    rubric = {
        "rubric_id": f"ec-pilot-rubric-{opaque}",
        "question_text": entry["method_packet"]["question"],
        "required_unit_prompts": units,
        "abstraction_level_options": LEVELS,
        "limitation_prompts": limits,
        "false_premise_applicable": family == "nominal_false_premise" and "command_motion_computation" in evidence,
        "sanitized_physical_facts": independent_facts,
    }
    provenance = {
        "schema": "crane-evidence-calibration-pilot-rubric-provenance/v1",
        "condition_id": condition_id,
        "family": family,
        "condition_packet_sha256": entry["condition"]["method_packet_sha256"],
        "independent_reference_sha256": hashlib.sha256(reference_bytes).hexdigest(),
        "rubric_sha256": canonical_sha256(rubric),
        "method_output_read": False,
        "development_only": True,
    }
    return rubric, provenance


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition-id", required=True)
    parser.add_argument("--blinding-salt-file", type=Path, required=True)
    parser.add_argument("--rubric-output", type=Path, required=True)
    parser.add_argument("--provenance-output", type=Path, required=True)
    args = parser.parse_args()
    rubric, provenance = build(args.condition_id, args.blinding_salt_file.read_text().strip())
    args.rubric_output.write_bytes(canonical_json_bytes(rubric) + b"\n")
    args.provenance_output.write_bytes(canonical_json_bytes(provenance) + b"\n")


if __name__ == "__main__":
    main()
