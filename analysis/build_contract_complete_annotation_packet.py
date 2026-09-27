#!/usr/bin/env python3
"""Decorate one contract-complete P/R pair for the blinded packet builder."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def decorate_pair(
    pair: dict[str, Any], reference: dict[str, Any], *, question_id: str
) -> dict[str, Any]:
    if pair.get("schema") != "crane-contract-complete-response-pair/v1":
        raise ValueError("unexpected contract-complete response-pair schema")
    if pair.get("status") != "DEVELOPMENT_ONLY_NOT_CONFIRMATORY":
        raise ValueError("contract pair is not a retained development pair")
    if pair.get("episode_id") != reference.get("episode_id"):
        raise ValueError("contract pair/reference episode mismatch")
    source_conditions = [item.get("condition") for item in pair.get("outputs", [])]
    if source_conditions != ["P-contract", "R-contract"]:
        raise ValueError("contract pair must preserve exact P-contract/R-contract order")
    condition_map = {"P-contract": "P", "R-contract": "R"}
    result = copy.deepcopy(pair)
    result["outputs"] = [
        {**item, "condition": condition_map[item["condition"]]}
        for item in pair["outputs"]
    ]
    result.update(
        {
            "question_id": question_id,
            "question_kind": pair["family"],
            "provider": "mixed-deterministic-and-contract-baseline",
            "model": "condition-specific",
            "permitted_evidence_identifiers": reference["allowed_evidence_identifiers"],
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing decorated pair: {args.output}")
    result = decorate_pair(
        json.loads(args.pair.resolve(strict=True).read_text()),
        json.loads(args.reference.resolve(strict=True).read_text()),
        question_id=args.question_id,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
