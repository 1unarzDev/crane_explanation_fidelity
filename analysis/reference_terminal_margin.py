#!/usr/bin/env python3
"""Independent development reference calculation for the RoboBoat terminal-margin family.

This evaluator-side implementation deliberately does not import ``crane_explain.diagnostics`` or
the proposed method's adapter.  It reads only the observation/source fields of a governed
robot-visible export, verifies the pinned Nav2 configuration, and evaluates the positional chain
separately from the stopped-speed state.  It is a development reference computation, not a human
label or a confirmatory gold result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from typing import Any


def config_number(text: str, key: str) -> float:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([0-9]+(?:\.[0-9]+)?)\s*$", text, re.M)
    if not match:
        raise ValueError(f"configuration key not found: {key}")
    return float(match.group(1))


def finite_nonnegative(name: str, value: Any) -> float:
    numeric = float(value)
    if not math.isfinite(numeric) or numeric < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return numeric


def calculate(export: dict[str, Any], config_bytes: bytes) -> dict[str, Any]:
    source = export["source"]
    observed_hash = hashlib.sha256(config_bytes).hexdigest()
    if observed_hash != source["config_sha256"]:
        raise ValueError("pinned configuration hash mismatch")
    config = config_bytes.decode("utf-8")
    observation = export["observation"]
    goal_tolerance = config_number(config, "xy_goal_tolerance")
    stopped_threshold = config_number(config, "trans_stopped_velocity")
    if goal_tolerance != finite_nonnegative(
        "configured_goal_tolerance_m", observation["configured_goal_tolerance_m"]
    ):
        raise ValueError("observation/configuration goal tolerance mismatch")
    if stopped_threshold != finite_nonnegative(
        "configured_stopped_speed_mps", observation["configured_stopped_speed_mps"]
    ):
        raise ValueError("observation/configuration stopped-speed mismatch")

    task_tolerance = finite_nonnegative(
        "task_acceptance_tolerance_m", observation["task_acceptance_tolerance_m"]
    )
    return_error = finite_nonnegative(
        "action_return_error_m", observation["action_return_error_m"]
    )
    settled_error_raw = observation.get("settled_error_m")
    displacement_raw = observation.get("post_result_coast_m")
    speed_raw = observation.get("measured_speed_at_return_mps")
    settled_error = (
        None
        if settled_error_raw is None
        else finite_nonnegative("settled_error_m", settled_error_raw)
    )
    displacement = (
        None
        if displacement_raw is None
        else finite_nonnegative("post_result_coast_m", displacement_raw)
    )
    measured_speed = (
        None
        if speed_raw is None
        else finite_nonnegative("measured_speed_at_return_mps", speed_raw)
    )

    position_margin = task_tolerance - return_error
    error_growth = None if settled_error is None else settled_error - return_error
    positional_chain_supported = (
        str(observation["action_status"]).lower() == "succeeded"
        and return_error <= goal_tolerance
        and settled_error is not None
        and displacement is not None
        and settled_error > task_tolerance
        and error_growth is not None
        and error_growth > position_margin
    )
    stopped_state = (
        "unresolved_missing_measured_speed"
        if measured_speed is None
        else (
            "measured_within_configured_threshold"
            if measured_speed <= stopped_threshold
            else "measured_above_configured_threshold"
        )
    )
    full_terminal_margin_supported = (
        positional_chain_supported and stopped_state == "measured_within_configured_threshold"
    )

    return {
        "schema": "crane-terminal-margin-independent-reference/v1",
        "status": "DEVELOPMENT_REFERENCE_NOT_CONFIRMATORY",
        "episode_id": export["episode_id"],
        "implementation_independence": {
            "imports_proposed_diagnostic_core": False,
            "imports_proposed_adapter": False,
            "human_label": False,
            "note": "Separate arithmetic/code path; still authored within the project and requires reviewer validation before freeze."
        },
        "input_fields_used": [
            "source.config_sha256",
            "observation.action_status",
            "observation.configured_goal_tolerance_m",
            "observation.configured_stopped_speed_mps",
            "observation.task_acceptance_tolerance_m",
            "observation.action_return_error_m",
            "observation.measured_speed_at_return_mps",
            "observation.post_result_coast_m",
            "observation.settled_error_m"
        ],
        "measurements": {
            "goal_tolerance_m": goal_tolerance,
            "stopped_speed_threshold_mps": stopped_threshold,
            "task_tolerance_m": task_tolerance,
            "return_error_m": return_error,
            "measured_speed_at_return_mps": measured_speed,
            "post_result_displacement_m": displacement,
            "settled_error_m": settled_error,
            "position_margin_at_return_m": position_margin,
            "radial_error_growth_m": error_growth
        },
        "reference_findings": {
            "positional_failure_chain_supported": positional_chain_supported,
            "stopped_speed_state": stopped_state,
            "full_terminal_margin_mechanism_supported": full_terminal_margin_supported,
            "physical_source_of_residual_motion": "unresolved"
        },
        "allowed_conclusion": (
            "Observed post-return motion exceeded the remaining positional margin and ended "
            "outside the declared task tolerance."
            if positional_chain_supported
            else "The retained observations do not establish the positional failure chain."
        ),
        "additional_full_mechanism_conclusion": (
            "Independently measured return speed was within the configured stopped threshold."
            if full_terminal_margin_supported
            else None
        ),
        "required_withholding": [
            "The physical source of residual motion is not identified.",
            (
                "Whether the physical platform met the configured stopped-speed threshold is unresolved."
                if measured_speed is None
                else "Delivered observations do not prove every value consumed internally by Nav2."
            )
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_export", type=Path)
    parser.add_argument("--config-repository", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    export = json.loads(args.evidence_export.read_text(encoding="utf-8"))
    source = export["source"]
    config_bytes = subprocess.run(
        ["git", "show", f"{source['config_commit']}:{source['config_path']}"],
        cwd=args.config_repository,
        check=True,
        capture_output=True,
    ).stdout
    result = calculate(export, config_bytes)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
