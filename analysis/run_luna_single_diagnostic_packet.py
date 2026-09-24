#!/usr/bin/env python3
"""Score one immutable four-condition diagnostic packet with two isolated Luna passes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from luna_model_judge import LunaIsolatedCodexCaller, atomic_write_json, packet_envelope


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def success(judgment: dict[str, Any]) -> bool:
    return judgment["mechanism_identification"] == "correct" and judgment["material_error"] is False


def run(packet: Path, key_path: Path, output_root: Path) -> dict[str, Any]:
    rows = read_jsonl(packet)
    if len(rows) != 4 or len({row["response_id"] for row in rows}) != 4:
        raise ValueError("packet must contain four unique responses")
    key = json.loads(key_path.read_text(encoding="utf-8"))
    conditions = {item["response_id"]: item["condition"] for item in key["entries"]}
    if set(conditions) != {row["response_id"] for row in rows}:
        raise ValueError("packet and condition-key inventories differ")
    joined: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    cache_keys: dict[str, dict[str, str]] = {}
    for pass_id in ("pass-1", "pass-2"):
        caller = LunaIsolatedCodexCaller(
            cache=output_root / "calls" / "high" / pass_id, effort="high"
        )
        cache_keys[pass_id] = {}
        for row in rows:
            response_id = row["response_id"]
            try:
                record = caller.call(packet_envelope(row, "diagnostic", pass_id))
            except RuntimeError as error:
                failures.append({"pass_id": pass_id, "response_id": response_id, "error": str(error)})
                continue
            cache_keys[pass_id][response_id] = record["cache_key"]
            joined.append(
                {
                    "pass_id": pass_id,
                    "response_id": response_id,
                    "condition": conditions[response_id],
                    "judgment": record["judgment"],
                }
            )
    passes: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        selected = [item for item in joined if item["pass_id"] == pass_id]
        passes[pass_id] = {
            condition: {
                "supported_diagnostic_success": success(
                    next(item["judgment"] for item in selected if item["condition"] == condition)
                ),
                "material_error": next(
                    item["judgment"]["material_error"]
                    for item in selected
                    if item["condition"] == condition
                ),
                "mechanism_identification": next(
                    item["judgment"]["mechanism_identification"]
                    for item in selected
                    if item["condition"] == condition
                ),
            }
            for condition in ("R", "P", "T", "N")
        }
    report = {
        "schema": "crane-luna-single-diagnostic-packet-result/v1",
        "status": "DEVELOPMENT_ONLY_NOT_CONFIRMATORY",
        "packet_sha256": digest(packet),
        "condition_key_sha256": digest(key_path),
        "passes": passes,
        "call_failures": failures,
        "cache_keys": cache_keys,
        "confirmatory_alpha_consumed": 0.0,
    }
    atomic_write_json(output_root / "development-summary.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if (output / "development-summary.json").exists():
        raise SystemExit("refusing to overwrite completed result")
    report = run(args.packet.resolve(strict=True), args.key.resolve(strict=True), output)
    print(json.dumps({"status": report["status"], "call_failures": len(report["call_failures"])}))
    return 0 if not report["call_failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
