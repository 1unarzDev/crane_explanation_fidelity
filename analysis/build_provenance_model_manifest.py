#!/usr/bin/env python3
"""Build a hash/usage manifest for one retained F/G/H provenance experiment batch."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def artifact(path: Path, workspace: Path) -> dict[str, Any]:
    return {
        "path": path.relative_to(workspace).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def usage(events: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    for event in events:
        raw = event.get("usage")
        if not isinstance(raw, dict):
            continue
        for key in totals:
            totals[key] += int(raw.get(key, 0))
    return totals


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cache-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--status", default="DEVELOPMENT_ONLY")
    args = parser.parse_args()
    workspace = Path(__file__).resolve().parent.parent
    output_root = (workspace / args.output_root).resolve()
    cache_root = (workspace / args.cache_root).resolve()
    manifest_path = (workspace / args.manifest).resolve()
    if manifest_path.exists():
        raise SystemExit(f"refusing existing manifest: {manifest_path}")
    if not output_root.is_dir() or not cache_root.is_dir():
        parser.error("output and cache roots must be existing directories")
    if (workspace / "model_outputs").resolve() not in output_root.parents:
        parser.error("--output-root must be below model_outputs/")
    if (workspace / "research/explanation_fidelity/model_cache").resolve() not in cache_root.parents:
        parser.error("--cache-root must be below research/explanation_fidelity/model_cache/")
    if (workspace / "manifests/model_outputs").resolve() not in manifest_path.parents:
        parser.error("--manifest must be below manifests/model_outputs/")

    output_paths = sorted(output_root.rglob("*.json"))
    outputs = [json.loads(path.read_text(encoding="utf-8")) for path in output_paths]
    if not outputs:
        raise SystemExit("no result JSON files found")
    call_keys = [call["cache_key"] for output in outputs for call in output["calls"]]
    if len(call_keys) != len(set(call_keys)):
        raise SystemExit("batch contains duplicate model-call cache keys")
    cache_paths = [cache_root / f"{key}.json" for key in sorted(call_keys)]
    missing = [str(path) for path in cache_paths if not path.is_file()]
    if missing:
        raise SystemExit(f"missing cache artifacts: {missing}")
    calls = [json.loads(path.read_text(encoding="utf-8")) for path in cache_paths]
    usage_totals = {key: 0 for key in usage([])}
    aggregate_latency_ms = 0.0
    for call in calls:
        aggregate_latency_ms += float(call["latency_ms"])
        for key, value in usage(call["events"]).items():
            usage_totals[key] += value
    payload = {
        "schema": "crane-explain-model-artifact-manifest/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": args.status,
        "episode_ids": sorted({output["episode_id"] for output in outputs}),
        "question_kinds": sorted({output["question_kind"] for output in outputs}),
        "conditions": sorted({condition for output in outputs for condition in output["conditions"]}),
        "provider": calls[0]["request"]["provider"],
        "model": calls[0]["request"]["model"],
        "reasoning_effort": calls[0]["request"]["reasoning_effort"],
        "single_sample_no_retry": all(output["single_sample_no_retry"] for output in outputs),
        "information_parity_audited": all(
            output["information_parity"]["accepted"] for output in outputs
        ),
        "evaluator_truth_available_to_methods": False,
        "new_model_calls": len(calls),
        "logical_condition_outputs": sum(len(output["outputs"]) for output in outputs),
        "usage": {
            **usage_totals,
            "aggregate_latency_ms": aggregate_latency_ms,
            "cost_usd": None,
            "cost_status": "not_reported_by_codex_cli_chatgpt_login",
        },
        "output_root": output_root.relative_to(workspace).as_posix(),
        "cache_root": cache_root.relative_to(workspace).as_posix(),
        "artifacts": [
            *[artifact(path, workspace) for path in output_paths],
            *[artifact(path, workspace) for path in cache_paths],
        ],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(manifest_path.relative_to(workspace))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
