#!/usr/bin/env python3
"""Fail closed unless evaluator truth matches the requested land catalog layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_binding(truth: dict[str, Any], catalog: dict[str, Any], *,
                     catalog_sha256: str, catalog_id: str, layout_id: str,
                     expected_mobility_hold_after: float = -1.0,
                     expected_mobility_release_after: float = -1.0) -> dict[str, Any]:
    layouts = [item for item in catalog.get("layouts", []) if item.get("id") == layout_id]
    if len(layouts) != 1:
        raise ValueError(f"requested layout must resolve exactly once: {layout_id}")
    layout = layouts[0]
    expected_environment = f"crane-land-proving-ground-{catalog_id}"
    checks = {
        "truth_schema": truth.get("schema") == "crane-land-proving-ground-truth-v1",
        "environment_id": truth.get("environmentId") == expected_environment,
        "manifest_sha256": str(truth.get("manifestSha256", "")).lower() == catalog_sha256,
        "layout_id": truth.get("layoutId") == layout_id,
        "seed": truth.get("seed") == layout.get("seed"),
        "generator_seed": truth.get("generatorSeed") == layout.get("generatorSeed"),
        "study_split": truth.get("studySplit") == layout.get("studySplit"),
        "diagnostic_mechanism": (
            truth.get("diagnosticMechanism") == layout.get("diagnosticMechanism")
        ),
        "expected_broad_outcome": (
            truth.get("expectedBroadOutcome") == layout.get("expectedBroadOutcome")
        ),
        "relevant_obstacles": (
            truth.get("relevantObstacles") == layout.get("relevantObstacles")
        ),
        "obstacle_semantic_ids": (
            truth.get("obstacleSemanticIds")
            == [item.get("id") for item in layout.get("obstacles", [])]
        ),
        "obstacles_active": (
            truth.get("obstacleActive")
            == [bool(item.get("activeInitially")) for item in layout.get("obstacles", [])]
        ),
        "mobility_hold_configuration": math.isclose(
            float(truth.get("mobilityHoldAfterSeconds", -1.0)),
            expected_mobility_hold_after,
            rel_tol=0.0,
            abs_tol=1e-6,
        ),
        "mobility_release_configuration": math.isclose(
            float(truth.get("mobilityReleaseAfterSeconds", -1.0)),
            expected_mobility_release_after,
            rel_tol=0.0,
            abs_tol=1e-6,
        ),
    }
    failed = sorted(name for name, accepted in checks.items() if not accepted)
    return {
        "schema": "crane-land-scenario-binding-audit/v1",
        "accepted": not failed,
        "catalog_id": catalog_id,
        "catalog_sha256": catalog_sha256,
        "requested_layout_id": layout_id,
        "observed_truth_schema": truth.get("schema"),
        "observed_environment_id": truth.get("environmentId"),
        "observed_layout_id": truth.get("layoutId"),
        "expected_mobility_hold_after_seconds": expected_mobility_hold_after,
        "observed_mobility_hold_after_seconds": truth.get("mobilityHoldAfterSeconds", -1.0),
        "expected_mobility_release_after_seconds": expected_mobility_release_after,
        "observed_mobility_release_after_seconds": truth.get(
            "mobilityReleaseAfterSeconds", -1.0
        ),
        "checks": checks,
        "failed_checks": failed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--truth", required=True, type=Path)
    parser.add_argument("--catalog", required=True, type=Path)
    parser.add_argument("--catalog-id", required=True)
    parser.add_argument("--layout", required=True)
    parser.add_argument("--expected-mobility-hold-after", type=float, default=-1.0)
    parser.add_argument("--expected-mobility-release-after", type=float, default=-1.0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    result = validate_binding(
        truth,
        catalog,
        catalog_sha256=sha256(args.catalog),
        catalog_id=args.catalog_id,
        layout_id=args.layout,
        expected_mobility_hold_after=args.expected_mobility_hold_after,
        expected_mobility_release_after=args.expected_mobility_release_after,
    )
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if not result["accepted"]:
        print(
            "land scenario binding rejected: " + ", ".join(result["failed_checks"]),
            file=__import__("sys").stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
