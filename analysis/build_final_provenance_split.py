#!/usr/bin/env python3
"""Build the frozen opaque 60-instance provenance-study schedule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")

    widths = (3.75, 4.0, 4.25, 4.5, 4.75, 5.0)
    goals = (3.25, 3.5, 3.75, 4.0, 4.25)
    hold_times = (14.5, 15.0, 15.5, 16.0, 16.5)
    instances = []
    for index in range(60):
        family = "recovery_followed_by_success" if index % 2 == 0 else "terminal_recovery_abort"
        hold = hold_times[(index // 2) % len(hold_times)]
        instances.append(
            {
                "opaque_episode_id": f"pn-{index + 1:04d}",
                "collection_order": index + 1,
                "scenario_family": family,
                "seed_base": 3001 + index,
                "corridor_width_m": widths[index % len(widths)],
                "corridor_length_m": 22.0,
                "goal_distance_m": goals[(index // 2) % len(goals)],
                "mobility_hold_after_fixed_simulation_s": hold,
                "mobility_release_after_fixed_simulation_s": (
                    hold + 12.0 if family == "recovery_followed_by_success" else None
                ),
                "ros_domain_id": 100 + index,
                "ros_tcp_port": 10100 + index,
            }
        )
    payload = {
        "schema": "crane-provenance-final-split/v1",
        "status": "FROZEN_BEFORE_COLLECTION",
        "split": "sealed_test",
        "minimum_included_episodes": 40,
        "target_included_episodes": 50,
        "preferred_included_episodes": 60,
        "stopping_rule": (
            "Run in collection_order. Stop at 50 included episodes; use later entries only to "
            "replace predeclared capture-quality exclusions or to reach 60 if compute and the "
            "September 28 deadline permit. Never stop based on model outputs or labels."
        ),
        "question_kinds": ["recovery-mechanism", "failure-cause"],
        "instances": instances,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
