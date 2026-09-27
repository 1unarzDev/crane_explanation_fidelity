#!/usr/bin/env python3
"""Freeze the untouched suffix of the prior v6 reserve for the v2 development pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "crane-contract-complete-v2-pilot-schedule/v1"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(source: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    rows = source.get("stages", {}).get("pilot")
    if not isinstance(rows, list) or len(rows) != 20:
        raise ValueError("source pilot must contain exactly twenty configurations")
    if rows[0].get("run_id") != "cr-pilot-001":
        raise ValueError("expected inspected canary is not first in the source schedule")
    retained = rows[1:]
    if [row.get("order") for row in retained] != list(range(2, 21)):
        raise ValueError("source pilot suffix is not in exact frozen order")
    if len({row.get("layout_id") for row in retained}) != 19:
        raise ValueError("pilot configurations are not independent by layout")
    primary = sum(row.get("primary_eligible_family") is True for row in retained)
    controls = sum(row.get("primary_eligible_family") is False for row in retained)
    if (primary, controls) != (15, 4):
        raise ValueError("unexpected pilot primary/control composition")
    return {
        "schema": SCHEMA,
        "schedule_id": "contract-complete-diagnostic-communication-v2-development-pilot",
        "status": "FROZEN_BEFORE_REMAINING_PHYSICAL_OR_MODEL_OUTPUTS",
        "recorded_date": "2026-09-27",
        "source_schedule_sha256": source_sha256,
        "inspected_excluded_configuration": {
            "run_id": rows[0]["run_id"],
            "cluster_id": rows[0]["cluster_id"],
            "reason": "physical outcome and P/R semantic tie already inspected",
        },
        "unit": "one independently configured physical scenario",
        "counts": {"total": 19, "primary": primary, "controls": controls},
        "claims": ["A_complete_supported_MQOL", "B_substantive_assertion_reliability"],
        "alpha": 0.0,
        "confirmation_activation": "PROHIBITED",
        "configurations": retained,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    source_path = args.source.resolve(strict=True)
    result = build(json.loads(source_path.read_text()), source_sha256=digest(source_path))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
