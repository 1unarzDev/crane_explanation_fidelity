#!/usr/bin/env python3
"""Mask odometry for one independently configured ambiguity cluster."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from recompute_command_motion_diagnostic import build_result, method_input_from_export


MASK_ID = "remove-delivered-odometry-v1"


def build_masked_export(source: dict[str, Any], episode_id: str) -> dict[str, Any]:
    method_payload = copy.deepcopy(method_input_from_export(source))
    method_payload["episode_id"] = episode_id
    method_payload["method_input"]["odometry_samples"] = []
    checked = build_result(method_payload)
    if checked["diagnostic_result"]["disposition"] != "insufficient":
        raise RuntimeError("independent-cluster odometry mask did not produce insufficiency")

    boundary = copy.deepcopy(method_payload["evidence_boundary"])
    limitations = list(boundary.get("limitations") or ())
    limitations.append(
        "Delivered odometry samples are unavailable in this evidence condition, so a "
        "time-aligned command-to-motion comparison cannot be computed."
    )
    boundary["limitations"] = list(dict.fromkeys(limitations))
    return {
        "schema": "crane-command-motion-diagnostic-export-v1",
        "episode_id": episode_id,
        "visibility": "robot_visible",
        "source": method_payload["source"],
        "method_input": method_payload["method_input"],
        "evidence_boundary": boundary,
        "evidence_mask": {
            "mask_id": MASK_ID,
            "withheld": ["delivered odometry samples"],
            "paired_unmasked_export_available_to_methods": False,
            "role": "sole method-visible export for an independently configured ambiguity cluster",
            "independent_scenario_increment": 1,
        },
        "diagnostic_result": checked["diagnostic_result"],
        "final_answer": checked["final_answer"],
        "final_text_verification": checked["final_text_verification"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--episode-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    result = build_masked_export(
        json.loads(args.source.read_text(encoding="utf-8")), args.episode_id
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
