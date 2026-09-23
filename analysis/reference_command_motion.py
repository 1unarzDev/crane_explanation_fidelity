#!/usr/bin/env python3
"""Independent reference computation for a command-to-motion diagnostic export.

This evaluator-side implementation imports neither the proposed diagnostic core nor its exporter.
It rebuilds fixed windows from the method-visible samples and independently applies the declared
development thresholds.  It does not infer an intervention or unique physical cause.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


def calculate(export: dict[str, Any]) -> dict[str, Any]:
    if export.get("schema") != "crane-command-motion-diagnostic-export-v1":
        raise ValueError("unsupported command-motion export schema")
    if export.get("visibility") != "robot_visible":
        raise ValueError("reference input is not declared robot-visible")
    method = export["method_input"]
    config = method["windowing"]
    window_seconds = float(config["window_seconds"])
    duration = float(method["analysis_duration_s"])
    count = max(0, math.ceil(duration / window_seconds))
    commands = method.get("command_samples") or []
    odometry = method.get("odometry_samples") or []
    windows = []
    for index in range(count):
        start = index * window_seconds
        end = start + window_seconds
        command_values = [
            float(item["planar_speed_mps"])
            for item in commands
            if start <= float(item["offset_s"]) < end
        ]
        odometry_values = [
            float(item["planar_speed_mps"])
            for item in odometry
            if start <= float(item["offset_s"]) < end
        ]
        windows.append(
            {
                "index": index,
                "start_offset_s": start,
                "end_offset_s": end,
                "command_sample_count": len(command_values),
                "odometry_sample_count": len(odometry_values),
                "median_commanded_planar_speed_mps": (
                    statistics.median(command_values) if command_values else None
                ),
                "median_measured_planar_speed_mps": (
                    statistics.median(odometry_values) if odometry_values else None
                ),
            }
        )

    eligible = [
        window
        for window in windows
        if window["command_sample_count"]
        >= int(config["minimum_command_samples_per_window"])
        and window["odometry_sample_count"]
        >= int(config["minimum_odometry_samples_per_window"])
        and window["median_commanded_planar_speed_mps"] is not None
        and window["median_measured_planar_speed_mps"] is not None
        and window["median_commanded_planar_speed_mps"]
        >= float(config["minimum_commanded_speed_mps"])
    ]
    calibration_count = int(config["calibration_window_count"])
    calibration = eligible[:calibration_count]
    disposition = "insufficient"
    healthy_speed = None
    healthy_command = None
    selected_run = []
    recovery_window = None
    if len(calibration) == calibration_count:
        healthy_speed = statistics.median(
            window["median_measured_planar_speed_mps"] for window in calibration
        )
        healthy_command = statistics.median(
            window["median_commanded_planar_speed_mps"] for window in calibration
        )
        if healthy_speed >= float(config["minimum_healthy_measured_speed_mps"]):
            candidates = {
                window["index"]: window
                for window in eligible
                if window["index"] > calibration[-1]["index"]
                and window["median_measured_planar_speed_mps"] / healthy_speed
                <= float(config["maximum_discrepancy_response_ratio"])
            }
            runs = []
            current = []
            for index in sorted(candidates):
                if current and index != current[-1]["index"] + 1:
                    runs.append(current)
                    current = []
                current.append(candidates[index])
            if current:
                runs.append(current)
            runs = [
                run
                for run in runs
                if len(run) >= int(config["minimum_consecutive_discrepancy_windows"])
            ]
            if runs:
                # Independently mirror the declared earliest-onset selection rule.  A longer
                # post-recovery segment must not move the diagnosed onset after the failures.
                selected_run = sorted(runs, key=lambda run: run[0]["index"])[0]
                disposition = "supported"
                recovery_window = next(
                    (
                        window
                        for window in eligible
                        if window["index"] > selected_run[-1]["index"]
                        and window["median_measured_planar_speed_mps"]
                        >= float(config["minimum_healthy_measured_speed_mps"])
                        and window["median_measured_planar_speed_mps"] / healthy_speed
                        > float(config["maximum_discrepancy_response_ratio"])
                    ),
                    None,
                )
            else:
                disposition = "not_triggered"

    discrepancy_command = (
        statistics.median(
            window["median_commanded_planar_speed_mps"] for window in selected_run
        )
        if selected_run
        else None
    )
    discrepancy_motion = (
        statistics.median(
            window["median_measured_planar_speed_mps"] for window in selected_run
        )
        if selected_run
        else None
    )
    recovered_motion = (
        recovery_window["median_measured_planar_speed_mps"]
        if recovery_window is not None
        else None
    )
    sequence = method["execution_sequence"]
    return {
        "schema": "crane-command-motion-independent-reference/v1",
        "status": "DEVELOPMENT_REFERENCE_NOT_CONFIRMATORY",
        "episode_id": export["episode_id"],
        "implementation_independence": {
            "imports_proposed_diagnostic_core": False,
            "imports_proposed_exporter": False,
            "human_label": False,
            "window_algorithm": "independent_fixed_half_open_wall_time_windows",
        },
        "sample_counts": {
            "command": len(commands),
            "odometry": len(odometry),
        },
        "result": {
            "disposition": disposition,
            "healthy_commanded_planar_speed_mps": healthy_command,
            "healthy_measured_planar_speed_mps": healthy_speed,
            "discrepancy_commanded_planar_speed_mps": discrepancy_command,
            "discrepancy_measured_planar_speed_mps": discrepancy_motion,
            "response_ratio": (
                discrepancy_motion / healthy_speed
                if discrepancy_motion is not None and healthy_speed
                else None
            ),
            "interval_s": (
                [selected_run[0]["start_offset_s"], selected_run[-1]["end_offset_s"]]
                if selected_run
                else None
            ),
            "recovered_measured_planar_speed_mps": recovered_motion,
            "recovered_response_ratio": (
                recovered_motion / healthy_speed
                if recovered_motion is not None and healthy_speed
                else None
            ),
            "response_recovery_interval_s": (
                [recovery_window["start_offset_s"], recovery_window["end_offset_s"]]
                if recovery_window is not None
                else None
            ),
            "follow_path_failure_count": int(sequence["follow_path_failure_count"]),
            "follow_path_attempt_count": int(sequence["follow_path_attempt_count"]),
            "source_qualified_wait_recovery_count": int(
                sequence["source_qualified_wait_recovery_count"]
            ),
        },
        "allowed_conclusion": (
            (
                "A sustained delivered-command/measured-motion discrepancy is supported, and a later command-active window shows that measured response recovered; its unique physical cause is unresolved."
                if recovery_window is not None
                else "A sustained delivered-command/measured-motion discrepancy is supported; its unique physical cause is unresolved."
            )
            if disposition == "supported"
            else "No supported command-to-motion diagnosis is established by this computation."
        ),
        "prohibited_conclusions": [
            "the command was accepted by an actuator",
            "Nav2 consumed the delivered odometry",
            "motor failure, slip, collision, or obstruction was the unique cause",
            "the evaluator intervention identity",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("export", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = calculate(json.loads(args.export.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
