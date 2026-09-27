#!/usr/bin/env python3
"""Extend P-contract v3 to two prospectively declared missing-stream contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from compose_contract_complete_answer_v3 import compile_answer as compile_v3


VERSION = "p-contract-v4-development"
FAMILY = "missing_decisive_or_ambiguous_evidence"


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


def _measurements(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in document.get("diagnostic_result", {}).get("measurements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }


def compile_answer(
    document: dict[str, Any], *, family: str, source_sha256: str,
    question_registry: dict[str, Any],
) -> dict[str, Any]:
    """Return v3 unchanged except when the declared missing stream is command delivery."""
    result = compile_v3(
        document,
        family=family,
        source_sha256=source_sha256,
        question_registry=question_registry,
    )
    result["candidate_version"] = VERSION
    result["parent_candidate_version"] = "p-contract-v3-development"
    result["bounded_repair"] = {
        "family": FAMILY,
        "components": ["M", "Q", "L"],
        "scope": "distinguish missing delivered-command from missing measured-motion evidence",
        "evidence_deficiency_contracts": [
            "missing-measured-motion-v1",
            "missing-delivered-command-v1",
        ],
    }
    if family != FAMILY:
        return result

    measurements = _measurements(document)
    commands = measurements.get("delivered_command_sample_count")
    odometry = measurements.get("independent_odometry_sample_count")
    if commands is None or odometry is None:
        raise ValueError("missing-stream contract lacks stream-count measurements")
    command_count = commands.get("value")
    odometry_count = odometry.get("value")
    if not isinstance(command_count, int) or isinstance(command_count, bool):
        raise ValueError("delivered command count is not an integer")
    if not isinstance(odometry_count, int) or isinstance(odometry_count, bool):
        raise ValueError("independent odometry count is not an integer")
    if command_count > 0 and odometry_count == 0:
        result["missing_stream_contract"] = "missing-measured-motion-v1"
        return result
    if command_count != 0 or odometry_count <= 0:
        raise ValueError("missing-stream contract requires exactly one retained decisive stream")

    by_code = {item["component"]: item for item in result["components"]}
    by_code["M"]["text"] = (
        "A command-to-measured-motion mechanism cannot be established from the retained evidence."
    )
    by_code["Q"]["text"] = (
        f"The record contains {command_count} delivered command samples and {odometry_count} "
        "independent odometry samples; delivered command is the decisive missing discriminator."
    )
    by_code["L"]["text"] = (
        "Without the missing delivered-command stream, measured motion and the recorded execution "
        "sequence cannot establish a requested-to-delivered-to-measured response chain, actuator "
        "acceptance, or a unique physical cause."
    )
    result["missing_stream_contract"] = "missing-delivered-command-v1"
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
