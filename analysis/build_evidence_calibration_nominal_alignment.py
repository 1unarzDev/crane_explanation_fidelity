#!/usr/bin/env python3
"""Prospective nominal control projection; preserve old pilot packets and responses."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from build_nested_evidence_conditions import _remove_pointer, build_conditions
from build_evidence_calibration_pilot_support_packets import write_once
from evidence_calibration_io import canonical_sha256
from evaluate_command_motion_requirements import evaluate
from maximal_supported_diagnosis import diagnose
from normalize_command_motion_evidence import normalize
from run_evidence_calibration_b2_pilot import _materialize
from validate_evidence_calibration_ladder_materialization import validate_materialization

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = "research/explanation_fidelity/experiment_configs/development/evidence-calibration-nominal-alignment-v1.json"
AUDIT = "manifests/study/evidence-calibration-nominal-alignment-v1-development.json"
LADDER_ID = "nominal-false-premise-v1-development"
QUESTION = "Why did this episode exhibit a sustained command–measured-motion discrepancy under the registered diagnostic computation?"
TRACE_MEASUREMENTS = {"follow_path_failures", "source_qualified_wait_recoveries"}
NOMINAL_MEASUREMENTS = {"calibrated_healthy_commanded_planar_speed", "calibrated_healthy_planar_speed", "action_status"}
TRACE_ASSUMPTION = "Source-qualified recovery counts use the retained behavior-tree policy and transition stream."


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project(diagnostic: dict, configuration_id: str, question: str = QUESTION) -> tuple[dict, list[str], dict]:
    """Remove trace roles and duplicated trace facts; never modify surviving evidence values."""
    if question != QUESTION:
        raise ValueError("prospective nominal question scope changed")
    original = normalize(diagnostic, configuration_id=configuration_id, question=question)
    evidence = original["evidence"]
    if (evidence["navigate_to_pose_result"]["action_status"] != "succeeded"
            or evidence["command_motion_computation"]["diagnostic_disposition"] != "not_triggered"):
        raise ValueError("retained recording does not satisfy the declared nominal command-motion control")
    for role in ("delivered_command_stream", "delivered_odometry_stream"):
        if not evidence[role]["samples"] or not evidence[role]["provenance"]:
            raise ValueError("nominal non-trigger control needs valid delivered command and measured-motion evidence")
    computation = evidence["command_motion_computation"]
    measurements = computation["measurements"]
    ids = [item["id"] for item in measurements]
    if len(ids) != len(set(ids)) or set(ids) != NOMINAL_MEASUREMENTS | TRACE_MEASUREMENTS:
        raise ValueError("nominal diagnostic measurement inventory changed; review projection before reuse")
    if computation["assumptions"].count(TRACE_ASSUMPTION) != 1:
        raise ValueError("registered trace-derived computation assumption changed")
    removed = ["/evidence/behavior_tree_transitions", "/evidence/source_anchors"]
    removed += [f"/evidence/command_motion_computation/measurements/{index}"
                for index, item in enumerate(measurements) if item["id"] in TRACE_MEASUREMENTS]
    removed += [f"/evidence/command_motion_computation/assumptions/{index}"
                for index, item in enumerate(computation["assumptions"]) if item == TRACE_ASSUMPTION]
    projected = copy.deepcopy(original)
    # Delete array entries from the greatest index first; indices refer to the unmodified source.
    for pointer in sorted(removed, key=lambda p: (p.rsplit("/", 1)[0], int(p.rsplit("/", 1)[1]) if p.rsplit("/", 1)[1].isdigit() else -1), reverse=True):
        _remove_pointer(projected, pointer)
    if set(projected["evidence"]) != {"navigate_to_pose_result", "delivered_command_stream", "delivered_odometry_stream", "command_motion_computation"}:
        raise ValueError("prospective nominal projection has undeclared roles")
    return projected, sorted(removed), original


def materialize(diagnostic: dict, configuration_id: str, catalog: dict) -> tuple[list[dict], dict]:
    source, removed, original = project(diagnostic, configuration_id)
    ladder = next(item for item in catalog["ladders"] if item["ladder_id"] == LADDER_ID)
    terminal_roles = set(ladder["terminal_evidence_roles"])
    spec = {"schema": "crane-nested-evidence-mask-spec/v1", "ladder_id": LADDER_ID,
            "condition_builder_id": "nested-evidence-condition-builder", "condition_builder_version": "v1",
            "condition_builder_sha256": digest(ROOT / "analysis/build_nested_evidence_conditions.py"),
            "source_configuration_sha256": diagnostic["source"]["nav2_config_sha256"],
            "runtime_manifest_sha256": diagnostic["source"]["runtime_manifest_sha256"],
            "conditions": []}
    for level in ladder["levels"]:
        index = level["level_index"]
        pointers = sorted(f"/evidence/{role}" for role in terminal_roles - set(level["available_evidence_roles"]))
        spec["conditions"].append({"condition_id": f"{diagnostic['episode_id']}-nominal-aligned-v1-E{index}",
            "level_index": index, "removed_json_pointers": pointers,
            "mask_id": f"nominal-aligned-v1-E{index}" if pointers else None,
            "mask_version": "v1-development-source-projection" if pointers else None})
    conditions = build_conditions(source, spec)
    checked = validate_materialization(catalog, LADDER_ID, conditions)
    return conditions, {"source_projection_removed_json_pointers": removed,
                        "unprojected_source_with_new_question_sha256": canonical_sha256(original),
                        "projected_source_sha256": canonical_sha256(source),
                        "mask_spec_sha256": canonical_sha256(spec), "materialization_audit": checked}


def build(root: Path = ROOT) -> dict:
    if root.resolve() != ROOT.resolve():
        raise ValueError("nominal alignment must use the audited checkout")
    declaration = json.loads((root / DECLARATION).read_text())
    if (declaration["question_text"] != QUESTION or declaration["source_episode_ids"] != ["cm-land-conf-054", "cm-land-conf-072"]
            or any(declaration[field] is not False for field in ("model_calls_authorized", "physical_acquisition_authorized", "p11_authorized", "confirmation_authorized"))):
        raise ValueError("nominal prospective declaration scope changed")
    for item in declaration["bindings"].values():
        if digest(root / item["path"]) != item["raw_sha256"]:
            raise ValueError("nominal prospective declaration binding changed")
    def load(name):
        return json.loads((root / declaration["bindings"][name]["path"]).read_text())
    catalog, ontology, pilot, schedule, old_validation = (load(name) for name in ("ladder_catalog", "ontology", "old_pilot", "source_schedule", "old_input_validation"))
    rows = []
    for episode_id in declaration["source_episode_ids"]:
        old = next(item for item in old_validation["episodes"] if item["run_id"] == episode_id)
        if digest(root / old["diagnostic_path"]) != old["diagnostic_sha256"]:
            raise ValueError("retained physical diagnostic changed")
        diagnostic = json.loads((root / old["diagnostic_path"]).read_text())
        old_entries = [_materialize(root, pilot, schedule, f"{episode_id}-E{index}")[0] for index in range(3)]
        if [entry["condition"]["method_packet_sha256"] for entry in old_entries] != old["condition_packet_sha256s"]:
            raise ValueError("historical nominal packet hashes no longer reproduce")
        conditions, projection = materialize(diagnostic, old_entries[0]["condition"]["configuration_id"], catalog)
        reference_rows = []
        for entry in conditions:
            question_contract = {"question_id": "nominal-registered-discrepancy-premise-v1-development",
                                 "failure_premise": True, "required_mechanism_families": ["false_premise"]}
            facts = evaluate(ontology, entry, question_contract)
            reference = diagnose(ontology, entry, facts)
            requirements = {item["requirement_id"]: item["status"] for item in facts["requirement_evaluations"]}
            index = entry["condition"]["level_index"]
            if (requirements["req-no-failure-triggered"] != ("SATISFIED" if index == 2 else "ABSENT")
                    or ("claim-false-premise-success" in reference["approved_claim_ids"]) != (index == 2)
                    or "claim-command-motion-discrepancy" in reference["approved_claim_ids"]
                    or "claim-measured-response-recovered" in reference["approved_claim_ids"]
                    or "claim-task-success" not in reference["approved_claim_ids"]):
                raise ValueError("nominal candidate does not preserve supported outcome and the full non-trigger boundary")
            reference_rows.append({"condition_id": entry["condition"]["condition_id"], "level_index": index,
                "method_packet_sha256": entry["condition"]["method_packet_sha256"],
                "available_evidence_roles": list(entry["condition"]["available_evidence_roles"]),
                "registered_non_trigger_requirement": requirements["req-no-failure-triggered"],
                "reference_state": reference["state"], "approved_claim_ids": list(reference["approved_claim_ids"]),
                "reference_sha256": canonical_sha256(reference)})
        rows.append({"episode_id": episode_id, "retained_diagnostic": {"path": old["diagnostic_path"], "raw_sha256": old["diagnostic_sha256"]},
                     "old_condition_ids": old["condition_ids"], "old_packet_sha256s": old["condition_packet_sha256s"],
                     "old_role_mismatch_count": sum(set(entry["method_packet"]["evidence"]) != set(level["available_evidence_roles"])
                         for entry, level in zip(old_entries, next(x for x in catalog["ladders"] if x["ladder_id"] == LADDER_ID)["levels"])),
                     **projection, "conditions": reference_rows})
    if sum(row["old_role_mismatch_count"] for row in rows) != 6:
        raise ValueError("historical nominal mismatch count changed")
    return {"schema": "crane-nominal-alignment-audit/v1-development", "status": "PASS_PROSPECTIVE_PACKET_AND_QUESTION_CANDIDATE_NOT_EXECUTED",
            "recorded_date": "2026-09-30", "declaration": {"path": DECLARATION, "raw_sha256": digest(root / DECLARATION)},
            "episode_count": 2, "within_episode_condition_count": 6, "historical_role_mismatches_preserved": 6,
            "question_scope": "registered sustained command-measured-motion discrepancy, not every local software failure",
            "episodes": rows, "semantic_method_outputs_generated": 0, "model_call_attempted": False,
            "physical_acquisition_attempted": False, "old_packets_or_answers_changed": False, "old_responses_rescored": False,
            "fresh_five_method_development_run_complete": False, "pilot_support_gate_changed": False,
            "p11_authorized": False, "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    output = build()
    if args.write:
        write_once(ROOT / AUDIT, output)
    elif (ROOT / AUDIT).exists() and json.loads((ROOT / AUDIT).read_text()) != output:
        raise ValueError("nominal alignment audit differs from its bound reconstruction")
    print(json.dumps(output, indent=2, sort_keys=True))
