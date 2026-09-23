#!/usr/bin/env python3
"""Build robot-visible provenance for the additive diagnostic land capture path."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_runtime_manifest import (
    checkout_record,
    image_record,
    ros_package_versions,
    versioned_file,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--umbrella-checkout", required=True, type=Path)
    parser.add_argument("--crane-checkout", required=True, type=Path)
    parser.add_argument("--astro-checkout", required=True, type=Path)
    parser.add_argument("--nav2-params", required=True, type=Path)
    parser.add_argument("--bt-xml", required=True, type=Path)
    parser.add_argument("--environment-catalog", required=True, type=Path)
    parser.add_argument("--player-provenance", required=True, type=Path)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--nav2-profile", required=True)
    parser.add_argument("--goal-distance-m", required=True, type=float)
    parser.add_argument("--action-duration-s", required=True, type=float)
    parser.add_argument("--command-flag", required=True)
    parser.add_argument("--lidar-frame", required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing runtime manifest: {args.output}")

    player_provenance = json.loads(args.player_provenance.read_text(encoding="utf-8"))
    artifacts = [
        versioned_file(
            args.umbrella_checkout / "scripts/run_diagnostic_land_capture.sh",
            args.umbrella_checkout,
            "capture_orchestrator",
        ),
        versioned_file(
            args.umbrella_checkout / "scripts/build_diagnostic_runtime_manifest.py",
            args.umbrella_checkout,
            "runtime_manifest_builder",
        ),
        versioned_file(
            args.umbrella_checkout / "scripts/build_runtime_manifest.py",
            args.umbrella_checkout,
            "runtime_manifest_helper",
        ),
        versioned_file(args.bt_xml, args.crane_checkout, "behavior_tree_xml"),
        versioned_file(args.nav2_params, args.crane_checkout, "nav2_parameter_file"),
        versioned_file(
            args.environment_catalog,
            args.crane_checkout,
            "environment_catalog",
        ),
        versioned_file(
            args.crane_checkout
            / "Tools/Performance/run_land_proving_ground_nav2_fixture.sh",
            args.crane_checkout,
            "proving_ground_fixture_entrypoint",
        ),
        versioned_file(
            args.crane_checkout / "Tools/Performance/run_land_nav2_fixture.sh",
            args.crane_checkout,
            "land_fixture_entrypoint",
        ),
        versioned_file(
            args.crane_checkout / "Tools/Performance/run_nav2_controller_fixture.sh",
            args.crane_checkout,
            "nav2_fixture_entrypoint",
        ),
    ]
    payload = {
        "schema": "crane-runtime-provenance/v1",
        "run_id": args.run_id,
        "container_image": image_record(args.image),
        "ros_packages": ros_package_versions(args.image),
        "checkouts": {
            "explanation_fidelity": checkout_record(args.umbrella_checkout),
            "crane_ml": checkout_record(args.crane_checkout),
            "astro_dock": checkout_record(args.astro_checkout),
        },
        "artifacts": artifacts,
        "player": {
            "sha256": player_provenance["player"]["sha256"],
            "bytes": player_provenance["player"]["bytes"],
            "managed_assemblies_sha256": player_provenance["managed_assemblies"]["sha256"],
            "physics_assembly_sha256": player_provenance["managed_assemblies"][
                "physics_assembly_sha256"
            ],
            "build_manifest_sha256": player_provenance["build_manifest"]["sha256"],
            "build_source_commit": player_provenance["build_source_commit"],
            "build_source_commit_proven": player_provenance["build_source_commit_proven"],
            "provenance_limit": player_provenance["provenance_limit"],
        },
        "launch_contract": {
            "scene": args.scene,
            "platform": args.platform,
            "graphics_mode": "batchmode_nographics",
            "nav2_profile": args.nav2_profile,
            "nav2_parameter_artifact_role": "nav2_parameter_file",
            "behavior_tree_artifact_role": "behavior_tree_xml",
            "environment_catalog_artifact_role": "environment_catalog",
            "goal_distance_m": args.goal_distance_m,
            "action_duration_s": args.action_duration_s,
            "command_flag": args.command_flag,
            "lidar_frame": args.lidar_frame,
            "occupied_costmap_required": True,
        },
        "intentionally_excluded_from_robot_visible_manifest": [
            "selected environment layout and evaluator mechanism label",
            "fault or intervention identity",
            "simulator evaluator truth",
            "expected terminal outcome",
        ],
        "limitations": [
            "The environment-catalog hash identifies source but does not disclose the selected layout.",
            "A configured parameter does not prove that it triggered a particular behavior.",
            "The player checkout is not its binary source unless build_source_commit_proven is true.",
            "No topic identity or timestamp proves controller consumption.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
