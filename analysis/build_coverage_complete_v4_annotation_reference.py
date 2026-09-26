#!/usr/bin/env python3
"""Bind an independently checked reference to the coverage-complete-v4 namespace.

The frozen transport inherited a legacy question namespace inside its in-memory reference hash.
This builder changes only that transport identifier after verifying the original canonical hash;
it does not alter evidence, required units, prohibited claims, or response content.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_checked_composition_annotation_reference import build_reference, load_inventory
from run_measurement_complete_v2_development import sha256_json


ROOT = Path(__file__).resolve().parents[1]


def _index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    result = {item["case_id"]: item for item in items}
    if len(result) != len(items):
        raise ValueError("duplicate case IDs")
    return result


def build(contract: dict[str, Any], result: dict[str, Any], case_id: str) -> dict[str, Any]:
    cases = _index(contract.get("cases", []))
    if case_id not in cases or result.get("case_id") != case_id:
        raise ValueError("contract/result case mismatch")
    inventory = load_inventory(ROOT / contract["reference_inventory"])
    reference_cases = _index(inventory.get("cases", []))
    if set(cases) != set(reference_cases):
        raise ValueError("contract and reference inventories differ")

    reference = build_reference(cases[case_id], reference_cases[case_id])
    inherited_id = reference["question_id"]
    inherited_hash = sha256_json(reference)
    declared_hash = result.get("inputs", {}).get("annotation_reference_sha256")
    if inherited_hash != declared_hash:
        raise ValueError("result is not bound to the inherited independently checked reference")

    corrected_id = f"coverage-complete-v4:{case_id}"
    if result.get("question_id") != corrected_id:
        raise ValueError("result has an unexpected v4 question namespace")
    reference["question_id"] = corrected_id
    reference["transport_binding_correction"] = {
        "amendment": (
            "research/explanation_fidelity/experiment_configs/development/"
            "coverage-complete-v4-language-screen-v1-amendment-1.json"
        ),
        "field_changed": "question_id",
        "inherited_question_id": inherited_id,
        "inherited_canonical_reference_sha256": inherited_hash,
        "corrected_question_id": corrected_id,
        "scientific_content_changed": False,
    }
    return reference


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    reference = build(contract, result, args.case_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(reference, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
