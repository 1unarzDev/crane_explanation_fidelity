#!/usr/bin/env python3
"""Create a content-free SHA-256 inventory for one or more governed artifact roots."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", action="append", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provenance", required=True)
    parser.add_argument("--status", default="DEVELOPMENT_ONLY")
    args = parser.parse_args()

    workspace = Path(__file__).resolve().parent.parent
    allowed_roots = tuple(
        (workspace / name).resolve()
        for name in ("data", "model_outputs", "research/explanation_fidelity/model_cache")
    )
    roots: list[Path] = []
    for value in args.root:
        root = (workspace / value).resolve()
        if not root.is_dir() or not any(root == allowed or allowed in root.parents for allowed in allowed_roots):
            parser.error("each --root must be an existing governed artifact directory")
        roots.append(root)
    output = (workspace / args.output).resolve()
    manifests_root = (workspace / "manifests").resolve()
    if manifests_root not in output.parents:
        parser.error("--output must be below manifests/")
    if output.exists():
        raise SystemExit(f"refusing to overwrite manifest: {output}")

    paths = sorted({path for root in roots for path in root.rglob("*") if path.is_file()})
    artifacts = [
        {
            "path": path.relative_to(workspace).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": digest(path),
        }
        for path in paths
    ]
    payload = {
        "schema": "crane-explain-artifact-list-manifest/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "roots": [root.relative_to(workspace).as_posix() for root in roots],
        "provenance": args.provenance,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output.relative_to(workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
