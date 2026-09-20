#!/usr/bin/env python3
"""Validate one predeclared runtime-provenance capture without evaluator truth."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def git_blob(checkout: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ("git", "-C", str(checkout), "show", f"{commit}:{path}")
    )


def forbidden_keys(value: Any, prefix: str = "") -> list[str]:
    forbidden = ("fault", "intervention", "mobility_hold", "mobility_release", "expected_outcome")
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            location = f"{prefix}.{key}" if prefix else key
            normalized = key.lower().replace("-", "_")
            if any(term in normalized for term in forbidden):
                findings.append(location)
            findings.extend(forbidden_keys(item, location))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(forbidden_keys(item, f"{prefix}[{index}]"))
    return findings


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--predeclaration", required=True, type=Path)
    parser.add_argument("--parity-audit", required=True, type=Path)
    parser.add_argument("--umbrella-checkout", required=True, type=Path)
    parser.add_argument("--astro-checkout", required=True, type=Path)
    parser.add_argument("--crane-checkout", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")

    capture_manifest_path = args.capture_dir / "manifest.json"
    runtime_manifest_path = args.capture_dir / "runtime_manifest.json"
    capture_manifest = json.loads(capture_manifest_path.read_text(encoding="utf-8"))
    runtime_payload = runtime_manifest_path.read_bytes()
    runtime = json.loads(runtime_payload)
    predeclaration = json.loads(args.predeclaration.read_text(encoding="utf-8"))
    parity = json.loads(args.parity_audit.read_text(encoding="utf-8"))

    run_id = predeclaration["run_id"]
    require(capture_manifest["run_id"] == run_id, "capture run ID mismatch")
    require(runtime["run_id"] == run_id, "runtime-manifest run ID mismatch")
    require(
        capture_manifest["episode_id"] == f"{run_id}-worker-0",
        "capture episode ID mismatch",
    )
    require(
        capture_manifest["runtime_manifest_sha256"] == sha256(runtime_payload),
        "retained runtime-manifest hash mismatch",
    )
    require(parity.get("accepted") is True, "F/G/H parity audit did not accept")
    require(parity.get("episode_id") == capture_manifest["episode_id"], "parity episode mismatch")

    configuration = predeclaration["configuration"]
    launch = runtime["launch_contract"]
    expected_launch = {
        "scene": configuration["scene"],
        "platform": configuration["platform"],
        "command_flag": configuration["command_flag"],
        "lidar_frame": configuration["lidar_frame"],
        "goal_distance_m": float(configuration["goal_distance_m"]),
        "action_duration_s": float(configuration["action_duration_s"]),
    }
    for key, expected in expected_launch.items():
        require(launch.get(key) == expected, f"launch-contract mismatch for {key}")

    checkout_paths = {
        "explanation_fidelity": args.umbrella_checkout,
        "astro_dock": args.astro_checkout,
        "crane_ml": args.crane_checkout,
    }
    for name, checkout in checkout_paths.items():
        record = runtime["checkouts"][name]
        require(record["commit"], f"missing commit for {name}")
        require(record["remote"], f"missing remote for {name}")
        require(record["dirty"] is False, f"runtime checkout was dirty: {name}")
        subprocess.run(
            ("git", "-C", str(checkout), "cat-file", "-e", f"{record['commit']}^{{commit}}"),
            check=True,
        )

    repository_for_role = {
        "capture_orchestrator": args.umbrella_checkout,
        "runtime_manifest_builder": args.umbrella_checkout,
        "behavior_tree_xml": args.crane_checkout,
        "nav2_parameter_file": args.crane_checkout,
        "land_fixture_entrypoint": args.crane_checkout,
        "nav2_fixture_entrypoint": args.crane_checkout,
    }
    artifacts = runtime["artifacts"]
    require(
        {item["role"] for item in artifacts} == set(repository_for_role),
        "runtime artifact-role set is incomplete or unexpected",
    )
    for artifact in artifacts:
        payload = git_blob(
            repository_for_role[artifact["role"]],
            artifact["repository_commit"],
            artifact["repository_path"],
        )
        require(artifact["byte_identical_to_git_object"] is True, "artifact equality not retained")
        require(artifact["content_sha256"] == sha256(payload), "artifact Git-object hash mismatch")
        require(artifact["bytes"] == len(payload), "artifact byte count mismatch")

    require(runtime["container_image"]["id"].startswith("sha256:"), "missing image ID")
    require(runtime["container_image"]["repo_digests"], "missing image repository digest")
    require(runtime["ros_packages"], "missing ROS package versions")
    require(runtime["player"]["sha256"], "missing player hash")
    require(runtime["player"]["managed_assemblies_sha256"], "missing assembly hash")
    require(runtime["player"]["build_source_commit_proven"] is False, "unexpected source proof")
    require(runtime["player"]["provenance_limit"], "missing player source limitation")
    leaked_keys = forbidden_keys(runtime)
    require(not leaked_keys, f"forbidden evaluator-only keys: {leaked_keys}")

    result = {
        "schema": "crane-runtime-provenance-calibration-result/v1",
        "status": "PASS",
        "run_id": run_id,
        "episode_id": capture_manifest["episode_id"],
        "runtime_manifest_sha256": sha256(runtime_payload),
        "artifact_count": len(artifacts),
        "parity_unit_count": len(parity["units"]),
        "navigation_outcome_is_not_a_pass_criterion": True,
        "checks": [
            "retained runtime-manifest hash and run identity",
            "effective launch contract versus predeclaration",
            "clean versioned checkout identities",
            "all declared source artifacts versus exact Git objects",
            "image, ROS package, player, and source-limit fields",
            "absence of evaluator-only keys",
            "accepted F/G/H information-parity audit",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
