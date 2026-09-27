#!/usr/bin/env python3
"""Execute the frozen finite causal-link detector qualification once."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

try:
    from audit_explicit_causal_links import DETECTOR_SOURCE, RULE_IDS, classify_text
except ModuleNotFoundError:  # Imported as analysis.qualify_explicit_causal_link_detector.
    from analysis.audit_explicit_causal_links import (
        DETECTOR_SOURCE,
        RULE_IDS,
        classify_text,
    )


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(suite: dict[str, Any]) -> dict[str, Any]:
    if suite.get("schema") != "crane-explicit-causal-link-detector-qualification/v1":
        raise ValueError("unsupported qualification suite")
    rows = []
    for case in suite["cases"]:
        prohibited = frozenset(case.get("prohibited_relations", RULE_IDS))
        findings = classify_text(case["text"], prohibited)
        actual = [item["relation"] for item in findings]
        expected = case["relations"]
        spans_exact = all(
            case["text"][item["start"] : item["end"]] == item["span"]
            for item in findings
        )
        rows.append(
            {
                "id": case["id"],
                "expected_relations": expected,
                "actual_relations": actual,
                "polarity_correct": bool(actual) == bool(expected),
                "relation_set_correct": actual == expected,
                "spans_exact": spans_exact,
                "findings": findings,
            }
        )
    count = len(rows)
    metrics = {
        "case_count": count,
        "case_polarity_accuracy": sum(item["polarity_correct"] for item in rows) / count,
        "relation_set_accuracy": sum(item["relation_set_correct"] for item in rows) / count,
        "exact_span_accuracy": sum(item["spans_exact"] for item in rows) / count,
        "execution_failures": 0,
    }
    acceptance = suite["acceptance"]
    passed = all(metrics[key] == value for key, value in acceptance.items())
    return {"metrics": metrics, "passed": passed, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    suite_path = args.suite.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError(f"refusing existing qualification output: {output}")
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    declared_hash = suite.get("detector_sha256")
    actual_hash = sha256(DETECTOR_SOURCE)
    if declared_hash != actual_hash:
        raise ValueError(
            f"detector hash mismatch: suite={declared_hash}, actual={actual_hash}"
        )
    result = evaluate(suite)
    report = {
        "schema": "crane-explicit-causal-link-detector-qualification-result/v1",
        "qualification_id": suite["qualification_id"],
        "suite_path": suite_path.relative_to(ROOT).as_posix(),
        "suite_sha256": sha256(suite_path),
        "detector_path": DETECTOR_SOURCE.relative_to(ROOT).as_posix(),
        "detector_sha256": actual_hash,
        "scope": suite["scope"],
        **result,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], **report["metrics"]}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
