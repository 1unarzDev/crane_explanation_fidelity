#!/usr/bin/env python3
"""Run the one-shot complete-endpoint extension under unchanged Luna v12."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from luna_model_judge import atomic_write_json, digest_path  # noqa: E402
from run_luna_judge_qualification_v8 import wilson_interval  # noqa: E402
from run_luna_v11_qualification import bucket, run_pass, units  # noqa: E402


PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
CALLER = ROOT / "analysis/luna_model_judge.py"
BUILDER = ROOT / "analysis/build_luna_v12_complete_endpoint_extension.py"


def complete_success(case: dict, judgment: dict) -> bool:
    statuses = units(judgment)
    required = case["complete_endpoint_unit_ids"]
    if set(statuses) != set(required):
        raise ValueError(f"{case['case_id']}: returned unit inventory mismatch")
    return judgment.get("material_error") is False and all(
        statuses[unit_id] == "covered" for unit_id in required
    )


def score(suite: dict, judgments: dict[str, dict]) -> dict:
    cases = suite["cases"]
    if set(judgments) != {case["case_id"] for case in cases}:
        raise ValueError("complete-endpoint judgment inventory mismatch")
    endpoint_matches = []
    unit_matches = []
    core_matches = []
    positive_matches = []
    negative_matches = []
    category_errors: Counter[str] = Counter()
    results = []
    for case in cases:
        actual = judgments[case["case_id"]]
        expected = case["expected"]
        actual_units = units(actual)
        expected_units = expected["required_unit_statuses"]
        if set(actual_units) != set(expected_units):
            raise ValueError(f"{case['case_id']}: unit inventory mismatch")
        unit_match = {
            unit_id: actual_units[unit_id] == expected_units[unit_id]
            for unit_id in expected_units
        }
        core_match = {
            field: actual.get(field) == expected[field]
            for field in case["scored_core_fields"]
        }
        expected_success = expected["material_error"] is False and all(
            status == "covered" for status in expected_units.values()
        )
        actual_success = complete_success(case, actual)
        endpoint_match = actual_success == expected_success
        endpoint_matches.append(endpoint_match)
        unit_matches.extend(unit_match.values())
        core_matches.extend(core_match.values())
        (positive_matches if expected_success else negative_matches).append(endpoint_match)
        if not endpoint_match and case["variant"].startswith("omit-"):
            category_errors[case["variant"]] += 1
        results.append(
            {
                "case_id": case["case_id"],
                "family": case["family"],
                "variant": case["variant"],
                "expected_complete_success": expected_success,
                "actual_complete_success": actual_success,
                "complete_endpoint_match": endpoint_match,
                "unit_matches": unit_match,
                "core_matches": core_match,
            }
        )
    false_rejections = len(positive_matches) - sum(positive_matches)
    false_acceptances = len(negative_matches) - sum(negative_matches)
    thresholds = suite["thresholds"]
    endpoint = bucket(endpoint_matches)
    unit_coverage = bucket(unit_matches)
    core = bucket(core_matches)
    gates = {
        "complete_endpoint_accuracy": endpoint["accuracy"]
        >= thresholds["minimum_complete_endpoint_accuracy"],
        "unit_coverage_accuracy": unit_coverage["accuracy"]
        >= thresholds["minimum_unit_coverage_accuracy"],
        "core_field_accuracy": core["accuracy"]
        >= thresholds["minimum_core_field_accuracy"],
        "false_rejection_rate": false_rejections / len(positive_matches)
        <= thresholds["maximum_false_rejection_rate"],
        "false_acceptance_rate": false_acceptances / len(negative_matches)
        <= thresholds["maximum_false_acceptance_rate"],
        "omission_categories": all(
            count <= thresholds["maximum_errors_per_omission_category"]
            for count in category_errors.values()
        ),
    }
    return {
        "complete_endpoint": endpoint,
        "unit_coverage": unit_coverage,
        "core_fields": core,
        "false_rejections": {
            **wilson_interval(false_rejections, len(positive_matches)),
            "errors": false_rejections,
            "rate": false_rejections / len(positive_matches),
        },
        "false_acceptances": {
            **wilson_interval(false_acceptances, len(negative_matches)),
            "errors": false_acceptances,
            "rate": false_acceptances / len(negative_matches),
        },
        "omission_category_errors": dict(category_errors),
        "case_results": results,
        "gates": gates,
        "qualified": all(gates.values()),
    }


def validate_freeze(freeze_path: Path, suite_path: Path) -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (
        freeze.get("schema") != "crane-luna-complete-endpoint-extension-freeze/v1"
        or freeze.get("status") != "FROZEN_BEFORE_ANY_EXTENSION_CALL"
    ):
        raise ValueError("complete-endpoint extension freeze mismatch")
    paths = {
        "suite_sha256": suite_path,
        "prompt_sha256": PROMPT,
        "output_schema_sha256": SCHEMA,
        "caller_source_sha256": CALLER,
        "runner_source_sha256": Path(__file__),
        "suite_builder_sha256": BUILDER,
    }
    for field, path in paths.items():
        if freeze.get(field) != digest_path(path):
            raise ValueError(f"complete-endpoint freeze {field} mismatch")
    return freeze


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, type=Path)
    parser.add_argument("--freeze", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    suite_path = args.suite.resolve(strict=True)
    freeze_path = args.freeze.resolve(strict=True)
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    validate_freeze(freeze_path, suite_path)
    report_path = args.output_root / "heldout-extension.json"
    if report_path.exists():
        raise FileExistsError(f"refusing existing extension result: {report_path}")
    passes = {}
    cache_keys = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, cache_keys[pass_id], failures = run_pass(
            suite["cases"], pass_id, args.output_root
        )
        if failures:
            passes[pass_id] = {
                "qualified": False,
                "call_failures": failures,
                "call_failure_count": len(failures),
            }
        else:
            passes[pass_id] = {
                **score(suite, judgments),
                "call_failures": {},
                "call_failure_count": 0,
            }
    qualified = all(item["qualified"] for item in passes.values())
    report = {
        "schema": "crane-luna-complete-endpoint-extension-result/v1",
        "status": "QUALIFIED" if qualified else "FAILED",
        "suite": suite_path.relative_to(ROOT).as_posix(),
        "suite_sha256": digest_path(suite_path),
        "freeze": freeze_path.relative_to(ROOT).as_posix(),
        "freeze_sha256": digest_path(freeze_path),
        "passes": passes,
        "call_cache_keys": cache_keys,
        "study_scoring_allowed": qualified,
        "confirmatory_study_responses_scored": 0,
        "confirmatory_alpha_consumed": 0.0,
    }
    atomic_write_json(report_path, report)
    print(json.dumps({"status": report["status"]}))


if __name__ == "__main__":
    main()
