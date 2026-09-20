#!/usr/bin/env python3
"""Run one opaque sealed episode from the frozen split and pre-data amendment."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode_id")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    split = json.loads(
        (root / "research/explanation_fidelity/dataset_splits/provenance-final-v1.json").read_text()
    )
    amendment = json.loads(
        (root / "research/explanation_fidelity/experiment_configs/frozen/provenance-study-v1-amendment-1.json").read_text()
    )
    matches = [item for item in split["instances"] if item["opaque_episode_id"] == args.episode_id]
    if len(matches) != 1:
        raise SystemExit(f"unknown or duplicate frozen episode ID: {args.episode_id}")
    instance = matches[0]
    constants = amendment["launch_constants"]
    environment = os.environ.copy()
    environment.update(
        {
            "CRANE_DATA_SPLIT": "final",
            "CRANE_SEED_BASE": str(instance["seed_base"]),
            "CRANE_SCENE": constants["scene"],
            "CRANE_NAV2_COMMAND_FLAG": constants["command_flag"],
            "CRANE_NAV2_LIDAR_FRAME": constants["lidar_frame"],
            "CRANE_NAV2_GOAL_DISTANCE": str(instance["goal_distance_m"]),
            "CRANE_NAV2_ACTION_DURATION": str(constants["action_duration_s"]),
            "CRANE_FIXTURE_DELAY": str(constants["fixture_delay_s"]),
            "CRANE_DURATION": str(constants["worker_duration_s"]),
            "CRANE_TIME_SCALE": str(constants["time_scale"]),
            "CRANE_EXPECT_NAV_STATUS": (
                "succeeded"
                if instance["scenario_family"] == "recovery_followed_by_success"
                else "aborted"
            ),
        }
    )
    unity_arguments = [
        "--crane-land-corridor-width",
        str(instance["corridor_width_m"]),
        "--crane-land-corridor-length",
        str(instance["corridor_length_m"]),
        "--crane-land-blocker",
        "none",
        "--crane-land-mobility-hold-after",
        str(instance["mobility_hold_after_fixed_simulation_s"]),
    ]
    release = instance["mobility_release_after_fixed_simulation_s"]
    if release is not None:
        unity_arguments.extend(("--crane-land-mobility-release-after", str(release)))
    environment["CRANE_NAV2_UNITY_EXTRA_ARGS"] = " ".join(unity_arguments)
    subprocess.run(
        (
            str(root / "scripts/run_land_capture.sh"),
            args.episode_id,
            str(instance["ros_domain_id"]),
            str(instance["ros_tcp_port"]),
        ),
        cwd=root,
        env=environment,
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
