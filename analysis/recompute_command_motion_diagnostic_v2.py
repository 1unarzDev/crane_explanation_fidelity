#!/usr/bin/env python3
"""Recompute command-motion diagnosis while preserving optional config provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recompute_command_motion_diagnostic import (
    build_result as build_result_v1,
    method_input_from_export,
)


def build_result(payload: dict[str, Any]) -> dict[str, Any]:
    result = build_result_v1(payload)
    config_hash = payload.get("source", {}).get("diagnostic_config_sha256")
    if config_hash is None:
        result["schema"] = "crane-command-motion-recomputed-diagnostic-v2"
        return result
    if not isinstance(config_hash, str) or len(config_hash) != 64:
        raise ValueError("diagnostic configuration SHA-256 must be 64 hexadecimal characters")
    try:
        int(config_hash, 16)
    except ValueError as exc:
        raise ValueError("diagnostic configuration SHA-256 is not hexadecimal") from exc

    evidence_id = f"diagnostic-config-sha256:{config_hash}"
    diagnostic = result["diagnostic_result"]
    for measurement in diagnostic["measurements"]:
        identifiers = measurement["evidence_ids"]
        if evidence_id not in identifiers:
            identifiers.append(evidence_id)
    if evidence_id not in diagnostic["supporting_evidence"]:
        diagnostic["supporting_evidence"].append(evidence_id)
    result["schema"] = "crane-command-motion-recomputed-diagnostic-v2"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    if payload.get("schema") == "crane-command-motion-diagnostic-export-v1":
        payload = method_input_from_export(payload)
    result = build_result(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
