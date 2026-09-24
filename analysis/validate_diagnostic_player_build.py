#!/usr/bin/env python3
"""Fail closed unless a diagnostic Unity bundle matches its declared identity and checkout assets."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


WAREHOUSE_SOURCE = "Assets/Scripts/Physics/Land/CraneReferenceWarehouse.cs"
WAREHOUSE_SCENE = "Assets/Scenes/TurtleBot3 Warehouse Validation.unity"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_build(
    provenance: dict,
    checkout: Path,
    expected_manifest_sha256: str,
    expected_assemblies_sha256: str,
    player: Path,
    catalog: Path,
) -> dict:
    manifest_record = provenance.get("build_manifest", {})
    manifest = manifest_record.get("content", {})
    assets = manifest.get("assets", [])
    by_path = {
        item.get("path"): item
        for item in assets
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }

    checks = {
        "provenance_schema": provenance.get("schema") == "crane-build-run-provenance-v1",
        "declared_build_manifest": manifest_record.get("sha256")
        == expected_manifest_sha256,
        "declared_managed_assemblies": provenance.get("managed_assemblies", {}).get("sha256")
        == expected_assemblies_sha256,
        "checkout_clean": provenance.get("checkout_at_run", {}).get("dirty") is False,
    }
    for name, relative in (
        ("warehouse_source", WAREHOUSE_SOURCE),
        ("warehouse_scene", WAREHOUSE_SCENE),
    ):
        source = checkout / relative
        embedded = by_path.get(relative, {})
        checks[f"{name}_present"] = bool(embedded)
        checks[f"{name}_hash_matches_checkout"] = (
            source.is_file()
            and isinstance(embedded.get("sha256"), str)
            and embedded["sha256"].lower() == sha256_file(source)
        )
        checks[f"{name}_size_matches_checkout"] = (
            source.is_file() and embedded.get("bytes") == source.stat().st_size
        )

    resources = player.parent / "CRANE_Data" / "resources.assets"
    catalog_bytes = catalog.read_bytes() if catalog.is_file() else b""
    resources_bytes = resources.read_bytes() if resources.is_file() else b""
    checks["runtime_resources_present"] = resources.is_file()
    checks["catalog_present"] = bool(catalog_bytes)
    checks["exact_catalog_embedded"] = bool(
        catalog_bytes and resources_bytes and catalog_bytes in resources_bytes
    )

    failed = sorted(name for name, accepted in checks.items() if not accepted)
    return {
        "schema": "crane-diagnostic-player-build-audit/v1",
        "accepted": not failed,
        "checks": checks,
        "failed_checks": failed,
        "expected_build_manifest_sha256": expected_manifest_sha256,
        "observed_build_manifest_sha256": manifest_record.get("sha256"),
        "expected_managed_assemblies_sha256": expected_assemblies_sha256,
        "observed_managed_assemblies_sha256": provenance.get("managed_assemblies", {}).get(
            "sha256"
        ),
        "checkout_commit": provenance.get("checkout_at_run", {}).get("commit"),
        "source_commit_proven": provenance.get("build_source_commit_proven") is True,
        "provenance_limit": provenance.get("provenance_limit"),
        "catalog_sha256": sha256_file(catalog) if catalog.is_file() else None,
        "runtime_resources_sha256": sha256_file(resources) if resources.is_file() else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--player", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--expected-build-manifest-sha256", required=True)
    parser.add_argument("--expected-managed-assemblies-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    for name, value in (
        ("--expected-build-manifest-sha256", args.expected_build_manifest_sha256),
        ("--expected-managed-assemblies-sha256", args.expected_managed_assemblies_sha256),
    ):
        if len(value) != 64 or any(char not in "0123456789abcdefABCDEF" for char in value):
            parser.error(f"{name} must be a SHA-256 hex digest")

    result = validate_build(
        json.loads(args.provenance.read_text(encoding="utf-8")),
        args.checkout.resolve(strict=True),
        args.expected_build_manifest_sha256.lower(),
        args.expected_managed_assemblies_sha256.lower(),
        args.player.resolve(strict=True),
        args.catalog.resolve(strict=True),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not result["accepted"]:
        raise SystemExit(
            "diagnostic player build rejected: " + ", ".join(result["failed_checks"])
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
