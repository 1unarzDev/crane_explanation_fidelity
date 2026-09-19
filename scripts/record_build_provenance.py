#!/usr/bin/env python3
"""Record the exact CRANE player artifact used by an evaluator-only run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(checkout: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ("git", "-C", str(checkout), *arguments), text=True
    ).strip()


def managed_assembly_record(player: Path) -> dict:
    managed = player.parent / f"{player.stem}_Data" / "Managed"
    if not managed.is_dir():
        # Unity players conventionally use <product>_Data, while this project names the
        # executable CRANE.x86_64 and the data directory CRANE_Data.
        managed = player.parent / "CRANE_Data" / "Managed"
    assemblies = sorted(managed.glob("*.dll"))
    if not assemblies:
        raise FileNotFoundError(f"No managed assemblies found below {managed}")
    digest = hashlib.sha256()
    total_bytes = 0
    physics_hash = None
    for assembly in assemblies:
        relative = assembly.relative_to(player.parent).as_posix()
        file_hash = sha256_file(assembly)
        size = assembly.stat().st_size
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(str(size).encode("ascii") + b"\0")
        digest.update(file_hash.encode("ascii") + b"\n")
        total_bytes += size
        if assembly.name == "PhysicsAssembly.dll":
            physics_hash = file_hash
    if physics_hash is None:
        raise FileNotFoundError(f"PhysicsAssembly.dll not found below {managed}")
    return {
        "algorithm": "sha256(relative_path NUL bytes NUL file_sha256 LF), sorted by path",
        "sha256": digest.hexdigest(),
        "assembly_count": len(assemblies),
        "total_bytes": total_bytes,
        "physics_assembly_sha256": physics_hash,
    }


def build_record(player: Path, checkout: Path) -> dict:
    player = player.resolve(strict=True)
    checkout = checkout.resolve(strict=True)
    manifest_path = player.parent / "crane-build-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"CRANE build manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_commit = manifest.get("sourceCommit")
    checkout_commit = git_output(checkout, "rev-parse", "HEAD")
    dirty = bool(git_output(checkout, "status", "--porcelain"))
    return {
        "schema": "crane-build-run-provenance-v1",
        "player": {
            "basename": player.name,
            "sha256": sha256_file(player),
            "bytes": player.stat().st_size,
        },
        "managed_assemblies": managed_assembly_record(player),
        "build_manifest": {
            "basename": manifest_path.name,
            "sha256": sha256_file(manifest_path),
            "content": manifest,
        },
        "checkout_at_run": {
            "commit": checkout_commit,
            "dirty": dirty,
        },
        "build_source_commit": source_commit,
        "build_source_commit_proven": bool(source_commit),
        "provenance_limit": None if source_commit else (
            "The embedded build manifest does not record a source commit. The checkout commit "
            "is recorded separately and must not be represented as the proven binary source."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = build_record(args.player, args.checkout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
