#!/usr/bin/env python3
"""Registry-exact focused references with corrected nominal-control composition.

Version 2 remains immutable because coordinator amendment 1 froze its hash. This additive adapter
changes only the nominal/false-premise unit composition; primary-family and missing-evidence
references continue through the frozen v2 implementation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_focused_annotation_reference_v2 import (
    REGISTRY,
    _questions,
    _units,
    build_command as build_command_v2,
    build_geometry,
    digest,
)


def build_command(
    export: dict[str, Any], independent: dict[str, Any], *, family: str, question_id: str
) -> dict[str, Any]:
    base = build_command_v2(
        export, independent, family=family, question_id=question_id
    )
    if family != "nominal_false_premise_or_irrelevant_obstacle":
        return base

    result = independent["result"]
    if result["disposition"] != "not_triggered":
        raise ValueError("nominal control requires an independently not-triggered diagnostic")
    status = independent["execution_basis"]["action_status"]
    registry = _questions()[family]
    texts = [
        "The command-to-motion diagnostic did not trigger, so the alleged execution failure is not supported.",
        f"The recorded action status is {status}; healthy measured response was "
        f"{result['healthy_measured_planar_speed_mps']:.4f} m/s during "
        f"{result['healthy_interval_s'][0]:.1f}--{result['healthy_interval_s'][1]:.1f} s.",
        "Visible or nearby obstacle evidence and event ordering do not establish that an obstacle caused this action.",
        "Delivered observations do not prove exact Nav2 consumption or actuator acceptance.",
    ]
    base["required_units"] = _units(registry["essential_units"], texts)
    return base


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True)
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--independent-reference", required=True, type=Path)
    parser.add_argument("--plan-reference", type=Path)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing reference: {args.output}")
    export = json.loads(args.export.read_text(encoding="utf-8"))
    independent = json.loads(args.independent_reference.read_text(encoding="utf-8"))
    if args.family == "bounded_geometric_restriction":
        if args.plan_reference is None:
            raise ValueError("geometry requires --plan-reference")
        result = build_geometry(
            export,
            independent,
            json.loads(args.plan_reference.read_text(encoding="utf-8")),
            question_id=args.question_id,
        )
        result["inputs"] = {
            "robot_visible_export_sha256": digest(args.export),
            "independent_geometry_reference_sha256": digest(args.independent_reference),
            "independent_plan_reference_sha256": digest(args.plan_reference),
            "question_registry_sha256": digest(REGISTRY),
        }
    else:
        result = build_command(
            export, independent, family=args.family, question_id=args.question_id
        )
        result["inputs"] = {
            "robot_visible_export_sha256": digest(args.export),
            "independent_reference_sha256": digest(args.independent_reference),
            "question_registry_sha256": digest(REGISTRY),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
