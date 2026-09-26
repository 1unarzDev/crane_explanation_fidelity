#!/usr/bin/env python3
"""Prospective coordinator amendment for outcome-dependent diagnostic eligibility.

The immutable schedule fixes which configurations are collected.  Whether a scheduled primary
family contributes to primary N is instead established by its independent physical reference.
This wrapper preserves the frozen v1 arithmetic while making that distinction auditable and
ending discovery after all scheduled configurations, even when eligible N is below its nominal
maximum.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from focused_sequential_monitor import (
    DEFAULT_LEDGER,
    DEFAULT_PROTOCOL,
    DEFAULT_RESOURCE_FREEZE,
    analyze as analyze_v1,
)


def analyze(payload: dict[str, Any], protocol: dict[str, Any], ledger: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    adjusted = copy.deepcopy(payload)
    primary = set(protocol["families"]["primary"])
    fallback_control = "missing_decisive_or_ambiguous_evidence"
    retained_outcome_insufficient = 0
    for row in adjusted.get("clusters", []):
        if row.get("family") in primary and row.get("primary_endpoint_eligible") is False:
            row["family"] = fallback_control
            retained_outcome_insufficient += 1
    result = analyze_v1(adjusted, protocol, ledger, freeze)
    result["schema"] = "crane-focused-supported-diagnostic-monitor/v2"
    result["eligibility_rule"] = (
        "scheduled controls are ineligible; scheduled primary-family configurations increment "
        "primary N only when the independent reference supports the registered mechanism"
    )
    result["retained_primary_family_configurations_ineligible_by_independent_reference"] = retained_outcome_insufficient
    result["scheduled_configuration_count"] = len(payload.get("clusters", []))
    if (
        len(payload.get("clusters", [])) == sum(protocol["families"]["fixed_discovery_counts"].values())
        and result["status"] == "CONTINUE"
    ):
        result["status"] = "INCONCLUSIVE_FINAL"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--resource-freeze", type=Path, default=DEFAULT_RESOURCE_FREEZE)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing monitor output: {args.output}")
    values = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in (args.input, args.protocol, args.ledger, args.resource_freeze)
    ]
    result = analyze(*values)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
