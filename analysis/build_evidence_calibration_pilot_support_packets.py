#!/usr/bin/env python3
"""Mechanically assemble reviewed, blinded development support forms and a separate key."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from build_agent_atomic_claim_annotation_packets import build as build_agent_packet
from build_evidence_calibration_atomization_bank import build as rebuild_bank
from build_evidence_calibration_pilot_role_inputs import OUTPUT as ROLE_INPUTS, build as rebuild_atoms
from audit_evidence_calibration_pilot_role_inputs import audit as audit_atoms
from audit_evidence_calibration_pilot_rubric_bundle import audit as audit_rubrics
from audit_evidence_calibration_pilot_source_context_bundle import audit as audit_sources
from build_evidence_calibration_agent_qualification import LEVELS
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from run_evidence_calibration_b2_pilot import _materialize


ROOT = Path(__file__).resolve().parents[1]
PILOT = "evidence-calibration-b2-b4-pilot-v1"
DISPOSITION = "manifests/annotation/evidence-calibration-neutral-level-support-v2-disposition.json"
BUNDLE = f"model_outputs/annotation_packets/{PILOT}/support-packets-neutral-v2-v1.json"
KEY = f"data/evaluator_only/annotation_keys/{PILOT}/support-packet-key-neutral-v2-v1.json"
NON_RANK_OPTIONS = ["NO_DIAGNOSTIC_ASSERTION", "UNINTERPRETABLE"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound_disposition(root: Path) -> dict:
    disposition = json.loads((root / DISPOSITION).read_text())
    binding = disposition["qualified_binding"]
    if (disposition.get("status") != "QUALIFIED_SUPPORT_INPUT_EXTENSION_ONLY"
            or disposition.get("artifact_retention") != "DVC_PUSH_VERIFIED"
            or disposition.get("support_packet_construction_authorized") is not True
            or disposition.get("pilot_annotation_authorized") is not False
            or disposition.get("endpoint_scoring_authorized") is not False
            or disposition.get("p11_authorized") is not False
            or binding.get("model") != "gpt-6-astra" or binding.get("reasoning_effort") != "high"
            or binding.get("transport") != "codex-cli-chatgpt-login-ephemeral/v1"
            or binding.get("tools") != "none" or binding.get("quality_driven_retries") != 0
            or binding.get("atomic_input_level", "MISSING") is not None
            or binding.get("diagnostic_level_options") != LEVELS
            or binding.get("non_rank_options") != NON_RANK_OPTIONS
            or binding.get("highest_level_qualified") is not False
            or binding.get("raw_rank_endpoint_use_prohibited") is not True):
        raise ValueError("support-input disposition scope changed")
    for item in disposition["bindings"].values():
        if digest(root / item["path"]) != item["raw_sha256"]:
            raise ValueError("support-input disposition binding changed")
    for name in ("prompt", "annotation_schema", "adjudication_schema"):
        item = binding[name]
        if digest(root / item["path"]) != item["sha256"]:
            raise ValueError("qualified support component changed")
    result = json.loads((root / disposition["bindings"]["result"]["path"]).read_text())
    if (result["status"] != "PASS_INPUT_EXTENSION_PENDING_DISPOSITION"
            or len(result["passes"]) != 2
            or any(not row["passed"] or not all(row["gate_checks"].values()) for row in result["passes"])
            or disposition["pass_metrics"] != [
                {"slot": row["slot"], "metrics": row["metrics"], "gate_checks": row["gate_checks"]}
                for row in result["passes"]]):
        raise ValueError("qualified input-extension result does not reproduce its disposition")
    return disposition


def build_packet(condition: dict, response: dict, rubric: dict, salt: str, assets: list[dict]) -> tuple[dict, dict]:
    if any(claim.get("asserted_abstraction_level", "MISSING") is not None for claim in response["atomic_claims"]):
        raise ValueError("support packets cannot carry extractor or role diagnostic-level anchors")
    if rubric["abstraction_level_options"] != LEVELS:
        raise ValueError("unexpected original rubric levels")
    modified = copy.deepcopy(rubric)
    modified["abstraction_level_options"] = [*LEVELS, *NON_RANK_OPTIONS]
    packet, key = build_agent_packet(condition, response, modified, salt, assets)
    for form in packet["forms"]:
        visible = form["robot_visible_evidence"]
        if set(visible) != {"schema", "episode_id", "configuration_id", "question", "evidence", "exact_source_assets"}:
            raise ValueError("unexpected robot-visible packet envelope")
        # These two top-level IDs are packaging metadata. Preserve every evidence field and
        # exact source byte, including legitimate goal/record IDs inside the visible evidence.
        form["robot_visible_evidence"] = {
            name: value for name, value in visible.items() if name not in {"episode_id", "configuration_id"}}
    packet.update(builder_version="v1-neutral-v2-support-input", qualification_disposition=DISPOSITION,
                  qualification_status="NEUTRAL_V2_SUPPORT_FIELDS_ONLY_RANK_EXCLUDED",
                  highest_level_qualified=False, raw_rank_endpoint_use_prohibited=True)
    key.update(builder_version=packet["builder_version"], packet_set_sha256=canonical_sha256(packet))
    return packet, key


def build(root: Path = ROOT) -> tuple[dict, dict]:
    bound_disposition(root)
    # Coordination code reads the key to assemble packets. No key value is printed or placed in
    # a model-visible form; this is not a researcher/annotator method join or endpoint analysis.
    audit_atoms()
    audit_rubrics(root)
    audit_sources(root)
    salt_path = root / f"data/evaluator_only/annotation_keys/{PILOT}/atomization-salt.txt"
    salt = salt_path.read_text().strip()
    bank, expected_key = rebuild_bank(salt, root)
    bank_path = root / f"model_outputs/annotation_packets/{PILOT}/atomization-bank.json"
    original_key_path = root / f"data/evaluator_only/annotation_keys/{PILOT}/atomization-key.json"
    if (json.loads(bank_path.read_text()) != bank
            or json.loads(original_key_path.read_text()) != expected_key
            or expected_key["join_after_atomic_inventory_validation"] is not True):
        raise ValueError("original blind answer bank/key differs from its pinned reconstruction")
    role_inputs = json.loads((root / ROLE_INPUTS.relative_to(ROOT)).read_text())
    if role_inputs != rebuild_atoms():
        raise ValueError("reviewed atomic inputs changed")
    key_rows = {row["opaque_response_id"]: row for row in expected_key["entries"]}
    answers = {row["opaque_response_id"]: row["response_text"] for row in bank["entries"]}
    pilot = json.loads((root / f"research/explanation_fidelity/experiment_configs/development/{PILOT}.json").read_text())
    schedule = json.loads((root / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json").read_text())
    assets_path = root / f"model_outputs/annotation_packets/{PILOT}/source-assets-v1.json"
    assets = json.loads(assets_path.read_text())
    packets, joins = [], []
    for entry in role_inputs["entries"]:
        opaque_id = entry["case_id"]
        join = key_rows[opaque_id]
        if (entry["response_text"] != answers[opaque_id]
                or hashlib.sha256(entry["response_text"].encode()).hexdigest() != join["answer_sha256"]):
            raise ValueError("reviewed answer differs from retained blind source")
        condition, _, _ = _materialize(root, pilot, schedule, join["condition_id"])
        rubric_path = root / f"data/evaluator_only/analysis/{PILOT}/rubrics-v1/{join['condition_id']}-rubric.json"
        rubric = json.loads(rubric_path.read_text())
        response = {"response_id": opaque_id, "method_id": join["method_id"],
                    "condition_id": join["condition_id"], "final_response": entry["response_text"],
                    # The legacy builder copies this field only into its separate key. Remove
                    # the unused placeholder below rather than invent a model configuration.
                    "method_configuration_sha256": None,
                    "atomic_claims": [{"claim_id": item["item_id"], "text": item["claim_text"],
                                       "response_span": item["response_span"], "asserted_abstraction_level": None}
                                      for item in entry["claims"]]}
        packet, key = build_packet(condition, response, rubric, salt, assets)
        key.pop("method_configuration_sha256")
        key.update(answer_sha256=join["answer_sha256"],
                   retained_source_binding={"path": join["source_path"],
                                            "raw_sha256": digest(root / join["source_path"])},
                   paired_episode_analysis_eligible=join["paired_episode_analysis_eligible"],
                   configuration_binding="RETAINED_SOURCE_ENVELOPE_NOT_NEW_MODEL_CONFIGURATION")
        packets.append({"opaque_response_id": opaque_id, "packet": packet})
        joins.append(key)
    if (len(packets) != 114 or sum(len(row["packet"]["forms"][0]["atomic_statements"]) for row in packets) != 1084):
        raise ValueError("support packet bank differs from reviewed 114-answer/1084-atom inventory")
    bundle = {"schema": "crane-evidence-calibration-pilot-support-packet-bundle/v1-development",
              "development_only": True, "response_count": len(packets), "atomic_claim_count": 1084,
              "qualification_disposition": DISPOSITION, "highest_level_qualified": False,
              "raw_rank_endpoint_use_prohibited": True, "pilot_annotation_authorized": False,
              "endpoint_scoring_authorized": False, "p11_authorized": False,
              "records": packets}
    key_bundle = {"schema": "crane-evidence-calibration-pilot-support-key/v1-development",
                  "bundle_sha256": canonical_sha256(bundle), "entries": joins,
                  "deterministic_packaging_key_access": True, "annotation_payload_contains_join_key": False,
                  "join_for_analysis_only_after_all_support_and_adjudication_finalized": True,
                  "endpoint_scoring_authorized": False, "confirmation_independent_n": 0,
                  "replication_independent_n": 0}
    return bundle, key_bundle


def write_once(path: Path, value: dict) -> None:
    raw = canonical_json_bytes(value) + b"\n"
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("refusing to overwrite changed support packet artifacts")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(raw)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    bundle, key = build()
    write_once(ROOT / BUNDLE, bundle)
    write_once(ROOT / KEY, key)
    print(json.dumps({"status": "BLIND_DEVELOPMENT_SUPPORT_PACKETS_BUILT_NO_MODEL_CALL",
                      "responses": bundle["response_count"], "atoms": bundle["atomic_claim_count"],
                      "bundle_raw_sha256": digest(ROOT / BUNDLE),
                      "coordinator_key_written_separately": True}, indent=2))
