#!/usr/bin/env python3
"""Reconstruct aligned five-method packets in memory; audit only, with zero execution."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_ontology_v2_wording import audit as audit_wording
from build_evidence_calibration_method_packets import build as build_methods
from build_evidence_calibration_nominal_alignment import QUESTION, project
from build_nested_evidence_conditions import build_conditions
from evidence_calibration_io import canonical_sha256
from normalize_command_motion_evidence import normalize
from run_evidence_calibration_b2_pilot import _materialize
from validate_evidence_calibration_ladder_materialization import validate_materialization

ROOT = Path(__file__).resolve().parents[1]
PILOT = "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json"
SCHEDULE = "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json"
VALIDATION = "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json"
CATALOG = "configs/evidence_calibration_ladders_v1_development.json"
ONTOLOGY = "configs/evidence_calibration_claim_contracts_v2_development.json"
OUTPUT = "manifests/study/evidence-calibration-five-method-packet-candidate-v1-development.json"
LADDER_MAP = {
    "persistent_command_motion_discrepancy": "command-motion-full-v1-development",
    "measured_response_recovery": "command-motion-full-v1-development",
    "missing_decisive_evidence": "command-motion-missing-odometry-v1-development",
    "nominal_false_premise": "nominal-false-premise-v1-development",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def materialize(diagnostic: dict, configuration_id: str, family: str, catalog: dict) -> list[dict]:
    if family not in LADDER_MAP:
        raise ValueError("family is outside the fixed land pilot")
    source = project(diagnostic, configuration_id)[0] if family == "nominal_false_premise" else normalize(
        diagnostic, configuration_id=configuration_id,
        question="What is the strongest navigation diagnosis supported by the available robot-visible evidence?",
        omit_odometry=family == "missing_decisive_evidence")
    ladder = next(item for item in catalog["ladders"] if item["ladder_id"] == LADDER_MAP[family])
    spec = {"schema": "crane-nested-evidence-mask-spec/v1", "ladder_id": ladder["ladder_id"],
            "condition_builder_id": "nested-evidence-condition-builder", "condition_builder_version": "v1",
            "condition_builder_sha256": digest(ROOT / "analysis/build_nested_evidence_conditions.py"),
            "source_configuration_sha256": diagnostic["source"]["nav2_config_sha256"],
            "runtime_manifest_sha256": diagnostic["source"]["runtime_manifest_sha256"], "conditions": []}
    for level in ladder["levels"]:
        index = level["level_index"]
        pointers = sorted(f"/evidence/{role}" for role in set(ladder["terminal_evidence_roles"])
                          - set(level["available_evidence_roles"]))
        spec["conditions"].append({"condition_id": f"{diagnostic['episode_id']}-five-method-aligned-v1-E{index}",
            "level_index": index, "removed_json_pointers": pointers,
            "mask_id": f"five-method-aligned-v1-E{index}" if pointers else None,
            "mask_version": "v1-development" if pointers else None})
    entries = build_conditions(source, spec)
    validate_materialization(catalog, ladder["ladder_id"], entries)
    return entries


def execution_contract(entry: dict, diagnostic: dict) -> dict:
    """Hash-check actual permitted source files; do not provide diagnostic labels to B2."""
    paths = [
        ("bt-policy", "packages/crane_ml/Tools/Performance/nav2_land_progress_recovery.xml", "bt_policy_sha256"),
        ("nav2-config", "packages/crane_ml/Tools/Performance/nav2_land_proving_ground_fixture.yaml", "nav2_config_sha256"),
        ("diagnostic-config", "configs/diagnostic_command_motion_low_speed_v1.json", "diagnostic_config_sha256"),
    ]
    assets = []
    for identifier, relative, key in paths:
        sha = digest(ROOT / relative)
        if sha != diagnostic["source"][key]:
            raise ValueError("retained exact source/configuration asset changed")
        assets.append({"asset_id": identifier, "version": "retained-source-v1", "sha256": sha})
    packet = entry["method_packet"]
    # Lossless raw serialization is a presentation candidate, not a finalized B0 prompt.
    raw = json.dumps(packet, indent=2, sort_keys=True, allow_nan=False)
    if json.loads(raw) != packet:
        raise ValueError("raw presentation lost robot-visible facts")
    return {"contract_id": "five-method-aligned-packet-candidate-v1-development",
            "ordinary_runtime_presentation": raw,
            "presentation_evidence_ids": list(entry["condition"]["available_evidence_ids"]),
            "source_assets": assets,
            "primitive_tools": [{"asset_id": "inspect-evidence-calibration-packet", "version": "v1-development",
                                 "sha256": digest(ROOT / "analysis/inspect_evidence_calibration_packet.py")}],
            "question_instruction": packet["question"],
            "contract_assets": [{"asset_id": "claim-contracts", "version": "v2-development",
                                 "sha256": digest(ROOT / ONTOLOGY)}]}


def build() -> dict:
    audit_wording()
    def load(relative):
        return json.loads((ROOT / relative).read_text())
    pilot, schedule, validation, catalog = [load(path) for path in (PILOT, SCHEDULE, VALIDATION, CATALOG)]
    selected = pilot["selection"]["episode_ids"]
    originals = {item["run_id"]: item for item in validation["episodes"]}
    if (len(selected) != 16 or len(set(selected)) != len(selected) or set(selected) != set(originals)
            or pilot["independent_episode_count"] != len(selected)):
        raise ValueError("fixed inspected development selection changed")
    rows, families, configurations, condition_ids = [], Counter(), set(), set()
    for run_id in selected:
        original = originals[run_id]
        diagnostic_path = ROOT / original["diagnostic_path"]
        if digest(diagnostic_path) != original["diagnostic_sha256"]:
            raise ValueError("retained diagnostic changed")
        diagnostic = json.loads(diagnostic_path.read_text())
        old_entries = [_materialize(ROOT, pilot, schedule, condition_id) for condition_id in original["condition_ids"]]
        if [item[0]["condition"]["method_packet_sha256"] for item in old_entries] != original["condition_packet_sha256s"]:
            raise ValueError("old packet hashes no longer reproduce")
        family = old_entries[0][2]
        configuration = old_entries[0][0]["condition"]["configuration_id"]
        if configuration in configurations:
            raise ValueError("two selected episodes share an independent configuration")
        configurations.add(configuration)
        families[family] += 1
        entries = materialize(diagnostic, configuration, family, catalog)
        conditions = []
        for entry in entries:
            contract = execution_contract(entry, diagnostic)
            packets = build_methods(entry, contract)
            method_packets = {item["method_id"]: item for item in packets["method_packets"]}
            if set(method_packets) != {"B0", "B1", "B2", "B3", "B4"}:
                raise ValueError("five-method packet inventory is incomplete")
            if (json.loads(method_packets["B0"]["presentation"]) != method_packets["B1"]["presentation"]
                    or any(method_packets[method]["question_instruction"] != entry["method_packet"]["question"]
                           for method in method_packets)):
                raise ValueError("raw/structured evidence or question parity changed")
            condition = entry["condition"]
            if condition["condition_id"] in condition_ids:
                raise ValueError("duplicate prospective condition identity")
            condition_ids.add(condition["condition_id"])
            conditions.append({"condition_id": condition["condition_id"], "level_index": condition["level_index"],
                "method_packet_sha256": condition["method_packet_sha256"],
                "available_evidence_roles": list(condition["available_evidence_roles"]),
                "question_sha256": hashlib.sha256(contract["question_instruction"].encode()).hexdigest(),
                "method_packet_set_sha256": canonical_sha256(packets),
                "method_packet_hashes": {method: item["packet_sha256"] for method, item in method_packets.items()},
                "b2_b4_source_assets_sha256": packets["b2_b4_source_assets_sha256"],
                "b2_b4_primitive_tools_sha256": packets["b2_b4_primitive_tools_sha256"]})
        rows.append({"source_run_id": run_id, "raw_episode_id": diagnostic["episode_id"],
            "configuration_id": configuration, "family": family, "ladder_id": LADDER_MAP[family],
            "retained_diagnostic_sha256": original["diagnostic_sha256"],
            "historical_packet_hashes_preserved": original["condition_packet_sha256s"], "conditions": conditions})
    if dict(families) != pilot["selection"]["family_quotas"] or len(condition_ids) != 60:
        raise ValueError("fixed quotas or ladder counts changed")
    sources = (PILOT, SCHEDULE, VALIDATION, CATALOG, ONTOLOGY,
               "analysis/build_evidence_calibration_five_method_packet_candidate.py",
               "analysis/build_evidence_calibration_method_packets.py",
               "analysis/build_evidence_calibration_nominal_alignment.py",
               "analysis/inspect_evidence_calibration_packet.py",
               "manifests/operations/evidence-calibration-combined-support-canary-disposition-v1.json",
               "docs/FIVE_METHOD_PACKET_CANDIDATE_2026-09-30.md")
    return {"schema": "crane-five-method-packet-candidate/v1-development", "recorded_date": "2026-09-30",
            "status": "ALIGNED_PACKETS_AUDITED_MODEL_EXECUTION_UNBOUND",
            "bindings": [{"path": path, "raw_sha256": digest(ROOT / path)} for path in sources],
            "methods": ["B0", "B1", "B2", "B3", "B4"], "independent_unit": "episode_configuration",
            "inspected_development_episode_count": len(configurations), "family_counts": dict(families),
            "within_episode_condition_count": len(condition_ids), "method_packet_count": len(condition_ids) * 5,
            "independent_n_counted_from": "unique episode/configuration pairs; never packet-set increments",
            "episodes": rows, "b0_presentation_status": "LOSSLESS_RAW_JSON_CANDIDATE_PROMPT_UNBOUND",
            "semantic_method_outputs_generated": 0, "model_calls_authorized": False, "model_call_attempted": False,
            "pilot_annotation_authorized": False, "method_key_opened": False,
            "physical_acquisition_authorized": False, "p11_authorized": False,
            "old_outputs_rescored": False, "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    result = build()
    if json.loads((ROOT / OUTPUT).read_text()) != result:
        raise ValueError("five-method packet candidate differs from retained snapshot")
    print(json.dumps({key: value for key, value in result.items() if key not in ("bindings", "episodes")},
                     indent=2, sort_keys=True))
