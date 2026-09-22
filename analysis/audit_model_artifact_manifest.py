#!/usr/bin/env python3
"""Recompute a model-artifact manifest from retained accepted outputs and cache files."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def inventory(paths: list[tuple[str, Path]]) -> dict[str, int | str]:
    digest = hashlib.sha256()
    byte_count = 0
    for label, path in sorted(paths):
        content = path.read_bytes()
        byte_count += len(content)
        digest.update(label.encode())
        digest.update(b"\0")
        digest.update(hashlib.sha256(content).hexdigest().encode())
        digest.update(b"\n")
    return {"file_count": len(paths), "bytes": byte_count, "sha256": digest.hexdigest()}


def load_outputs(workspace: Path, roots: list[str]) -> list[dict]:
    outputs = []
    for root_name in roots:
        root = workspace / root_name
        for path in sorted(root.glob("*.json")):
            if path.name.endswith(".stdout.json"):
                continue
            value = json.loads(path.read_text(encoding="utf-8"))
            if "outputs" in value:
                outputs.append(value)
    return outputs


def audit_artifact_list_manifest(workspace: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate current per-episode manifests without interpreting sealed response content."""

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise SystemExit("manifest has neither aggregate roots nor an artifact list")
    seen: set[str] = set()
    total_bytes = 0
    for entry in artifacts:
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative:
            raise SystemExit("artifact path must be a non-empty string")
        if relative in seen:
            raise SystemExit(f"duplicate artifact path: {relative}")
        seen.add(relative)
        path = (workspace / relative).resolve()
        if not path.is_relative_to(workspace):
            raise SystemExit(f"artifact escapes workspace: {relative}")
        if not path.is_file():
            raise SystemExit(f"missing artifact: {relative}")
        content = path.read_bytes()
        actual_bytes = len(content)
        actual_sha256 = hashlib.sha256(content).hexdigest()
        if actual_bytes != entry.get("bytes"):
            raise SystemExit(
                f"artifact bytes differ for {relative}: {actual_bytes} != {entry.get('bytes')}"
            )
        if actual_sha256 != entry.get("sha256"):
            raise SystemExit(f"artifact sha256 differs for {relative}")
        total_bytes += actual_bytes
    return {
        "status": "PASS",
        "schema": manifest.get("schema"),
        "manifest_kind": "per_episode_artifact_list",
        "artifact_count": len(artifacts),
        "artifact_bytes": total_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--workspace", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if "accepted_output_roots" not in manifest:
        print(json.dumps(audit_artifact_list_manifest(workspace, manifest), indent=2, sort_keys=True))
        return 0
    outputs = load_outputs(workspace, manifest["accepted_output_roots"])
    call_references = [call for output in outputs for call in output.get("calls", [])]
    physical_references = {(call["cache_key"], call["latency_ms"]) for call in call_references}
    request_keys = {key for key, _ in physical_references}

    cache_artifacts: dict[tuple[str, float], tuple[Path, dict]] = {}
    for root_name in manifest["cache_roots"]:
        for path in (workspace / root_name).glob("*.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            cache_artifacts[(value["cache_key"], value["latency_ms"])] = (path, value)
    missing = sorted(physical_references - cache_artifacts.keys())
    if missing:
        raise SystemExit(f"missing physical cache artifacts: {missing}")

    physical_paths = [
        (f"{key}@{latency:.6f}.json", cache_artifacts[(key, latency)][0])
        for key, latency in physical_references
    ]
    physical_inventory = inventory(physical_paths)
    expected_inventory = manifest["physical_cache_inventory"]
    for field in ("file_count", "bytes", "sha256"):
        if physical_inventory[field] != expected_inventory[field]:
            raise SystemExit(
                f"physical cache {field}: {physical_inventory[field]} != {expected_inventory[field]}")

    logical_outputs = sum(len(output["outputs"]) for output in outputs)
    checks = {
        "logical_condition_outputs": logical_outputs,
        "model_call_references": len(call_references),
        "unique_request_cache_keys_referenced": len(request_keys),
        "physical_model_call_artifacts_referenced": len(physical_references),
    }
    for field, actual in checks.items():
        if actual != manifest[field]:
            raise SystemExit(f"{field}: {actual} != {manifest[field]}")

    usage_fields = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens")
    usage = {field: 0 for field in usage_fields}
    latency = 0.0
    for reference in physical_references:
        value = cache_artifacts[reference][1]
        latency += value["latency_ms"]
        record = next(event["usage"] for event in value["events"] if event["type"] == "turn.completed")
        for field in usage_fields:
            usage[field] += record.get(field, 0)
    expected_usage = manifest["usage_physical_call_artifacts"]
    for field in usage_fields:
        if usage[field] != expected_usage[field]:
            raise SystemExit(f"usage {field}: {usage[field]} != {expected_usage[field]}")
    if abs(latency - expected_usage["aggregate_latency_ms"]) > 1e-6:
        raise SystemExit("aggregate latency differs")

    new_roots = manifest["new_output_inventory"]["roots"]
    new_paths = []
    for root_name in new_roots:
        root = workspace / root_name
        for path in sorted(root.glob("*.json")):
            new_paths.append((f"{root.parent.name}/{root.name}/{path.name}", path))
    new_inventory = inventory(new_paths)
    for field in ("file_count", "bytes", "sha256"):
        if new_inventory[field] != manifest["new_output_inventory"][field]:
            raise SystemExit(f"new output {field} differs")

    print(json.dumps({"status": "PASS", **checks, "physical_cache_inventory": physical_inventory,
                      "new_output_inventory": new_inventory}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
