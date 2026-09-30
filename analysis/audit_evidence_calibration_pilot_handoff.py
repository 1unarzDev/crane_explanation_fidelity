#!/usr/bin/env python3
"""Audit the retained development pilot before blinded atomic annotation.

This is a read-only inventory. It never parses response meaning or joins method labels.
"""

from __future__ import annotations

import json
from pathlib import Path

from evidence_calibration_io import canonical_sha256
from audit_evidence_calibration_pilot_atomization import audit as audit_atomization
from audit_evidence_calibration_pilot_rubric_bundle import audit as audit_rubrics
from audit_evidence_calibration_pilot_source_context_bundle import audit as audit_source_bundle
from build_evidence_calibration_pilot_source_context import build as build_source_context
from run_evidence_calibration_b2_pilot import _materialize
from validate_evidence_calibration_pilot_inputs import validate


ROOT = Path(__file__).resolve().parents[1]
PILOT = "evidence-calibration-b2-b4-pilot-v1"


def audit(root: Path = ROOT) -> dict:
    validation = json.loads((root / f"manifests/study/{PILOT}-input-validation.json").read_text())
    status = json.loads((root / f"manifests/study/{PILOT}-execution-status.json").read_text())
    pilot = json.loads((root / f"research/explanation_fidelity/experiment_configs/development/{PILOT}.json").read_text())
    schedule = json.loads((root / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    catalog = json.loads((root / "configs/evidence_calibration_ladders_v1_development.json").read_text())
    outputs = root / "model_outputs" / PILOT
    expected = {
        condition_id: (row["family"], packet_hash, diagnostic)
        for row in validation["episodes"]
        for condition_id, packet_hash, diagnostic in zip(
            row["condition_ids"], row["condition_packet_sha256s"], row["diagnostics"], strict=True
        )
    }
    b2_paths = {path.stem: path for path in (outputs / "b2").glob("*.json")}
    failure_paths = {path.stem: path for path in (outputs / "technical_failures").glob("*.json")}
    errors: list[str] = []
    if canonical_sha256(validate(root, pilot, schedule)) != canonical_sha256(validation):
        errors.append("retained B4 and condition validation differs from a fresh deterministic rebuild")
    catalog_by_id = {ladder["ladder_id"]: ladder for ladder in catalog["ladders"]}
    family_ladder = {
        "persistent_command_motion_discrepancy": "command-motion-full-v1-development",
        "measured_response_recovery": "command-motion-full-v1-development",
        "missing_decisive_evidence": "command-motion-missing-odometry-v1-development",
        "nominal_false_premise": "nominal-false-premise-v1-development",
    }
    catalog_role_mismatches = []
    for row in validation["episodes"]:
        ladder = catalog_by_id[family_ladder[row["family"]]]
        for index, condition_id in enumerate(row["condition_ids"]):
            entry, _, _ = _materialize(root, pilot, schedule, condition_id)
            actual = set(entry["method_packet"]["evidence"])
            declared = set(ladder["levels"][index]["available_evidence_roles"])
            if actual != declared:
                catalog_role_mismatches.append({
                    "condition_id": condition_id,
                    "extra_roles": sorted(actual - declared),
                    "missing_roles": sorted(declared - actual),
                })
    if set(b2_paths) | set(failure_paths) != set(expected) or set(b2_paths) & set(failure_paths):
        errors.append("B2 outputs and retained failures do not partition the fixed condition inventory")
    if set(failure_paths) != set(status["b2"]["failed_conditions"]):
        errors.append("retained technical failure IDs differ from execution status")
    if len(b2_paths) != status["b2"]["valid_outputs"]:
        errors.append("B2 output count differs from execution status")
    if len(expected) != status["within_episode_conditions_scheduled"]:
        errors.append("fixed ladder count differs from execution status")
    if len(validation["episodes"]) != status["independent_episode_count_scheduled"]:
        errors.append("episode count differs from execution status")
    if validation["b4_outputs_generated"] != status["b4"]["outputs_complete"]:
        errors.append("B4 output count differs from execution status")

    cache_root = root / "research/explanation_fidelity/model_cache" / PILOT
    source_context_count = 0
    for condition_id, path in sorted(b2_paths.items()):
        if condition_id not in expected:
            continue
        family, packet_hash, _ = expected[condition_id]
        value = json.loads(path.read_text())
        if (value.get("schema") != "crane-evidence-calibration-b2-development-output/v1"
                or value.get("pilot_id") != PILOT or value.get("condition_id") != condition_id
                or value.get("method") != "B2" or value.get("family") != family
                or value.get("method_packet_sha256") != packet_hash
                or not value.get("development_only") or not value.get("single_call_no_retry")
                or not isinstance(value.get("answer"), str) or not value["answer"].strip()):
            errors.append(f"invalid B2 envelope: {condition_id}")
            continue
        cache_path = cache_root / f'{value["cache_key"]}.json'
        if not cache_path.is_file():
            errors.append(f"missing B2 call record: {condition_id}")
            continue
        record = json.loads(cache_path.read_text())
        if (canonical_sha256(record) != value["raw_call_record_sha256"]
                or record.get("return_code") != 0
                or record.get("parsed_final", {}).get("answer") != value["answer"]):
            errors.append(f"B2 call record mismatch: {condition_id}")
        try:
            build_source_context(condition_id, root)
        except (ValueError, KeyError, FileNotFoundError) as error:
            errors.append(f"B2 source context mismatch: {condition_id}: {error}")
        else:
            source_context_count += 1
    for condition_id, path in sorted(failure_paths.items()):
        if condition_id not in expected:
            continue
        value = json.loads(path.read_text())
        if (value.get("schema") != "crane-evidence-calibration-b2-technical-failure/v1"
                or value.get("condition_id") != condition_id
                or value.get("method_packet_sha256") != expected[condition_id][1]
                or value.get("valid_model_output") is not False
                or value.get("retry_performed") is not False):
            errors.append(f"technical failure disposition mismatch: {condition_id}")
    for condition_id, (_, _, diagnostic) in expected.items():
        if (diagnostic["condition_id"] != condition_id
                or diagnostic["b4_audit_status"] != "ACCEPTED"
                or not diagnostic["b4_final_response"].strip()):
            errors.append(f"invalid retained B4 result: {condition_id}")

    packet_root = root / "model_outputs/annotation_packets" / PILOT
    packet_count = len(list(packet_root.glob("atomic-packet-*.json"))) if packet_root.exists() else 0
    atomization_bank = packet_root / "atomization-bank.json"
    atomization_bank_entries = 0
    if atomization_bank.exists():
        atomization_bank_entries = json.loads(atomization_bank.read_text()).get("response_count", 0)
    try:
        atomization = audit_atomization(
            root / "model_outputs/automated_annotations/evidence-calibration-b2-b4-pilot-v1-atomization-v2",
            allow_incomplete=True,
        )
        rubric_bundle = audit_rubrics(root)
        source_bundle = audit_source_bundle(root)
    except (ValueError, KeyError, FileNotFoundError) as error:
        errors.append(f"annotation preparation audit failed: {error}")
        atomization, rubric_bundle, source_bundle = None, None, None
    complete_episodes = [
        row["run_id"] for row in validation["episodes"]
        if set(row["condition_ids"]) <= set(b2_paths)
    ]
    incomplete_episodes = [
        row["run_id"] for row in validation["episodes"]
        if not set(row["condition_ids"]) <= set(b2_paths)
    ]
    handoff_gaps = []
    if not errors and packet_count == 0:
        handoff_gaps.append(
            f"Only {atomization['structural_returns']}/114 atomization records exist; "
            f"ambiguous technical request count is {atomization['retained_ambiguous_technical_interruptions']}; "
            "no per-response semantic completeness review exists"
        )
        handoff_gaps.append("Extractor abstraction tags are unqualified and cannot anchor endpoint scoring")
        handoff_gaps.append("The common source-context annotation extension has no passing synthetic canary")
    if catalog_role_mismatches:
        handoff_gaps.append("Nominal control masks retain source and BT roles excluded by the declared development ladder")
    return {
        "schema": "crane-evidence-calibration-pilot-handoff-audit/v1",
        "pilot_id": PILOT,
        "status": (
            "INVALID_RETAINED_OUTPUTS" if errors else
            "RETAINED_OUTPUTS_VALID_WITH_CATALOG_ROLE_MISMATCH" if catalog_role_mismatches else
            "RETAINED_OUTPUTS_VALID_ANNOTATION_PREPARATION_REQUIRED"
        ),
        "independent_development_episodes": len(validation["episodes"]),
        "within_episode_conditions": len(expected),
        "valid_b2_outputs": len(b2_paths),
        "hash_checked_source_contexts": source_context_count,
        "catalog_role_mismatches": catalog_role_mismatches,
        "retained_b2_technical_failures": len(failure_paths),
        "accepted_deterministic_b4_outputs": len(expected),
        "complete_paired_episode_count": len(complete_episodes),
        "incomplete_paired_episode_ids": incomplete_episodes,
        "complete_paired_condition_count": sum(
            len(row["condition_ids"]) for row in validation["episodes"]
            if row["run_id"] in complete_episodes
        ),
        "blinded_atomic_packet_files": packet_count,
        "blinded_atomization_bank_responses": atomization_bank_entries,
        "structural_atomization_returns": None if atomization is None else atomization["structural_returns"],
        "retained_ambiguous_atomization_requests": None if atomization is None else atomization["retained_ambiguous_technical_interruptions"],
        "reviewed_method_blind_rubrics": None if rubric_bundle is None else rubric_bundle["rubrics"],
        "common_source_context_conditions": None if source_bundle is None else source_bundle["condition_count"],
        "handoff_gaps": handoff_gaps,
        "confirmatory_independent_n": 0,
        "errors": errors,
    }


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if not result["errors"] else 1)
