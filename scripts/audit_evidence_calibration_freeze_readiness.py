#!/usr/bin/env python3
"""Fail closed unless every P11 prerequisite is evidenced and the freeze is explicit."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


READY = "PASS"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    failures = []
    if manifest.get("schema") != "crane-evidence-calibration-p11-prefreeze-readiness/v1":
        failures.append("unsupported readiness schema")
    for item in manifest.get("development_components", []):
        path = root / item["path"]
        if not path.is_file():
            failures.append(f"missing component: {item['path']}")
        elif sha256(path) != item["sha256"]:
            failures.append(f"component hash mismatch: {item['path']}")
    requirements = manifest.get("requirements", [])
    ids = [item.get("requirement_id") for item in requirements]
    if len(ids) != len(set(ids)):
        failures.append("duplicate readiness requirement")
    for item in requirements:
        if item.get("status") != READY:
            failures.append(f"requirement not passed: {item.get('requirement_id')}={item.get('status')}")
        if item.get("status") == READY and not item.get("evidence"):
            failures.append(f"passed requirement lacks evidence: {item.get('requirement_id')}")
    if manifest.get("status") != "P11_FROZEN" or not manifest.get("confirmation_authorized"):
        failures.append("P11 freeze and explicit confirmation authorization are absent")
    return {
        "schema": "crane-evidence-calibration-freeze-readiness-audit/v1",
        "readiness_id": manifest.get("readiness_id"),
        "ready": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "confirmation_independent_n": manifest.get("confirmation_independent_n"),
        "replication_independent_n": manifest.get("replication_independent_n"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--manifest", type=Path,
                        default=Path("manifests/study/evidence-calibration-p11-prefreeze-readiness.json"))
    args = parser.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    result = audit(root, json.loads(manifest_path.read_text()))
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(0 if result["ready"] else 1)


if __name__ == "__main__":
    main()
