#!/usr/bin/env python3
"""Reject evaluator-only names or JSON keys below a robot-visible release root."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORBIDDEN_KEY_PARTS = (
    "fault_injection",
    "intervention_identity",
    "mobility_hold",
    "mobility_release",
    "expected_outcome",
    "evaluator_truth",
    "ground_truth",
)
FORBIDDEN_PATH_PARTS = (
    "evaluator_only",
    "evaluator-only",
    "ground_truth",
    "ground-truth",
    "fault_injection",
    "fault-injection",
    "mobility_hold",
    "mobility_release",
    "expected_outcome",
)


def key_findings(value: Any, source: Path, prefix: str = "") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            location = f"{prefix}.{key}" if prefix else key
            normalized = key.lower().replace("-", "_")
            safe_negative_attestation = (
                normalized == "evaluator_truth_available_to_methods" and child is False
            )
            if not safe_negative_attestation and any(
                part in normalized for part in FORBIDDEN_KEY_PARTS
            ):
                findings.append(f"{source}:{location}")
            findings.extend(key_findings(child, source, location))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(key_findings(child, source, f"{prefix}[{index}]"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    root = args.root.resolve(strict=True)
    findings: list[str] = []
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix().lower()
        if any(part in relative for part in FORBIDDEN_PATH_PARTS):
            findings.append(f"forbidden path: {relative}")
        if path.suffix.lower() not in {".json", ".jsonl"}:
            continue
        try:
            if path.suffix.lower() == ".jsonl":
                values = [json.loads(line) for line in path.read_text().splitlines() if line]
            else:
                values = [json.loads(path.read_text(encoding="utf-8"))]
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            findings.append(f"unparseable structured artifact: {relative}: {error}")
            continue
        for value in values:
            findings.extend(key_findings(value, Path(relative)))
    if findings:
        raise SystemExit("robot-visible leakage scan failed:\n" + "\n".join(findings))
    print(f"Robot-visible leakage scan passed: {len(files)} files below {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
