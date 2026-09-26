#!/usr/bin/env python3
"""Run the frozen two-pass boat-specific Luna qualification exactly once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from luna_model_judge import atomic_write_json, digest_path  # noqa: E402
from run_luna_v11_qualification import run_pass, score  # noqa: E402


PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
CALLER = ROOT / "analysis/luna_model_judge.py"
BUILDER = ROOT / "analysis/build_luna_boat_qualification_suite.py"


def load_suite(path: Path) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") != "crane-luna-boat-qualification-suite/v1":
        raise ValueError("unexpected boat qualification suite")
    if len(suite.get("cases", [])) != 12:
        raise ValueError("boat qualification suite inventory mismatch")
    return suite


def validate_freeze(path: Path, suite_path: Path) -> dict[str, Any]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "crane-luna-boat-judge-freeze/v1":
        raise ValueError("unexpected boat judge freeze")
    if freeze.get("status") != "FROZEN_BEFORE_ANY_BOAT_QUALIFICATION_CALL":
        raise ValueError("boat judge freeze is inactive")
    expected = {
        "suite_sha256": suite_path,
        "prompt_sha256": PROMPT,
        "output_schema_sha256": SCHEMA,
        "caller_source_sha256": CALLER,
        "runner_source_sha256": Path(__file__),
        "suite_builder_sha256": BUILDER,
    }
    for field, source in expected.items():
        if freeze.get(field) != digest_path(source):
            raise ValueError(f"boat judge freeze mismatch: {field}")
    if freeze.get("passes") != ["pass-1", "pass-2"]:
        raise ValueError("boat judge pass inventory mismatch")
    return freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    suite_path = args.suite.resolve(strict=True)
    freeze_path = args.freeze.resolve(strict=True)
    suite = load_suite(suite_path)
    validate_freeze(freeze_path, suite_path)
    report_path = args.output_root / "heldout-qualification.json"
    if report_path.exists():
        raise FileExistsError("boat qualification result already exists")
    passes: dict[str, Any] = {}
    keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, keys[pass_id], failures = run_pass(suite["cases"], pass_id, args.output_root)
        if failures:
            passes[pass_id] = {
                "qualified": False,
                "call_failures": failures,
                "call_failure_count": len(failures),
                "scoring_status": "NOT_SCORED_INCOMPLETE_INVENTORY",
            }
        else:
            passes[pass_id] = {
                **score(suite, judgments),
                "call_failures": {},
                "call_failure_count": 0,
            }
            passes[pass_id]["gates"]["zero_call_failures"] = True
    qualified = all(value.get("qualified") is True for value in passes.values())
    report = {
        "schema": "crane-luna-boat-heldout-qualification/v1",
        "suite": str(suite_path.relative_to(ROOT)),
        "suite_sha256": digest_path(suite_path),
        "freeze": str(freeze_path.relative_to(ROOT)),
        "freeze_sha256": digest_path(freeze_path),
        "passes": passes,
        "call_cache_keys": keys,
        "status": "QUALIFIED" if qualified else "FAILED",
        "boat_study_scoring_allowed": qualified,
        "land_qualification_unchanged": True,
    }
    atomic_write_json(report_path, report)
    print(json.dumps({"status": report["status"]}))


if __name__ == "__main__":
    main()
