#!/usr/bin/env python3
"""Create a content-free SHA-256 inventory for an untracked data directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provenance", required=True)
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parent.parent
    source = (workspace / args.root).resolve()
    output = (workspace / args.output).resolve()
    if workspace not in source.parents or not source.is_dir():
        parser.error("--root must be an existing directory below the umbrella root")
    data_root = (workspace / "data").resolve()
    if data_root not in source.parents:
        parser.error("--root must be below data/")
    manifests_root = (workspace / "manifests").resolve()
    if manifests_root not in output.parents:
        parser.error("--output must be below manifests/")

    files = []
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        files.append({
            "path": path.relative_to(workspace).as_posix(),
            "sha256": digest(path),
            "bytes": path.stat().st_size,
        })
    manifest = {
        "schema": "crane-explain-data-manifest/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_root": source.relative_to(workspace).as_posix(),
        "provenance": args.provenance,
        "file_count": len(files),
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise SystemExit(f"refusing to overwrite manifest: {output}")
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output.relative_to(workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
