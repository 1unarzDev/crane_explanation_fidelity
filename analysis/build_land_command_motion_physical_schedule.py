#!/usr/bin/env python3
"""Build the fixed v6 land command--motion physical-cohort schedule."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "crane-land-command-motion-physical-schedule/v1"
CATALOG_SCHEMA = "crane-land-proving-ground-catalog-v1"
QUALIFICATION_LAYOUT = (
    "diagnostic-command-motion-confirmation-reserve-connected-detour-001"
)
MECHANISM_QUOTAS = {
    "connected-detour": {
        "persistent-discrepancy": 18,
        "transient-compensation": 17,
        "ambiguous-missing-odometry": 8,
        "nominal-false-premise": 7,
    },
    "nominal-clear-route": {
        "persistent-discrepancy": 17,
        "transient-compensation": 18,
        "ambiguous-missing-odometry": 7,
        "nominal-false-premise": 8,
    },
}


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def _select(catalog: dict[str, Any], split: str) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for mechanism in MECHANISM_QUOTAS:
        choices = sorted(
            (
                layout
                for layout in catalog["layouts"]
                if layout.get("studySplit") == split
                and layout.get("diagnosticMechanism") == mechanism
                and layout.get("id") != QUALIFICATION_LAYOUT
            ),
            key=lambda item: item["id"],
        )
        if len(choices) < 50:
            raise ValueError(f"{split}/{mechanism} has fewer than 50 eligible layouts")
        groups[mechanism] = choices[:50]
    return groups


def _assign_families(
    cohort: str, groups: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    assigned: list[dict[str, Any]] = []
    for mechanism, layouts in groups.items():
        ranked = sorted(
            layouts,
            key=lambda item: _digest(
                SCHEMA, "family-rank", cohort, mechanism, item["id"]
            ),
        )
        cursor = 0
        for family, count in MECHANISM_QUOTAS[mechanism].items():
            for layout in ranked[cursor : cursor + count]:
                intervention = family != "nominal-false-premise"
                timing_bit = int(
                    _digest(SCHEMA, "timing", cohort, layout["id"])[0], 16
                ) % 2
                hold = float(18 if timing_bit == 0 else 25) if intervention else -1.0
                release = (
                    hold + 12.0 if family == "transient-compensation" else -1.0
                )
                assigned.append(
                    {
                        "layout_id": layout["id"],
                        "layout_seed": int(layout["seed"]),
                        "geometry_mechanism": mechanism,
                        "family": family,
                        "mobility_hold_after_s": hold,
                        "mobility_release_after_s": release,
                        "evidence_mask": (
                            "remove-delivered-odometry-v1"
                            if family == "ambiguous-missing-odometry"
                            else "none"
                        ),
                    }
                )
            cursor += count
        if cursor != len(ranked):
            raise AssertionError("family quotas do not consume exactly 50 layouts")
    return sorted(
        assigned,
        key=lambda item: _digest(
            SCHEMA, "collection-order", cohort, item["layout_id"]
        ),
    )


def _cohort(
    name: str, groups: dict[str, list[dict[str, Any]]]
) -> dict[str, Any]:
    items = _assign_families(name, groups)
    prefix = "cm-land-conf" if name == "confirmation-physical" else "cm-land-repl"
    domain_start = 145 if name == "confirmation-physical" else 45
    port_start = 12345 if name == "confirmation-physical" else 12445
    for index, item in enumerate(items, start=1):
        item["order"] = index
        item["run_id"] = f"{prefix}-{index:03d}"
        item["cluster_id"] = f"{prefix}-cluster-{index:03d}"
        item["ros_domain_id"] = domain_start + (index - 1) % 80
        item["ros_tcp_port"] = port_start + (index - 1) % 100
    return {
        "cohort": name,
        "fixed_cluster_count": len(items),
        "runs": items,
    }


def build(catalog: dict[str, Any], catalog_sha256: str) -> dict[str, Any]:
    if catalog.get("schema") != CATALOG_SCHEMA:
        raise ValueError("unsupported proving-ground catalog schema")
    if catalog.get("environmentId") != "crane-land-proving-ground-v6":
        raise ValueError("schedule requires the v6 proving-ground catalog")
    confirmation = _select(catalog, "command-motion-confirmation-reserve")
    replication = _select(catalog, "command-motion-replication-reserve")
    result = {
        "schema": SCHEMA,
        "status": "FROZEN_PHYSICAL_SCHEDULE_SEMANTIC_CAMPAIGN_INACTIVE",
        "catalog_sha256": catalog_sha256,
        "qualification_layout_excluded": QUALIFICATION_LAYOUT,
        "cohorts": [
            _cohort("confirmation-physical", confirmation),
            _cohort("replication-reserve", replication),
        ],
    }
    ids = [
        run["layout_id"]
        for cohort in result["cohorts"]
        for run in cohort["runs"]
    ]
    if len(ids) != len(set(ids)):
        raise AssertionError("confirmation and replication layouts are not disjoint")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing schedule: {args.output}")
    catalog_bytes = args.catalog.read_bytes()
    catalog = json.loads(catalog_bytes)
    result = build(catalog, hashlib.sha256(catalog_bytes).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
