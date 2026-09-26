#!/usr/bin/env python3
"""Run one no-retry Luna-v9 prompt-development pass on exposed cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from luna_model_judge import (  # noqa: E402
    LunaIsolatedCodexCaller,
    atomic_write_json,
    digest_path,
    qualification_envelope,
)
from run_luna_judge_qualification_v8 import score  # noqa: E402


PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
BUILDER = ROOT / "analysis/build_luna_v9_development_suite.py"


def load_suite(path: Path) -> dict:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") != "crane-luna-judge-development-suite/v9":
        raise ValueError("v9 development suite schema mismatch")
    if suite.get("status") != "DEVELOPMENT_ONLY_EXPOSED_CASES":
        raise ValueError("v9 development suite is not explicitly development-only")
    if len(suite.get("cases", [])) != 16:
        raise ValueError("v9 development suite must contain 16 cases")
    return suite


def validate_freeze(path: Path, suite_path: Path) -> dict:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "crane-luna-judge-development-freeze/v9":
        raise ValueError("v9 development freeze schema mismatch")
    if freeze.get("status") != "FROZEN_BEFORE_ANY_V9_DEVELOPMENT_CALL":
        raise ValueError("v9 development freeze status mismatch")
    expected = {
        "suite_sha256": suite_path,
        "prompt_sha256": PROMPT,
        "output_schema_sha256": SCHEMA,
        "caller_source_sha256": ROOT / "analysis/luna_model_judge.py",
        "runner_source_sha256": Path(__file__),
        "suite_builder_sha256": BUILDER,
    }
    for field, source in expected.items():
        if freeze.get(field) != digest_path(source):
            raise ValueError(f"v9 development freeze {field} mismatch")
    model = freeze.get("model", {})
    if model.get("requested_id") != "gpt-6-luna" or model.get("reasoning_effort") != "high":
        raise ValueError("v9 development model configuration mismatch")
    if freeze.get("passes") != ["development-pass-1"]:
        raise ValueError("v9 development must authorize exactly one pass")
    if freeze.get("confirmatory_use") is not False:
        raise ValueError("v9 exposed development cases cannot authorize confirmatory use")
    return freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    suite = load_suite(args.suite)
    freeze = validate_freeze(args.freeze.resolve(), args.suite.resolve())
    report_path = args.output_root / "development-result.json"
    if report_path.exists():
        raise FileExistsError("v9 development report already exists")
    caller = LunaIsolatedCodexCaller(
        cache=args.output_root / "calls/high/development",
        effort="high",
        prompt_path=PROMPT,
    )
    judgments = {}
    cache_keys = {}
    failures = {}
    for case in suite["cases"]:
        try:
            record = caller.call(qualification_envelope(case, "qualification"))
        except RuntimeError as error:
            failures[case["case_id"]] = str(error)
            continue
        judgments[case["case_id"]] = record["judgment"]
        cache_keys[case["case_id"]] = record["cache_key"]
    if failures:
        result = {"status": "FAILED_CALLS", "failures": failures, "cache_keys": cache_keys}
    else:
        scored = score(suite, judgments)
        result = {
            "status": "DEVELOPMENT_PASS" if scored["qualified"] else "DEVELOPMENT_FAIL",
            "prompt": str(PROMPT.relative_to(ROOT)),
            "freeze": str(args.freeze.resolve().relative_to(ROOT)),
            "freeze_sha256": digest_path(args.freeze.resolve()),
            "scored": scored,
            "cache_keys": cache_keys,
            "confirmatory_use": False,
        }
    atomic_write_json(report_path, result)
    print(json.dumps({"status": result["status"], "failures": len(failures)}))


if __name__ == "__main__":
    main()
