#!/usr/bin/env python3
"""Dry-build the fixed development-pilot ladders and emit only compact provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_nested_evidence_conditions import build_conditions
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from evaluate_command_motion_requirements import evaluate
from maximal_supported_diagnosis import diagnose
from normalize_command_motion_evidence import normalize
from realize_evidence_calibrated_explanation import realize


OUTPUT_SCHEMA = "crane-evidence-calibration-pilot-input-validation/v1"


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path, pilot: dict[str, Any], source_schedule: dict[str, Any]) -> dict[str, Any]:
    runs = {item["run_id"]: item for item in source_schedule["cohorts"][0]["runs"]}
    family_map = {
        "persistent-discrepancy": "persistent_command_motion_discrepancy",
        "transient-compensation": "measured_response_recovery",
        "ambiguous-missing-odometry": "missing_decisive_evidence",
        "nominal-false-premise": "nominal_false_premise",
    }
    builder_path = root / "analysis/build_nested_evidence_conditions.py"
    ontology = json.loads((root / "configs/evidence_calibration_claim_contracts_v1.json").read_text())
    nodes = {item["node_id"]: item for item in ontology["diagnostic_nodes"]}
    rows, condition_count = [], 0
    state_counts: dict[str, int] = {}
    for run_id in pilot["selection"]["episode_ids"]:
        run = runs[run_id]
        family = family_map[run["family"]]
        diagnostic_path = root / f"data/robot_visible/dev/{run_id}/command-motion-diagnostic-v3.json"
        diagnostic = json.loads(diagnostic_path.read_text())
        question = "The episode succeeded; was there nevertheless a navigation failure, and what does the evidence support?" \
            if family == "nominal_false_premise" else \
            "What is the strongest navigation diagnosis supported by the available robot-visible evidence?"
        source = normalize(diagnostic, configuration_id=run["cluster_id"], question=question,
                           omit_odometry=family == "missing_decisive_evidence")
        roles = list(source["evidence"])
        if family == "nominal_false_premise":
            removals = [
                ["/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"],
                ["/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], [],
            ]
        elif family == "missing_decisive_evidence":
            removals = [
                ["/evidence/behavior_tree_transitions", "/evidence/source_anchors", "/evidence/delivered_command_stream"],
                ["/evidence/delivered_command_stream"], [],
            ]
        else:
            removals = [
                ["/evidence/behavior_tree_transitions", "/evidence/source_anchors", "/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"],
                ["/evidence/delivered_command_stream", "/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"],
                ["/evidence/delivered_odometry_stream", "/evidence/command_motion_computation"], [],
            ]
        source_meta = diagnostic["source"]
        conditions = []
        for index, pointers in enumerate(removals):
            conditions.append({
                "condition_id": f"{run_id}-E{index}", "level_index": index,
                "removed_json_pointers": pointers,
                "mask_id": None if not pointers else f"{family}-E{index}",
                "mask_version": None if not pointers else "v1-development",
            })
        spec = {
            "schema": "crane-nested-evidence-mask-spec/v1",
            "ladder_id": f"{family}-ladder-v1-development",
            "condition_builder_id": "nested-evidence-condition-builder",
            "condition_builder_version": "v1",
            "condition_builder_sha256": file_sha(builder_path),
            "source_configuration_sha256": source_meta["nav2_config_sha256"],
            "runtime_manifest_sha256": source_meta["runtime_manifest_sha256"],
            "conditions": conditions,
        }
        bundle = build_conditions(source, spec)
        required_families = ["false_premise"] if family == "nominal_false_premise" else \
            ["command_motion"]
        question_contract = {
            "question_id": f"{family}-question-v1-development", "failure_premise": True,
            "required_mechanism_families": required_families,
        }
        diagnostics = []
        for entry in bundle:
            facts = evaluate(ontology, entry, question_contract)
            diagnosis = diagnose(ontology, entry, facts)
            required_claims = sorted({
                claim_id for node_id in diagnosis["maximal_node_ids"]
                for claim_id in nodes[node_id]["claim_ids"]
            })
            numeric_values = []
            if "claim-command-motion-discrepancy" in required_claims:
                computation = entry["method_packet"]["evidence"]["command_motion_computation"]
                measurements = {item["id"]: item for item in computation["measurements"]}
                command = measurements["discrepancy_commanded_planar_speed"]
                measured = measurements["discrepancy_measured_planar_speed"]
                support = "command-motion-computation"
                numeric_values = [
                    {"claim_id": "claim-command-motion-discrepancy", "slot_id": "commanded_speed",
                     "value": command["value"], "unit": command["unit"], "support_reference": support},
                    {"claim_id": "claim-command-motion-discrepancy", "slot_id": "measured_speed",
                     "value": measured["value"], "unit": measured["unit"], "support_reference": support},
                    {"claim_id": "claim-command-motion-discrepancy", "slot_id": "interval_start",
                     "value": command["interval_s"][0], "unit": "s", "support_reference": support},
                    {"claim_id": "claim-command-motion-discrepancy", "slot_id": "interval_end",
                     "value": command["interval_s"][1], "unit": "s", "support_reference": support},
                ]
            plan = {
                "schema": "crane-claim-realization-plan/v1",
                "plan_id": f"{entry['condition']['condition_id']}-B4-plan-v1-development",
                "diagnostic_result_sha256": canonical_sha256(diagnosis),
                "required_claim_ids": required_claims, "optional_claim_ids": [],
                "required_non_entailment_ids": diagnosis["required_non_entailment_ids"],
                "approved_numeric_values": numeric_values,
            }
            clauses = [
                {"clause_id": f"claim-{index}", "kind": "CLAIM", "contract_id": claim_id,
                 "numeric_values": [
                     {"slot_id": item["slot_id"], "value": item["value"], "unit": item["unit"]}
                     for item in numeric_values if item["claim_id"] == claim_id
                 ]}
                for index, claim_id in enumerate(required_claims)
            ] + [
                {"clause_id": f"limit-{index}", "kind": "NON_ENTAILMENT",
                 "contract_id": relation_id, "numeric_values": []}
                for index, relation_id in enumerate(diagnosis["required_non_entailment_ids"])
            ]
            candidate = {
                "schema": "crane-claim-realization-candidate/v1",
                "response_id": f"{entry['condition']['condition_id']}-B4-v1-development",
                "plan_sha256": canonical_sha256(plan), "clauses": clauses,
            }
            realized = realize(ontology, diagnosis, plan, candidate)
            state_counts[diagnosis["state"]] = state_counts.get(diagnosis["state"], 0) + 1
            diagnostics.append({
                "condition_id": entry["condition"]["condition_id"], "state": diagnosis["state"],
                "approved_claim_ids": diagnosis["approved_claim_ids"],
                "maximal_node_ids": diagnosis["maximal_node_ids"],
                "required_non_entailment_ids": diagnosis["required_non_entailment_ids"],
                "diagnostic_result_sha256": canonical_sha256(diagnosis),
                "realization_plan_sha256": canonical_sha256(plan),
                "b4_response_id": candidate["response_id"],
                "b4_final_response": realized["final_response"],
                "b4_audit_status": realized["audit"]["status"],
                "b4_output_sha256": canonical_sha256(realized),
            })
        condition_count += len(bundle)
        rows.append({
            "run_id": run_id, "family": family, "diagnostic_path": str(diagnostic_path.relative_to(root)),
            "diagnostic_sha256": file_sha(diagnostic_path), "normalized_source_sha256": canonical_sha256(source),
            "mask_spec_sha256": canonical_sha256(spec), "condition_count": len(bundle),
            "condition_ids": [item["condition"]["condition_id"] for item in bundle],
            "condition_packet_sha256s": [item["condition"]["method_packet_sha256"] for item in bundle],
            "strongest_available_roles": roles,
            "diagnostics": diagnostics,
        })
    return {
        "schema": OUTPUT_SCHEMA, "pilot_id": pilot["pilot_id"],
        "pilot_config_sha256": canonical_sha256(pilot), "source_schedule_sha256": canonical_sha256(source_schedule),
        "status": "B4_DEVELOPMENT_OUTPUTS_COMPLETE_B2_NOT_RUN_AT_BUILD_TIME", "independent_episode_count": len(rows),
        "within_episode_condition_count": condition_count, "b4_outputs_generated": condition_count,
        "b2_model_outputs_generated": 0,
        "human_annotations_collected": 0, "diagnostic_state_counts": state_counts,
        "episodes": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--pilot", type=Path, default=Path("research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json"))
    parser.add_argument("--schedule", type=Path, default=Path("research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    resolve = lambda path: path if path.is_absolute() else root / path
    output = validate(root, json.loads(resolve(args.pilot).read_text()), json.loads(resolve(args.schedule).read_text()))
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
