#!/usr/bin/env python3
"""Build the fixed fresh development-pilot schedule for P-contract/R-contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "crane-contract-complete-pilot-schedule/v1"
CATALOG_SCHEMA = "crane-land-proving-ground-catalog-v1"
QUALIFICATION_LAYOUT = (
    "diagnostic-command-motion-confirmation-reserve-connected-detour-001"
)
FAMILY_QUOTAS = {
    "connected-detour": {
        "persistent_command_motion_discrepancy": 4,
        "measured_response_recovery": 3,
        "missing_decisive_or_ambiguous_evidence": 1,
        "nominal_false_premise_or_irrelevant_obstacle": 1,
    },
    "nominal-clear-route": {
        "persistent_command_motion_discrepancy": 4,
        "measured_response_recovery": 4,
        "missing_decisive_or_ambiguous_evidence": 1,
        "nominal_false_premise_or_irrelevant_obstacle": 1,
    },
}


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def build(
    catalog: dict[str, Any], closed_schedule: dict[str, Any], catalog_sha256: str
) -> dict[str, Any]:
    if catalog.get("schema") != CATALOG_SCHEMA:
        raise ValueError("unsupported proving-ground catalog schema")
    if catalog.get("environmentId") != "crane-land-proving-ground-v6":
        raise ValueError("pilot requires the v6 proving-ground catalog")
    if closed_schedule.get("schema") != "crane-land-command-motion-physical-schedule/v1":
        raise ValueError("closed physical schedule schema mismatch")

    assigned = {
        run["layout_id"]
        for cohort in closed_schedule.get("cohorts", [])
        for run in cohort.get("runs", [])
    }
    pilot: list[dict[str, Any]] = []
    for mechanism, quotas in FAMILY_QUOTAS.items():
        available = [
            item
            for item in catalog["layouts"]
            if item.get("studySplit") == "command-motion-confirmation-reserve"
            and item.get("diagnosticMechanism") == mechanism
            and item["id"] not in assigned
            and item["id"] != QUALIFICATION_LAYOUT
        ]
        expected = sum(quotas.values())
        if len(available) != expected:
            raise ValueError(
                f"fresh {mechanism} inventory changed: expected {expected}, got {len(available)}"
            )
        ranked = sorted(
            available,
            key=lambda item: _digest(SCHEMA, "family-rank", mechanism, item["id"]),
        )
        cursor = 0
        for family, count in quotas.items():
            for layout in ranked[cursor : cursor + count]:
                intervention = family != "nominal_false_premise_or_irrelevant_obstacle"
                timing_bit = int(_digest(SCHEMA, "timing", layout["id"])[0], 16) % 2
                hold = float(18 if timing_bit == 0 else 25) if intervention else -1.0
                release = hold + 12.0 if family == "measured_response_recovery" else -1.0
                pilot.append(
                    {
                        "layout_id": layout["id"],
                        "layout_seed": int(layout["seed"]),
                        "geometry_mechanism": mechanism,
                        "family": family,
                        "mobility_hold_after_s": hold,
                        "mobility_release_after_s": release,
                        "evidence_mask": (
                            "remove-delivered-odometry-v1"
                            if family == "missing_decisive_or_ambiguous_evidence"
                            else "none"
                        ),
                        "study_role": "fresh-development-pilot",
                    }
                )
            cursor += count

    pilot.sort(key=lambda item: _digest(SCHEMA, "collection-order", item["layout_id"]))
    for index, item in enumerate(pilot, start=1):
        item.update(
            {
                "order": index,
                "run_id": f"cc-pilot-{index:03d}",
                "cluster_id": f"cc-pilot-cluster-{index:03d}",
                "ros_domain_id": 10 + index,
                "ros_tcp_port": 12600 + index,
            }
        )

    primary = {
        "persistent_command_motion_discrepancy",
        "measured_response_recovery",
    }
    return {
        "schema": SCHEMA,
        "status": "FROZEN_DEVELOPMENT_PILOT_BEFORE_CAPTURE",
        "pilot_id": "contract-complete-diagnostic-communication-v1-fresh-pilot",
        "catalog_sha256": catalog_sha256,
        "closed_schedule_sha256": hashlib.sha256(
            json.dumps(
                closed_schedule, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8")
        ).hexdigest(),
        "qualification_layout_excluded": QUALIFICATION_LAYOUT,
        "primary_diagnosable_count": sum(item["family"] in primary for item in pilot),
        "control_count": sum(item["family"] not in primary for item in pilot),
        "geometry_secondary_count": 0,
        "confirmation_alpha_consumed": 0.0,
        "runs": pilot,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--closed-schedule", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing pilot schedule: {args.output}")
    catalog_bytes = args.catalog.resolve(strict=True).read_bytes()
    result = build(
        json.loads(catalog_bytes),
        json.loads(args.closed_schedule.resolve(strict=True).read_text(encoding="utf-8")),
        hashlib.sha256(catalog_bytes).hexdigest(),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
