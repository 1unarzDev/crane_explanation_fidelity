#!/usr/bin/env python3
"""Offline full-cohort preparation/staging integration; hashes only, no model calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build as build_packets
from evidence_calibration_io import canonical_sha256, ontology_from_dict
from evaluate_command_motion_requirements import evaluate
from maximal_supported_diagnosis import diagnose
from prepare_evidence_calibration_baselines import prepare as prepare_baseline
from prepare_evidence_calibration_b3_ordinary import prepare as prepare_b3
from prepare_evidence_calibration_b4_candidate import prepare as prepare_b4
from realize_evidence_calibrated_explanation_v2 import _validate_plan
from stage_evidence_calibration_workspace import staged_workspace, verify

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = "manifests/study/evidence-calibration-method-preparation-v1-development.json"
BASELINES = "manifests/study/evidence-calibration-baseline-requests-v1-development.json"


def visible_plan(ontology: dict, entry: dict, facts: dict) -> tuple[dict, dict]:
    """Reuse the retained maximal-node plan rule and discrepancy measurement bindings."""
    result = diagnose(ontology, entry, facts)
    nodes = {row["node_id"]: row for row in ontology["diagnostic_nodes"]}
    required = sorted({claim for node in result["maximal_node_ids"] for claim in nodes[node]["claim_ids"]})
    numeric = []
    if "claim-command-motion-discrepancy" in required:
        computation = entry["method_packet"]["evidence"]["command_motion_computation"]
        measurements = {row["id"]: row for row in computation["measurements"]}
        command = measurements["discrepancy_commanded_planar_speed"]
        measured = measurements["discrepancy_measured_planar_speed"]
        bindings = [("commanded_speed", command["value"], command["unit"]),
                    ("measured_speed", measured["value"], measured["unit"]),
                    ("interval_start", command["interval_s"][0], "s"),
                    ("interval_end", command["interval_s"][1], "s")]
        numeric = [{"claim_id": "claim-command-motion-discrepancy", "slot_id": slot,
                    "value": value, "unit": unit, "support_reference": "command-motion-computation"}
                   for slot, value, unit in bindings]
    plan = {"schema": "crane-claim-realization-plan/v1",
            "plan_id": entry["condition"]["condition_id"] + "-aligned-plan-v1-development",
            "diagnostic_result_sha256": canonical_sha256(result), "required_claim_ids": required,
            "optional_claim_ids": [], "required_non_entailment_ids": result["required_non_entailment_ids"],
            "approved_numeric_values": numeric}
    _validate_plan(plan, result, ontology_from_dict(ontology))
    return result, plan


def build() -> dict:
    source = candidate.build()
    if source != json.loads((ROOT / candidate.OUTPUT).read_text()):
        raise ValueError("five-method source snapshot changed")
    ontology = json.loads((ROOT / candidate.ONTOLOGY).read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    baseline_rows = json.loads((ROOT / BASELINES).read_text())["requests"]
    baselines = {row["condition_id"]: row for row in baseline_rows}
    if len(baselines) != 60:
        raise ValueError("baseline condition inventory changed")
    rows = []
    for episode in source["episodes"]:
        diagnostic = json.loads((ROOT / f"data/robot_visible/dev/{episode['source_run_id']}/command-motion-diagnostic-v3.json").read_text())
        entries = candidate.materialize(diagnostic, episode["configuration_id"], episode["family"], catalog)
        for entry, retained in zip(entries, episode["conditions"], strict=True):
            packets = build_packets(entry, candidate.execution_contract(entry, diagnostic))
            by_id = {packet["method_id"]: packet for packet in packets["method_packets"]}
            if {method: packet["packet_sha256"] for method, packet in by_id.items()} != retained["method_packet_hashes"]:
                raise ValueError("source method packet changed")
            nominal = episode["family"] == "nominal_false_premise"
            question = {"question_id": "nominal-registered-discrepancy-premise-v1-development" if nominal
                        else episode["family"] + "-question-v1-development", "failure_premise": True,
                        "required_mechanism_families": ["false_premise"] if nominal else ["command_motion"]}
            facts = evaluate(ontology, entry, question)
            result, plan = visible_plan(ontology, entry, facts)
            requests = {method: prepare_baseline(method, entry, packets) for method in ("B0", "B1")}
            requests.update(B3=prepare_b3(ontology, entry, facts, plan, packets),
                            B4=prepare_b4(ontology, entry, facts, plan, packets))
            for method in ("B0", "B1"):
                if requests[method]["request_sha256"] != baselines[entry["condition"]["condition_id"]]["requests"][method]["request_sha256"]:
                    raise ValueError("existing baseline request changed")
            workspaces = {}
            for method, packet in by_id.items():
                with staged_workspace(entry, packet) as (workspace, identity):
                    verify(workspace, identity)
                    workspaces[method] = identity
            for method in ("B3", "B4"):
                shared = workspaces["B2"]["inventory"]["files"]
                if any(workspaces[method]["inventory"]["files"].get(path) != sha for path, sha in shared.items()):
                    raise ValueError("staged source/tool/evidence parity changed")
            rows.append({"source_run_id": episode["source_run_id"], "configuration_id": episode["configuration_id"],
                         "family": episode["family"], "condition_id": entry["condition"]["condition_id"],
                         "level_index": entry["condition"]["level_index"], "facts_sha256": canonical_sha256(facts),
                         "diagnostic_result_sha256": canonical_sha256(result), "plan_sha256": canonical_sha256(plan),
                         "requests": {method: {"request_sha256": request["request_sha256"],
                             "prompt_utf8_bytes": len(request["prompt"].encode()), "token_fit": None}
                                      for method, request in requests.items()},
                         "workspaces": {method: {"workspace_sha256": identity["workspace_sha256"],
                             "file_count": len(identity["inventory"]["files"])} for method, identity in workspaces.items()}})
    if {row["condition_id"] for row in rows} != set(baselines):
        raise ValueError("full condition inventory not covered")
    paths = ["analysis/audit_evidence_calibration_method_preparation.py",
             "tests/test_evidence_calibration_method_preparation.py", candidate.OUTPUT, BASELINES,
             "analysis/evaluate_command_motion_requirements.py", "analysis/maximal_supported_diagnosis.py",
             "analysis/validate_evidence_calibration_pilot_inputs.py", candidate.ONTOLOGY,
             "analysis/prepare_evidence_calibration_baselines.py", "analysis/prepare_evidence_calibration_b3_ordinary.py",
             "analysis/prepare_evidence_calibration_b4_candidate.py", "analysis/stage_evidence_calibration_workspace.py",
             "research/explanation_fidelity/prompts/evidence_calibration_baseline_ordinary_development_v1.txt",
             "research/explanation_fidelity/prompts/evidence_calibration_b3_ordinary_development_v1.txt",
             "research/explanation_fidelity/prompts/evidence_calibration_b4_candidate_development_v1.txt",
             "analysis/realize_evidence_calibrated_explanation_v2.py", "docs/METHOD_PREPARATION_INTEGRATION_2026-09-30.md",
             "manifests/operations/evidence-calibration-combined-support-canary-disposition-v1.json"]
    return {"schema": "crane-method-preparation-integration/v1-development", "recorded_date": "2026-09-30",
            "status": "FULL_INSPECTED_COHORT_INPUTS_STAGED_EXECUTION_UNBOUND",
            "bindings": [{"path": path, "raw_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()} for path in paths],
            "inspected_development_episode_count": len({row["configuration_id"] for row in rows}),
            "within_episode_condition_count": len(rows), "prepared_request_count": 4 * len(rows),
            "staged_workspace_count": 5 * len(rows), "prepared_methods": ["B0", "B1", "B3", "B4"],
            "b2_complete_request_bound": False, "harness_confinement_verified": False,
            "token_capacity_status": "UNVERIFIED_NO_TRUNCATION_AUTHORIZED",
            "prompt_utf8_byte_ranges": {method: {"minimum": min(row["requests"][method]["prompt_utf8_bytes"] for row in rows),
                "maximum": max(row["requests"][method]["prompt_utf8_bytes"] for row in rows)} for method in ("B0", "B1", "B3", "B4")},
            "conditions": rows, "model_calls_authorized": False, "model_call_attempted": False,
            "semantic_method_outputs_generated": 0, "pilot_annotation_authorized": False,
            "method_key_opened": False, "old_packets_or_outputs_changed": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    result = build()
    if json.loads((ROOT / OUTPUT).read_text()) != result:
        raise ValueError("method preparation differs from retained snapshot")
    print(json.dumps({key: value for key, value in result.items() if key not in ("bindings", "conditions")}, indent=2, sort_keys=True))
