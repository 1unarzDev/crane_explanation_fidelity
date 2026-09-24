#!/usr/bin/env python3
"""Offline rescore of retained Luna development calls under a versioned reference suite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from luna_model_judge import atomic_write_json, digest_path
from run_luna_judge_qualification import load_suite, score


def rescore(
    *, suite_path: Path, prior_report_path: Path, calls_root: Path, effort: str
) -> dict:
    suite = load_suite(suite_path)
    cases = [case for case in suite["cases"] if case["split"] == "development"]
    prior = json.loads(prior_report_path.read_text(encoding="utf-8"))
    keys = prior["call_cache_keys"][effort]
    if set(keys) != {case["case_id"] for case in cases}:
        raise ValueError("prior call inventory differs from amended development suite")
    judgments = {}
    call_hashes = {}
    for case in cases:
        path = calls_root / effort / "qualification" / f"{keys[case['case_id']]}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("status") != "VALID":
            raise ValueError(f"retained call is not valid: {path}")
        judgment = record["judgment"]
        if judgment.get("opaque_response_id") != case["case_id"]:
            raise ValueError("retained call response ID differs from suite case")
        judgments[case["case_id"]] = judgment
        call_hashes[case["case_id"]] = digest_path(path)
    result = score(cases, judgments)
    return {
        "schema": "crane-luna-judge-development-rescore/v1",
        "status": "QUALIFIED" if result["qualified"] else "NO_CONFIGURATION_QUALIFIED",
        "model_calls_made": 0,
        "suite": str(suite_path),
        "suite_sha256": digest_path(suite_path),
        "prior_report": str(prior_report_path),
        "prior_report_sha256": digest_path(prior_report_path),
        "effort": effort,
        "retained_call_sha256": call_hashes,
        "result": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", type=Path, required=True)
    parser.add_argument("--prior-report", type=Path, required=True)
    parser.add_argument("--calls-root", type=Path, required=True)
    parser.add_argument("--effort", choices=("low", "medium", "high"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = rescore(
        suite_path=args.suite.resolve(),
        prior_report_path=args.prior_report.resolve(),
        calls_root=args.calls_root.resolve(),
        effort=args.effort,
    )
    atomic_write_json(args.output, report)
    print(json.dumps({"status": report["status"], "model_calls_made": 0}))


if __name__ == "__main__":
    main()
