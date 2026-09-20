#!/usr/bin/env python3
"""Build immutable, robot-visible runtime provenance before a land/Nav2 capture."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROS_PACKAGES = (
    "nav2-msgs",
    "nav2-bt-navigator",
    "nav2-controller",
    "nav2-behaviors",
    "nav2-planner",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(checkout: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ("git", "-C", str(checkout), *arguments), text=True
    ).strip()


def versioned_file(path: Path, checkout: Path, role: str) -> dict[str, Any]:
    path = path.resolve(strict=True)
    checkout = checkout.resolve(strict=True)
    relative = path.relative_to(checkout).as_posix()
    commit = git(checkout, "rev-parse", "HEAD")
    payload = path.read_bytes()
    try:
        committed = subprocess.check_output(
            ("git", "-C", str(checkout), "show", f"{commit}:{relative}")
        )
    except subprocess.CalledProcessError:
        committed = None
    return {
        "role": role,
        "repository_path": relative,
        "repository_commit": commit,
        "content_sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "byte_identical_to_git_object": committed == payload,
    }


def checkout_record(checkout: Path) -> dict[str, Any]:
    return {
        "commit": git(checkout, "rev-parse", "HEAD"),
        "dirty": bool(git(checkout, "status", "--porcelain")),
        "remote": git(checkout, "remote", "get-url", "origin"),
    }


def image_record(image: str) -> dict[str, Any]:
    inspected = json.loads(
        subprocess.check_output(("docker", "image", "inspect", image), text=True)
    )[0]
    return {
        "reference": image,
        "id": inspected["Id"],
        "repo_digests": sorted(inspected.get("RepoDigests") or ()),
    }


def ros_package_versions(image: str) -> dict[str, str]:
    package_names = [f"ros-jazzy-{name}" for name in ROS_PACKAGES]
    query = "dpkg-query -W -f='${Package}\\t${Version}\\n' " + " ".join(package_names)
    output = subprocess.check_output(
        ("docker", "run", "--rm", "--entrypoint", "bash", image, "-lc", query),
        text=True,
    )
    return dict(line.split("\t", 1) for line in output.splitlines())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--crane-checkout", required=True, type=Path)
    parser.add_argument("--astro-checkout", required=True, type=Path)
    parser.add_argument("--nav2-params", required=True, type=Path)
    parser.add_argument("--bt-xml", required=True, type=Path)
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
        versioned_file(args.bt_xml, args.crane_checkout, "behavior_tree_xml"),
        versioned_file(args.nav2_params, args.crane_checkout, "nav2_parameter_file"),
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
            "goal_distance_m": args.goal_distance_m,
            "action_duration_s": args.action_duration_s,
            "command_flag": args.command_flag,
            "lidar_frame": args.lidar_frame,
            "occupied_costmap_required": True,
        },
        "intentionally_excluded_from_robot_visible_manifest": [
            "fault or intervention identity",
            "mobility hold/release timing",
            "simulator evaluator truth",
            "expected terminal outcome",
        ],
        "limitations": [
            "A configured parameter does not prove that it triggered a particular failure.",
            "Package versions and image identity do not prove a source rebuild mapping.",
            "The player checkout is not its binary source unless build_source_commit_proven is true.",
            "No topic identity or timestamp proves controller consumption.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
