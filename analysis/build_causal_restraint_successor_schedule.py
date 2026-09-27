#!/usr/bin/env python3
"""Build disjoint pilot, discovery, and replication schedules for causal restraint."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "crane-causal-restraint-successor-schedule/v1"
V6_PILOT_SPLIT = "command-motion-replication-reserve"
V8_DISCOVERY_SPLIT = "causal-restraint-discovery-reserve"
V8_REPLICATION_SPLIT = "causal-restraint-replication-reserve"
PRIMARY = {
    "persistent_command_motion_discrepancy",
    "measured_response_recovery",
}
QUOTAS = {
    "pilot": {
        "persistent_command_motion_discrepancy": 4,
        "measured_response_recovery": 4,
        "missing_decisive_or_ambiguous_evidence": 1,
        "nominal_false_premise_or_irrelevant_obstacle": 1,
    },
    "discovery": {
        "persistent_command_motion_discrepancy": 12,
        "measured_response_recovery": 12,
        "missing_decisive_or_ambiguous_evidence": 3,
        "nominal_false_premise_or_irrelevant_obstacle": 3,
    },
    "replication": {
        "persistent_command_motion_discrepancy": 12,
        "measured_response_recovery": 12,
        "missing_decisive_or_ambiguous_evidence": 3,
        "nominal_false_premise_or_irrelevant_obstacle": 3,
    },
}


def digest(*parts: str) -> str:
    return hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assign(stage: str, layouts: list[dict[str, Any]], catalog_id: str) -> list[dict[str, Any]]:
    expected_per_geometry = sum(QUOTAS[stage].values())
    result: list[dict[str, Any]] = []
    for geometry in ("connected-detour", "nominal-clear-route"):
        available = [item for item in layouts if item["diagnosticMechanism"] == geometry]
        if len(available) != expected_per_geometry:
            raise ValueError(
                f"{stage} {geometry} inventory changed: "
                f"expected {expected_per_geometry}, got {len(available)}"
            )
        ranked = sorted(
            available, key=lambda item: digest(SCHEMA, stage, geometry, item["id"])
        )
        cursor = 0
        for family, count in QUOTAS[stage].items():
            for item in ranked[cursor : cursor + count]:
                timing_bit = int(digest(SCHEMA, "timing", stage, item["id"])[0], 16) % 2
                hold = 18.0 if timing_bit == 0 else 25.0
                if family == "nominal_false_premise_or_irrelevant_obstacle":
                    hold, release, mask = -1.0, -1.0, "none"
                elif family == "measured_response_recovery":
                    release, mask = hold + 12.0, "none"
                elif family == "missing_decisive_or_ambiguous_evidence":
                    release, mask = -1.0, "remove-delivered-odometry-v1"
                else:
                    release, mask = -1.0, "none"
                result.append(
                    {
                        "catalog_id": catalog_id,
                        "layout_id": item["id"],
                        "layout_seed": int(item["seed"]),
                        "geometry_mechanism": geometry,
                        "family": family,
                        "primary_eligible_family": family in PRIMARY,
                        "mobility_hold_after_s": hold,
                        "mobility_release_after_s": release,
                        "evidence_mask": mask,
                    }
                )
            cursor += count
    result.sort(key=lambda item: digest(SCHEMA, "order", stage, item["layout_id"]))
    prefix = {"pilot": "cr-pilot", "discovery": "cr-conf", "replication": "cr-repl"}[stage]
    for index, item in enumerate(result, start=1):
        item.update(
            {
                "order": index,
                "run_id": f"{prefix}-{index:03d}",
                "cluster_id": f"{prefix}-cluster-{index:03d}",
                "study_stage": stage,
                "ros_domain_id": 30 + index,
                "ros_tcp_port": {
                    "pilot": 12700,
                    "discovery": 12800,
                    "replication": 12900,
                }[stage]
                + index,
            }
        )
    return result


def build(
    v6: dict[str, Any],
    v8: dict[str, Any],
    old_schedule: dict[str, Any],
    hashes: dict[str, str],
) -> dict[str, Any]:
    if v6.get("environmentId") != "crane-land-proving-ground-v6":
        raise ValueError("pilot source must be v6")
    if v8.get("environmentId") != "crane-land-proving-ground-v8":
        raise ValueError("successor source must be v8")
    assigned = {
        run["layout_id"]
        for cohort in old_schedule.get("cohorts", [])
        for run in cohort.get("runs", [])
    }
    pilot_layouts = [
        item
        for item in v6["layouts"]
        if item["studySplit"] == V6_PILOT_SPLIT and item["id"] not in assigned
    ]
    discovery_layouts = [
        item for item in v8["layouts"] if item["studySplit"] == V8_DISCOVERY_SPLIT
    ]
    replication_layouts = [
        item for item in v8["layouts"] if item["studySplit"] == V8_REPLICATION_SPLIT
    ]
    stages = {
        "pilot": assign("pilot", pilot_layouts, "v6"),
        "discovery": assign("discovery", discovery_layouts, "v8"),
        "replication": assign("replication", replication_layouts, "v8"),
    }
    all_layouts = [item["layout_id"] for rows in stages.values() for item in rows]
    if len(all_layouts) != len(set(all_layouts)):
        raise ValueError("successor stages must use disjoint layouts")
    return {
        "schema": SCHEMA,
        "status": "FROZEN_CONFIGURATIONS_BEFORE_SUCCESSOR_CAPTURE_OR_MODEL_OUTPUT",
        "schedule_id": "explicit-causal-restraint-successor-v1",
        "source_hashes": hashes,
        "unit": "one independently configured physical scenario",
        "related_artifacts": "Masks, question variants, generations, and judge passes remain within the physical cluster.",
        "pilot_reallocation": (
            "The 20 v6 layouts were never assigned to the original 100-configuration replication "
            "schedule and had no retained capture or model output. The original protected 100 remain untouched."
        ),
        "stage_counts": {
            stage: {
                "total": len(rows),
                "primary": sum(item["primary_eligible_family"] for item in rows),
                "controls": sum(not item["primary_eligible_family"] for item in rows),
            }
            for stage, rows in stages.items()
        },
        "stages": stages,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v6-catalog", required=True, type=Path)
    parser.add_argument("--v8-catalog", required=True, type=Path)
    parser.add_argument("--old-schedule", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing schedule: {args.output}")
    paths = {
        "v6_catalog": args.v6_catalog.resolve(strict=True),
        "v8_catalog": args.v8_catalog.resolve(strict=True),
        "old_schedule": args.old_schedule.resolve(strict=True),
    }
    result = build(
        json.loads(paths["v6_catalog"].read_text(encoding="utf-8")),
        json.loads(paths["v8_catalog"].read_text(encoding="utf-8")),
        json.loads(paths["old_schedule"].read_text(encoding="utf-8")),
        {key: file_sha256(path) for key, path in paths.items()},
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
