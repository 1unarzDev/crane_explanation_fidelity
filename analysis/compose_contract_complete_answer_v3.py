#!/usr/bin/env python3
"""Apply the bounded missing-evidence limitation repair to P-contract v2."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from compose_contract_complete_answer import compile_answer as compile_v2


VERSION = "p-contract-v3-development"
MISSING_EVIDENCE_LIMIT = (
    "Without the missing measured-motion stream, command delivery and the recorded execution "
    "sequence cannot establish a command-to-motion discrepancy, actuator acceptance, or a "
    "unique physical cause."
)


def _render(components: list[dict[str, Any]]) -> str:
    titles = {
        "M": "Supported mechanism",
        "Q": "Decisive comparison",
        "O": "Recorded outcome",
        "L": "Necessary limitation",
    }
    return "\n\n".join(
        f"{titles[item['component']]} ({item['component']}):\n{item['text']}"
        for item in components
    )


def compile_answer(
    document: dict[str, Any], *, family: str, source_sha256: str,
    question_registry: dict[str, Any],
) -> dict[str, Any]:
    """Return v2 unchanged except for the demonstrated missing-evidence L omission."""
    result = compile_v2(
        document,
        family=family,
        source_sha256=source_sha256,
        question_registry=question_registry,
    )
    parent_version = result.get("candidate_version")
    result["candidate_version"] = VERSION
    result["parent_candidate_version"] = parent_version
    result["bounded_repair"] = {
        "family": "missing_decisive_or_ambiguous_evidence",
        "component": "L",
        "basis": "replicated omission in cc-pilot-014 and cc-pilot-017",
    }
    if family == "missing_decisive_or_ambiguous_evidence":
        limitations = [item for item in result["components"] if item["component"] == "L"]
        if len(limitations) != 1:
            raise ValueError("missing-evidence answer lacks one atomic L component")
        limitations[0]["text"] = MISSING_EVIDENCE_LIMIT
        result["final_answer"] = _render(result["components"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--family", required=True)
    parser.add_argument("--question-registry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    raw = args.evidence.resolve(strict=True).read_bytes()
    result = compile_answer(
        json.loads(raw),
        family=args.family,
        source_sha256=hashlib.sha256(raw).hexdigest(),
        question_registry=json.loads(args.question_registry.resolve(strict=True).read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
