#!/usr/bin/env python3
"""Build deterministic, removal-only nested evidence conditions.

The input is a normalized method packet with top-level ``episode_id``, ``configuration_id``,
and an ``evidence`` object keyed by public evidence role. Every condition is derived from the
same source packet; a mask may delete values but never rewrite or add evidence.
"""

from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from evidence_calibration import CONDITION_SCHEMA, EvidenceCondition, validate_evidence_condition
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


MASK_SPEC_SCHEMA = "crane-nested-evidence-mask-spec/v1"
FORBIDDEN_KEYS = {
    "evaluator_only", "physical_truth", "intervention_identity", "gold",
    "gold_claims", "reference_answer", "supported_claims", "highest_defensible_diagnosis",
}


def _decode_pointer(pointer: str) -> list[str]:
    if not pointer.startswith("/") or pointer == "/":
        raise ValueError(f"invalid JSON pointer: {pointer}")
    return [token.replace("~1", "/").replace("~0", "~") for token in pointer[1:].split("/")]


def _remove_pointer(value: dict[str, Any], pointer: str) -> None:
    tokens = _decode_pointer(pointer)
    if not tokens or tokens[0] != "evidence":
        raise ValueError("masks may remove only /evidence/... paths")
    parent: Any = value
    for token in tokens[:-1]:
        if isinstance(parent, dict) and token in parent:
            parent = parent[token]
        elif isinstance(parent, list) and token.isdigit() and int(token) < len(parent):
            parent = parent[int(token)]
        else:
            raise ValueError(f"mask pointer does not exist in the source packet: {pointer}")
    final = tokens[-1]
    if isinstance(parent, dict) and final in parent:
        del parent[final]
    elif isinstance(parent, list) and final.isdigit() and int(final) < len(parent):
        del parent[int(final)]
    else:
        raise ValueError(f"mask pointer does not exist in the source packet: {pointer}")


def _walk_forbidden(value: Any, path: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise ValueError(f"evaluator-only field is prohibited in method packet: {path}/{key}")
            _walk_forbidden(child, f"{path}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden(child, f"{path}/{index}")


def _evidence_ids(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "evidence_id" and isinstance(child, str) and child:
                found.add(child)
            elif key == "evidence_ids" and isinstance(child, list):
                if any(not isinstance(item, str) or not item for item in child):
                    raise ValueError("evidence_ids must contain non-empty strings")
                found.update(child)
            else:
                found.update(_evidence_ids(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_evidence_ids(child))
    return found


def _validate_source(source: dict[str, Any]) -> None:
    if set(source) - {"schema", "episode_id", "configuration_id", "evidence", "question"}:
        raise ValueError("normalized method packet has undeclared top-level fields")
    if not isinstance(source.get("episode_id"), str) or not source["episode_id"]:
        raise ValueError("method packet needs an episode_id")
    if not isinstance(source.get("configuration_id"), str) or not source["configuration_id"]:
        raise ValueError("method packet needs a configuration_id")
    evidence = source.get("evidence")
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError("method packet needs a non-empty evidence object")
    if any(not isinstance(role, str) or not role for role in evidence):
        raise ValueError("evidence role names must be non-empty strings")
    _walk_forbidden(source)


def _validate_spec(spec: dict[str, Any]) -> None:
    required = {
        "schema", "ladder_id", "condition_builder_id", "condition_builder_version",
        "condition_builder_sha256", "source_configuration_sha256", "runtime_manifest_sha256",
        "conditions",
    }
    if set(spec) != required or spec.get("schema") != MASK_SPEC_SCHEMA:
        raise ValueError("invalid or non-closed nested evidence mask specification")
    conditions = spec["conditions"]
    if not isinstance(conditions, list) or not conditions:
        raise ValueError("mask specification needs conditions")
    expected_levels = list(range(len(conditions)))
    if [item.get("level_index") for item in conditions] != expected_levels:
        raise ValueError("conditions must be ordered at contiguous levels E0..Ek")
    ids = [item.get("condition_id") for item in conditions]
    if any(not isinstance(item, str) or not item for item in ids) or len(ids) != len(set(ids)):
        raise ValueError("condition IDs are missing or duplicated")
    previous_removed: set[str] | None = None
    for index, item in enumerate(conditions):
        if set(item) != {"condition_id", "level_index", "removed_json_pointers", "mask_id", "mask_version"}:
            raise ValueError("condition specification contains missing or unknown fields")
        pointers = item["removed_json_pointers"]
        if not isinstance(pointers, list) or len(pointers) != len(set(pointers)):
            raise ValueError("removed JSON pointers must be a unique list")
        decoded = [tuple(_decode_pointer(pointer)) for pointer in pointers]
        if any(not tokens or tokens[0] != "evidence" for tokens in decoded):
            raise ValueError("masks may remove only /evidence/... paths")
        if any(left != right and left == right[:len(left)] for left in decoded for right in decoded):
            raise ValueError("one mask pointer may not contain another")
        removed = set(pointers)
        if previous_removed is not None and not removed.issubset(previous_removed):
            raise ValueError("stronger evidence conditions may only restore evidence")
        previous_removed = removed
        if index < len(conditions) - 1 and (not item["mask_id"] or not item["mask_version"]):
            raise ValueError("masked conditions need mask id and version")
        if index == len(conditions) - 1 and (removed or item["mask_id"] is not None or item["mask_version"] is not None):
            raise ValueError("the strongest condition must be the unmasked source")


def build_conditions(source: dict[str, Any], spec: dict[str, Any]) -> list[dict[str, Any]]:
    _validate_source(source)
    _validate_spec(spec)
    source_sha256 = canonical_sha256(source)
    results: list[dict[str, Any]] = []
    for item in spec["conditions"]:
        packet = copy.deepcopy(source)
        for pointer in sorted(item["removed_json_pointers"], key=lambda value: (-value.count("/"), value)):
            _remove_pointer(packet, pointer)
        _walk_forbidden(packet)
        condition_mask = None if not item["removed_json_pointers"] else {
            "mask_id": item["mask_id"], "mask_version": item["mask_version"],
            "removed_json_pointers": sorted(item["removed_json_pointers"]),
        }
        condition = EvidenceCondition(
            schema=CONDITION_SCHEMA,
            episode_id=source["episode_id"], configuration_id=source["configuration_id"],
            condition_id=item["condition_id"], ladder_id=spec["ladder_id"],
            level_index=item["level_index"],
            parent_condition_id=None if item["level_index"] == 0 else spec["conditions"][item["level_index"] - 1]["condition_id"],
            source_packet_sha256=source_sha256, method_packet_sha256=canonical_sha256(packet),
            source_configuration_sha256=spec["source_configuration_sha256"],
            runtime_manifest_sha256=spec["runtime_manifest_sha256"],
            condition_builder_id=spec["condition_builder_id"],
            condition_builder_version=spec["condition_builder_version"],
            condition_builder_sha256=spec["condition_builder_sha256"],
            mask_id=None if condition_mask is None else item["mask_id"],
            mask_version=None if condition_mask is None else item["mask_version"],
            mask_sha256=None if condition_mask is None else canonical_sha256(condition_mask),
            available_evidence_ids=tuple(sorted(_evidence_ids(packet["evidence"]))),
            available_evidence_roles=tuple(sorted(packet["evidence"])),
            removed_json_pointers=tuple(sorted(item["removed_json_pointers"])),
        )
        validate_evidence_condition(condition)
        results.append({"condition": asdict(condition), "method_packet": packet})
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--mask-spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    spec = json.loads(args.mask_spec.read_text(encoding="utf-8"))
    output = {"schema": "crane-nested-evidence-condition-bundle/v1", "conditions": build_conditions(source, spec)}
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
