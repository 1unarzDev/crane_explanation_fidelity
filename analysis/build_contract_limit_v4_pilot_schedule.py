#!/usr/bin/env python3
"""Freeze the bounded, two-contract development schedule for P-contract v4."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "crane-contract-limit-v4-pilot-schedule/v1"
MASKS = (
    "remove-delivered-odometry-v1",
    "remove-delivered-command-v1",
)


def _digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode()).hexdigest()


def build(catalog: dict[str, Any], catalog_sha256: str) -> dict[str, Any]:
    if catalog.get("environmentId") != "crane-land-proving-ground-v7":
        raise ValueError("v4 pilot requires the v7 development catalog")
    layouts = list(catalog.get("layouts") or ())
    if len(layouts) != 16 or any(
        item.get("studySplit") != "contract-limit-v4-development" for item in layouts
    ):
        raise ValueError("v7 development inventory changed")
    runs: list[dict[str, Any]] = []
    by_mechanism = {
        mechanism: sorted(
            (item for item in layouts if item["diagnosticMechanism"] == mechanism),
            key=lambda item: _digest(SCHEMA, "rank", mechanism, item["id"]),
        )
        for mechanism in ("connected-detour", "nominal-clear-route")
    }
    for mechanism, values in by_mechanism.items():
        if len(values) != 8:
            raise ValueError("pilot requires eight layouts per geometry stratum")
        assignments = [
            (MASKS[0], 18.0, -1.0, "masked-persistent"),
            (MASKS[0], 25.0, -1.0, "masked-persistent"),
            (MASKS[0], 18.0, 30.0, "masked-recovery"),
            (MASKS[1], 18.0, -1.0, "masked-persistent"),
            (MASKS[1], 25.0, -1.0, "masked-persistent"),
            (MASKS[1], 25.0, 37.0, "masked-recovery"),
            ("none", 18.0, 30.0, "fully-evidenced-control"),
            ("none", -1.0, -1.0, "nominal-control"),
        ]
        for layout, (mask, hold, release, role) in zip(values, assignments, strict=True):
            runs.append({
                "layout_id": layout["id"],
                "layout_seed": int(layout["seed"]),
                "geometry_mechanism": mechanism,
                "evidence_mask": mask,
                "mobility_hold_after_s": hold,
                "mobility_release_after_s": release,
                "study_role": role,
                "primary_endpoint_eligible": mask in MASKS,
            })
    runs.sort(key=lambda item: _digest(SCHEMA, "order", item["layout_id"]))
    for index, item in enumerate(runs, start=1):
        item.update({
            "order": index,
            "run_id": f"cc-v4-pilot-{index:03d}",
            "cluster_id": f"cc-v4-pilot-cluster-{index:03d}",
            "ros_domain_id": 40 + index,
            "ros_tcp_port": 12700 + index,
        })
    return {
        "schema": SCHEMA,
        "status": "FROZEN_DEVELOPMENT_BEFORE_CAPTURE",
        "pilot_id": "contract-limit-v4-fresh-development-pilot",
        "catalog_sha256": catalog_sha256,
        "candidate": "p-contract-v4-development",
        "baseline": "r-contract-v1-development",
        "primary_claim_population": (
            "independent configurations with one prospectively declared decisive command/motion stream absent"
        ),
        "evidence_deficiency_contracts": list(MASKS),
        "primary_count": sum(item["primary_endpoint_eligible"] for item in runs),
        "control_count": sum(not item["primary_endpoint_eligible"] for item in runs),
        "confirmation_alpha_consumed": 0.0,
        "runs": runs,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing schedule: {args.output}")
    raw = args.catalog.resolve(strict=True).read_bytes()
    result = build(json.loads(raw), hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
