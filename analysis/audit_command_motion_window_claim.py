#!/usr/bin/env python3
"""Independently audit one half-open command/motion window asserted in an answer."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def audit(export: dict[str, Any], start: float, end: float) -> dict[str, Any]:
    if export.get("schema") != "crane-command-motion-diagnostic-export-v1":
        raise ValueError("unsupported export schema")
    if not start < end:
        raise ValueError("window must have positive duration")
    method = export["method_input"]
    config = method["windowing"]
    commands = [
        float(item["planar_speed_mps"]) for item in method.get("command_samples", [])
        if start <= float(item["offset_s"]) < end
    ]
    odometry = [
        float(item["planar_speed_mps"]) for item in method.get("odometry_samples", [])
        if start <= float(item["offset_s"]) < end
    ]
    command_median = statistics.median(commands) if commands else None
    motion_median = statistics.median(odometry) if odometry else None
    return {
        "schema": "crane-command-motion-window-claim-audit/v1",
        "episode_id": export["episode_id"],
        "implementation_independence": {
            "imports_proposed_diagnostic_core": False,
            "imports_proposed_exporter": False,
            "calculation": "direct half-open filtering and Python statistics.median",
        },
        "interval_s": [start, end],
        "command_sample_count": len(commands),
        "odometry_sample_count": len(odometry),
        "median_commanded_planar_speed_mps": command_median,
        "median_measured_planar_speed_mps": motion_median,
        "qualifying_command_motion_window": (
            len(commands) >= int(config["minimum_command_samples_per_window"])
            and len(odometry) >= int(config["minimum_odometry_samples_per_window"])
            and command_median is not None
            and command_median >= float(config["minimum_commanded_speed_mps"])
        ),
        "declared_thresholds": config,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    parser.add_argument("--start", required=True, type=float)
    parser.add_argument("--end", required=True, type=float)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.export.read_text(encoding="utf-8")), args.start, args.end)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
