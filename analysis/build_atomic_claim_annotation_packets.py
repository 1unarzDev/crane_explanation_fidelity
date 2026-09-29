#!/usr/bin/env python3
"""Build two independent blinded atomic-claim forms and a separate join key."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from evidence_calibration_io import canonical_json_bytes, canonical_sha256


PACKET_SCHEMA = "crane-blinded-atomic-annotation-packet-set/v1"
KEY_SCHEMA = "crane-blinded-atomic-annotation-key/v1"
BUILDER_ID = "blinded-atomic-claim-annotation-builder"
BUILDER_VERSION = "v1-development"
LABELS = [
    "SUPPORTED_BY_VISIBLE_EVIDENCE",
    "CONTRADICTED_BY_VISIBLE_EVIDENCE",
    "INSUFFICIENT_VISIBLE_EVIDENCE",
    "PHYSICALLY_TRUE_BUT_UNSUPPORTED",
    "UNINTERPRETABLE",
]
PROHIBITED_PACKET_KEYS = ("method_id", "claim_id", "intervention", "gold", "reference_answer")


def _closed(value: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    if required - set(value) or set(value) - required - optional:
        raise ValueError(f"{label} has missing or unknown fields")


def _opaque(salt: str, *parts: str) -> str:
    return hashlib.sha256("\x1f".join((salt, *parts)).encode()).hexdigest()[:24]


def _scan_packet(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower().replace("-", "_")
            if any(token in normalized for token in PROHIBITED_PACKET_KEYS):
                raise ValueError(f"blinding violation at {path}.{key}")
            _scan_packet(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_packet(item, f"{path}[{index}]")


def build(condition_entry: dict[str, Any], response: dict[str, Any], rubric: dict[str, Any],
          blinding_salt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if len(blinding_salt) < 16:
        raise ValueError("blinding salt must contain at least 16 characters")
    _closed(condition_entry, {"condition", "method_packet"}, set(), "condition entry")
    condition, evidence = condition_entry["condition"], condition_entry["method_packet"]
    if condition["method_packet_sha256"] != canonical_sha256(evidence):
        raise ValueError("condition packet hash mismatch")
    _closed(response, {"response_id", "method_id", "condition_id", "final_response",
                       "atomic_claims", "method_configuration_sha256"}, set(), "response")
    if response["condition_id"] != condition["condition_id"]:
        raise ValueError("response condition mismatch")
    if not response["final_response"].strip() or not response["atomic_claims"]:
        raise ValueError("response and atomic claims cannot be empty")
    _closed(rubric, {"rubric_id", "question_text", "required_unit_prompts",
                     "abstraction_level_options", "limitation_prompts", "false_premise_applicable",
                     "sanitized_physical_facts"}, set(), "rubric")
    if any("intervention" in key.lower() for fact in rubric["sanitized_physical_facts"] for key in fact):
        raise ValueError("intervention identity cannot enter the blinded physical-fact view")

    packet_id = "ap-" + _opaque(blinding_salt, response["response_id"], rubric["rubric_id"])
    claim_items, key_items = [], []
    seen_claims = set()
    for index, claim in enumerate(response["atomic_claims"]):
        _closed(claim, {"claim_id", "text", "response_span", "asserted_abstraction_level"},
                {"support_references"}, "atomic claim")
        if claim["claim_id"] in seen_claims or not claim["text"].strip():
            raise ValueError("atomic claims must be unique and nonempty")
        seen_claims.add(claim["claim_id"])
        item_id = "ci-" + _opaque(blinding_salt, response["response_id"], str(index), claim["claim_id"])
        claim_items.append({
            "item_id": item_id, "statement": claim["text"], "response_span": claim["response_span"],
            "asserted_abstraction_level": claim["asserted_abstraction_level"],
            "visible_support_references": claim.get("support_references", []),
            "label": None, "annotation_notes": None,
        })
        key_items.append({"item_id": item_id, "claim_id": claim["claim_id"], "source_index": index})

    base = {
        "packet_id": packet_id, "rubric_id": rubric["rubric_id"],
        "question_text": rubric["question_text"], "robot_visible_evidence": evidence,
        "sanitized_physical_facts": rubric["sanitized_physical_facts"],
        "atomic_statements": claim_items, "allowed_claim_labels": LABELS,
        "required_unit_coverage": [
            {"unit_prompt": item, "communicated": None, "response_span": None}
            for item in rubric["required_unit_prompts"]
        ],
        "highest_asserted_abstraction_level": None,
        "abstraction_level_options": rubric["abstraction_level_options"],
        "limitation_preservation": [
            {"limitation_prompt": item, "preserved": None, "response_span": None}
            for item in rubric["limitation_prompts"]
        ],
        "false_premise_handling": None if rubric["false_premise_applicable"] else "NOT_APPLICABLE",
        "annotator_attestation": None,
    }
    forms = []
    for slot in ("A", "B"):
        form = {"form_id": f"{packet_id}-{slot}", "annotator_slot": slot, **base}
        forms.append(form)
    packet_set = {
        "schema": PACKET_SCHEMA, "builder_id": BUILDER_ID, "builder_version": BUILDER_VERSION,
        "packet_count": 2, "independent_annotator_count_required": 2,
        "automated_judge_role": "SECONDARY_SENSITIVITY_ONLY", "forms": forms,
    }
    _scan_packet(packet_set)
    key = {
        "schema": KEY_SCHEMA, "builder_id": BUILDER_ID, "builder_version": BUILDER_VERSION,
        "packet_set_sha256": canonical_sha256(packet_set), "packet_id": packet_id,
        "response_id": response["response_id"], "method_id": response["method_id"],
        "method_configuration_sha256": response["method_configuration_sha256"],
        "episode_id": condition["episode_id"], "configuration_id": condition["configuration_id"],
        "condition_id": condition["condition_id"], "claim_items": key_items,
        "join_after_adjudication": True,
    }
    return packet_set, key


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition-entry", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--rubric", type=Path, required=True)
    parser.add_argument("--blinding-salt-file", type=Path, required=True)
    parser.add_argument("--packet-output", type=Path, required=True)
    parser.add_argument("--key-output", type=Path, required=True)
    args = parser.parse_args()
    packets, key = build(
        json.loads(args.condition_entry.read_text()), json.loads(args.response.read_text()),
        json.loads(args.rubric.read_text()), args.blinding_salt_file.read_text().strip(),
    )
    args.packet_output.write_bytes(canonical_json_bytes(packets) + b"\n")
    args.key_output.write_bytes(canonical_json_bytes(key) + b"\n")


if __name__ == "__main__":
    main()
