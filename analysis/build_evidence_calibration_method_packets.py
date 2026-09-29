#!/usr/bin/env python3
"""Build auditable B0--B4 method packets from one robot-visible condition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_calibration_io import canonical_json_bytes, canonical_sha256


SCHEMA = "crane-evidence-calibration-method-packet-set/v1"
BUILDER_ID = "evidence-calibration-method-packet-builder"
BUILDER_VERSION = "v1-development"
FORBIDDEN_FRAGMENTS = ("evaluator", "gold", "intervention_identity", "physical_truth")


def _closed(value: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing, unknown = required - set(value), set(value) - required - optional
    if missing or unknown:
        raise ValueError(f"{label} has missing or unknown fields")


def _scan(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = key.lower().replace("-", "_")
            if any(fragment in normalized for fragment in FORBIDDEN_FRAGMENTS):
                raise ValueError(f"evaluator-only key prohibited at {path}.{key}")
            _scan(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan(item, f"{path}[{index}]")


def _assets(items: list[dict[str, Any]], label: str) -> list[dict[str, Any]]:
    result, identifiers = [], set()
    for item in items:
        _closed(item, {"asset_id", "version", "sha256"}, set(), label)
        if item["asset_id"] in identifiers or len(item["sha256"]) != 64:
            raise ValueError(f"{label} identities or hashes are invalid")
        identifiers.add(item["asset_id"])
        result.append(dict(item))
    return result


def build(condition_entry: dict[str, Any], execution_contract: dict[str, Any]) -> dict[str, Any]:
    _closed(condition_entry, {"condition", "method_packet"}, set(), "condition entry")
    condition, evidence = condition_entry["condition"], condition_entry["method_packet"]
    if condition["method_packet_sha256"] != canonical_sha256(evidence):
        raise ValueError("condition method packet hash mismatch")
    if not condition.get("evaluator_only_absent") or condition.get("visibility") != "robot_visible":
        raise ValueError("condition is not certified robot-visible")
    _scan(evidence)
    _closed(execution_contract,
            {"contract_id", "ordinary_runtime_presentation", "presentation_evidence_ids",
             "source_assets", "primitive_tools", "question_instruction", "contract_assets"},
            set(), "execution contract")
    if set(execution_contract["presentation_evidence_ids"]) != set(condition["available_evidence_ids"]):
        raise ValueError("ordinary presentation must account for the same evidence inventory")
    if not execution_contract["ordinary_runtime_presentation"].strip():
        raise ValueError("ordinary runtime presentation cannot be empty")
    source_assets = _assets(execution_contract["source_assets"], "source asset")
    primitive_tools = _assets(execution_contract["primitive_tools"], "primitive tool")
    contract_assets = _assets(execution_contract["contract_assets"], "contract asset")
    _scan(execution_contract)
    basis = {
        "episode_id": condition["episode_id"], "configuration_id": condition["configuration_id"],
        "condition_id": condition["condition_id"],
        "method_packet_sha256": condition["method_packet_sha256"],
        "available_evidence_ids": condition["available_evidence_ids"],
        "source_configuration_sha256": condition["source_configuration_sha256"],
        "runtime_manifest_sha256": condition["runtime_manifest_sha256"],
    }
    evidence_basis_sha = canonical_sha256(basis)
    source_sha = canonical_sha256(source_assets)
    tools_sha = canonical_sha256(primitive_tools)
    question = execution_contract["question_instruction"]
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question instruction cannot be empty")

    packets = []
    specifications = {
        "B0": ("RAW_SUMMARY", False, False, False),
        "B1": ("STRUCTURED_EVIDENCE", False, False, False),
        "B2": ("TOOL_ENABLED_AGENT", True, True, False),
        "B3": ("DIAGNOSTIC_CONTRACT_UNVERIFIED", True, True, False),
        "B4": ("FULL_EVIDENCE_CALIBRATED", True, True, True),
    }
    for method_id, (method_class, has_source, has_tools, verifies) in specifications.items():
        packet: dict[str, Any] = {
            "schema": "crane-evidence-calibration-method-packet/v1",
            "method_id": method_id, "method_class": method_class,
            "episode_id": condition["episode_id"], "condition_id": condition["condition_id"],
            "question_instruction": question, "evidence_basis_sha256": evidence_basis_sha,
            "method_packet_sha256": condition["method_packet_sha256"],
            "available_evidence_ids": condition["available_evidence_ids"],
            "presentation": execution_contract["ordinary_runtime_presentation"] if method_id == "B0" else evidence,
            "source_assets": source_assets if has_source else [],
            "primitive_tools": primitive_tools if has_tools else [],
            "contract_assets": contract_assets if method_id in {"B3", "B4"} else [],
            "final_claim_verification": verifies,
            "physical_sample_increment": 0,
        }
        packet["packet_sha256"] = canonical_sha256(packet)
        packets.append(packet)

    by_id = {item["method_id"]: item for item in packets}
    for method_id in ("B2", "B3", "B4"):
        packet = by_id[method_id]
        if canonical_sha256(packet["source_assets"]) != source_sha or \
                canonical_sha256(packet["primitive_tools"]) != tools_sha or \
                packet["evidence_basis_sha256"] != evidence_basis_sha:
            raise AssertionError("B2--B4 parity invariant failed")
    return {
        "schema": SCHEMA, "builder_id": BUILDER_ID, "builder_version": BUILDER_VERSION,
        "execution_contract_id": execution_contract["contract_id"],
        "episode_id": condition["episode_id"], "condition_id": condition["condition_id"],
        "evidence_basis_sha256": evidence_basis_sha,
        "b2_b4_source_assets_sha256": source_sha,
        "b2_b4_primitive_tools_sha256": tools_sha,
        "independent_episode_increment": 1,
        "method_packets": packets,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition-entry", type=Path, required=True)
    parser.add_argument("--execution-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = build(json.loads(args.condition_entry.read_text()),
                   json.loads(args.execution_contract.read_text()))
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
