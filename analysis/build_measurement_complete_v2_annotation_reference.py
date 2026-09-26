#!/usr/bin/env python3
"""Bind checked-composition references to the measurement-complete-v2 question namespace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_checked_composition_annotation_reference import (
    build_reference as build_base_reference,
    load_inventory,
)


def build_reference(
    screen_case: dict[str, Any], reference_case: dict[str, Any]
) -> dict[str, Any]:
    result = build_base_reference(screen_case, reference_case)
    expected = f"checked-composition:{screen_case['case_id']}"
    if result.get("question_id") != expected:
        raise ValueError("base reference question identity changed unexpectedly")
    result["question_id"] = f"measurement-complete-v2:{screen_case['case_id']}"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    inventory = load_inventory(args.inventory)
    cases = {item["case_id"]: item for item in contract["cases"]}
    references = {item["case_id"]: item for item in inventory["cases"]}
    if args.case_id not in cases or args.case_id not in references:
        raise ValueError("case is absent from the frozen treatment or reference inventory")
    result = build_reference(cases[args.case_id], references[args.case_id])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
