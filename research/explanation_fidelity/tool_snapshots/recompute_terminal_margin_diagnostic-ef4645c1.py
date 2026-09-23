#!/usr/bin/env python3
"""Recompute the bounded terminal-margin diagnosis from robot-visible observations.

This is the narrow executable adapter supplied to both the proposed diagnostic method and the
tool-enabled repository-agent baseline.  It accepts no evaluator-only labels or simulator force
state.  The exact configuration file is hash-checked and its two relevant thresholds must match
the retained observation before the core diagnostic is called.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CORE_SRC = ROOT / "packages" / "astro_dock" / "src" / "crane_explain" / "src"
sys.path.insert(0, str(CORE_SRC))

from crane_explain.diagnostics import (  # noqa: E402
    GoalTerminationObservation,
    diagnose_terminal_stopping_margin,
    render_diagnostic,
    verify_diagnostic_text,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def config_value(config_text: str, key: str) -> float:
    match = re.search(rf"^\s*{re.escape(key)}:\s*([0-9]+(?:\.[0-9]+)?)\s*$", config_text, re.M)
    if not match:
        raise ValueError(f"configuration key not found: {key}")
    return float(match.group(1))


def build_result(method_input: dict[str, Any], config_path: Path) -> dict[str, Any]:
    if method_input.get("schema") != "crane-terminal-margin-method-input-v1":
        raise ValueError("unsupported method-input schema")
    if method_input.get("visibility") != "robot_visible":
        raise ValueError("method input is not declared robot-visible")
    prohibited = {"diagnostic_result", "checked_answer", "final_text_verification"}
    leaked = sorted(prohibited.intersection(method_input))
    if leaked:
        raise ValueError(f"method input contains derived answer fields: {leaked}")

    source = method_input["source"]
    expected_hash = source["config_sha256"]
    actual_hash = sha256(config_path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"configuration hash mismatch: expected {expected_hash}, observed {actual_hash}"
        )
    config_text = config_path.read_text(encoding="utf-8")
    observation = method_input["observation"]
    configured_goal_tolerance = config_value(config_text, "xy_goal_tolerance")
    configured_stopped_speed = config_value(config_text, "trans_stopped_velocity")
    if configured_goal_tolerance != observation["configured_goal_tolerance_m"]:
        raise ValueError("retained goal tolerance does not match the pinned configuration")
    if configured_stopped_speed != observation["configured_stopped_speed_mps"]:
        raise ValueError("retained stopped-speed threshold does not match the pinned configuration")

    retained = GoalTerminationObservation(
        episode_id=observation["episode_id"],
        evidence_ids=tuple(observation["evidence_ids"]),
        frame=observation["frame"],
        action_status=observation["action_status"],
        configured_goal_tolerance_m=observation["configured_goal_tolerance_m"],
        configured_stopped_speed_mps=observation["configured_stopped_speed_mps"],
        task_acceptance_tolerance_m=observation["task_acceptance_tolerance_m"],
        action_return_error_m=observation["action_return_error_m"],
        measured_speed_at_return_mps=observation.get("measured_speed_at_return_mps"),
        post_result_coast_m=observation.get("post_result_coast_m"),
        settled_error_m=observation.get("settled_error_m"),
        action_return_timestamp_s=observation["action_return_timestamp_s"],
        settled_timestamp_s=observation["settled_timestamp_s"],
        source_anchor_ids=tuple(observation["source_anchor_ids"]),
    )
    result = diagnose_terminal_stopping_margin(retained)
    answer = render_diagnostic(result)
    verification = verify_diagnostic_text(result, answer)
    return {
        "schema": "crane-terminal-margin-recomputation-v1",
        "episode_id": retained.episode_id,
        "source": source,
        "diagnostic_result": result.to_dict(),
        "checked_answer": answer,
        "final_text_verification": {
            "accepted": verification.accepted,
            "method": "exact-deterministic-render-v1",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("method_input", type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = build_result(
        json.loads(args.method_input.read_text(encoding="utf-8")), args.config
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
