#!/usr/bin/env python3
"""Run the frozen one-time corrected primary-family causal qualification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from luna_model_judge import atomic_write_json, digest_path
from run_contract_complete_luna_qualification_v2 import score
from run_luna_v11_qualification import run_pass


ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
CALLER = ROOT / "analysis/luna_model_judge.py"
BUILDER = ROOT / "analysis/build_contract_primary_causal_luna_qualification_v2.py"


def validate_freeze(path: Path, suite_path: Path) -> dict[str, Any]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "crane-contract-primary-causal-luna-qualification-freeze/v2":
        raise ValueError("v2 primary-causal freeze schema mismatch")
    if freeze.get("status") != "FROZEN_BEFORE_ANY_QUALIFICATION_CALL":
        raise ValueError("v2 primary-causal qualification was not prospectively frozen")
    for field, source in {
        "suite_sha256": suite_path,
        "prompt_sha256": PROMPT,
        "output_schema_sha256": SCHEMA,
        "caller_source_sha256": CALLER,
        "runner_source_sha256": Path(__file__),
        "suite_builder_sha256": BUILDER,
    }.items():
        if freeze.get(field) != digest_path(source):
            raise ValueError(f"v2 primary-causal freeze {field} mismatch")
    return freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    suite_path = args.suite.resolve(strict=True)
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    if suite.get("schema") != "crane-contract-primary-causal-luna-qualification-suite/v2" or len(suite.get("cases", [])) != 12:
        raise ValueError("v2 primary-causal suite mismatch")
    validate_freeze(args.freeze.resolve(strict=True), suite_path)
    report_path = args.output_root / "heldout-qualification.json"
    if report_path.exists():
        raise FileExistsError("v2 primary-causal result exists")
    passes: dict[str, Any] = {}
    keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, keys[pass_id], failures = run_pass(suite["cases"], pass_id, args.output_root)
        if failures:
            passes[pass_id] = {"qualified": False, "call_failures": failures,
                               "call_failure_count": len(failures),
                               "scoring_status": "NOT_SCORED_INCOMPLETE_INVENTORY"}
        else:
            passes[pass_id] = {**score(suite, judgments), "call_failures": {}, "call_failure_count": 0}
            passes[pass_id]["gates"]["zero_call_failures"] = True
            passes[pass_id]["qualified"] = all(passes[pass_id]["gates"].values())
    qualified = all(item["qualified"] for item in passes.values())
    report = {
        "schema": "crane-contract-primary-causal-luna-qualification-result/v2",
        "status": "QUALIFIED" if qualified else "FAILED",
        "suite": suite_path.relative_to(ROOT).as_posix(),
        "suite_sha256": digest_path(suite_path),
        "freeze": args.freeze.resolve().relative_to(ROOT).as_posix(),
        "freeze_sha256": digest_path(args.freeze.resolve()),
        "passes": passes,
        "call_cache_keys": keys,
        "study_scoring_allowed": qualified,
        "confirmatory_alpha_consumed": 0.0,
    }
    atomic_write_json(report_path, report)
    print(json.dumps({"status": report["status"]}))


if __name__ == "__main__":
    main()
