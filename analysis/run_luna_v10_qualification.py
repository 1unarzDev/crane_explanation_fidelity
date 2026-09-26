#!/usr/bin/env python3
"""Run the prospectively frozen Luna-v10 held-out qualification exactly once."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


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
BUILDER = ROOT / "analysis/build_luna_v10_qualification_suite.py"


def load_suite(path: Path) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") != "crane-luna-judge-qualification-suite/v10":
        raise ValueError("v10 qualification suite schema mismatch")
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 26:
        raise ValueError("v10 suite must contain exactly 26 cases")
    if sum(case.get("accuracy_eligible") is True for case in cases) != 24:
        raise ValueError("v10 suite must contain exactly 24 accuracy cases")
    if any(case.get("split") != "heldout" for case in cases):
        raise ValueError("v10 suite is not fresh heldout")
    return suite


def validate_freeze(path: Path, suite_path: Path) -> dict[str, Any]:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "crane-luna-judge-freeze/v10":
        raise ValueError("v10 freeze schema mismatch")
    if freeze.get("status") != "FROZEN_BEFORE_ANY_V10_QUALIFICATION_CALL":
        raise ValueError("v10 freeze status mismatch")
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
            raise ValueError(f"v10 freeze {field} mismatch")
    if freeze.get("passes") != ["pass-1", "pass-2"]:
        raise ValueError("v10 must authorize exactly two passes")
    model = freeze.get("model", {})
    if model.get("requested_id") != "gpt-6-luna" or model.get("reasoning_effort") != "high":
        raise ValueError("v10 model configuration mismatch")
    return freeze


def run_pass(cases: list[dict[str, Any]], pass_id: str, output_root: Path):
    caller = LunaIsolatedCodexCaller(
        cache=output_root / "calls" / "high" / pass_id,
        effort="high",
        prompt_path=PROMPT,
    )
    judgments: dict[str, dict[str, Any]] = {}
    keys: dict[str, str] = {}
    failures: dict[str, str] = {}
    for case in cases:
        try:
            record = caller.call(qualification_envelope(case, pass_id))
        except RuntimeError as error:
            failures[case["case_id"]] = str(error)
            continue
        judgments[case["case_id"]] = record["judgment"]
        keys[case["case_id"]] = record["cache_key"]
    return judgments, keys, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    suite_path = args.suite.resolve()
    suite = load_suite(suite_path)
    validate_freeze(args.freeze.resolve(), suite_path)
    report_path = args.output_root / "heldout-qualification.json"
    if report_path.exists():
        raise FileExistsError("v10 held-out report already exists")

    passes: dict[str, Any] = {}
    keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, keys[pass_id], failures = run_pass(suite["cases"], pass_id, args.output_root)
        if failures:
            passes[pass_id] = {
                "qualified": False,
                "call_failure_count": len(failures),
                "call_failures": failures,
                "scoring_status": "NOT_SCORED_INCOMPLETE_INVENTORY",
            }
        else:
            passes[pass_id] = score(suite, judgments)
            passes[pass_id]["call_failure_count"] = 0
            passes[pass_id]["call_failures"] = {}
            passes[pass_id]["gates"]["zero_call_failures"] = True

    report = {
        "schema": "crane-luna-judge-heldout-qualification/v10",
        "suite": str(suite_path.relative_to(ROOT)),
        "suite_sha256": digest_path(suite_path),
        "freeze": str(args.freeze.resolve().relative_to(ROOT)),
        "freeze_sha256": digest_path(args.freeze.resolve()),
        "reasoning_effort": "high",
        "passes": passes,
        "call_cache_keys": keys,
        "status": "QUALIFIED" if all(item["qualified"] for item in passes.values()) else "FAILED",
        "study_scoring_allowed": all(item["qualified"] for item in passes.values()),
    }
    atomic_write_json(report_path, report)
    print(json.dumps({"status": report["status"], "passes": list(passes)}))


if __name__ == "__main__":
    main()
