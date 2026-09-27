#!/usr/bin/env python3
"""Run the one-shot Luna M/Q/O/L contract qualification extension."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from luna_model_judge import atomic_write_json, digest_path  # noqa: E402
from run_luna_judge_qualification_v8 import wilson_interval  # noqa: E402
from run_luna_v11_qualification import bucket, run_pass, units  # noqa: E402


PROMPT = ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v5.md"
OUTPUT_SCHEMA = ROOT / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json"
CALLER = ROOT / "analysis/luna_model_judge.py"
BUILDER = ROOT / "analysis/build_contract_complete_luna_qualification.py"


def _endpoint(judgment: dict[str, Any]) -> bool:
    statuses = units(judgment)
    return judgment.get("material_error") is False and all(
        statuses.get(code) == "covered" for code in ("M", "Q", "O", "L")
    )


def score(suite: dict[str, Any], judgments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cases = suite["cases"]
    if set(judgments) != {case["case_id"] for case in cases}:
        raise ValueError("contract qualification judgment inventory mismatch")
    endpoint_matches: list[bool] = []
    unit_matches: list[bool] = []
    core_matches: list[bool] = []
    factual: list[bool] = []
    unsupported: list[bool] = []
    protected_failures: list[str] = []
    results = []
    category_errors: Counter[str] = Counter()
    for case in cases:
        actual = judgments[case["case_id"]]
        expected = case["expected"]
        actual_units = units(actual)
        expected_units = expected["required_unit_statuses"]
        if set(actual_units) != {"M", "Q", "O", "L"}:
            raise ValueError(f"{case['case_id']}: returned M/Q/O/L inventory mismatch")
        unit_match = {
            code: actual_units[code] == expected_units[code] for code in expected_units
        }
        core_match = {
            field: actual.get(field) == expected[field]
            for field in case["scored_core_fields"]
        }
        expected_endpoint = expected["material_error"] is False and all(
            value == "covered" for value in expected_units.values()
        )
        endpoint_match = _endpoint(actual) == expected_endpoint
        endpoint_matches.append(endpoint_match)
        unit_matches.extend(unit_match.values())
        core_matches.extend(core_match.values())
        if expected["material_error"] is False:
            factual.append(actual.get("material_error") is False)
        else:
            unsupported.append(actual.get("material_error") is True)
        if case.get("protected_causal") and not (
            actual.get("material_error") == expected["material_error"]
            and actual.get("causal_overclaim") == expected["causal_overclaim"]
            and actual_units["L"] == expected_units["L"]
        ):
            protected_failures.append(case["case_id"])
        if not endpoint_match or not all(unit_match.values()) or not all(core_match.values()):
            category_errors[case["variant"]] += 1
        results.append(
            {
                "case_id": case["case_id"],
                "variant": case["variant"],
                "endpoint_match": endpoint_match,
                "unit_matches": unit_match,
                "core_matches": core_match,
            }
        )
    false_rejections = len(factual) - sum(factual)
    false_acceptances = len(unsupported) - sum(unsupported)
    thresholds = suite["thresholds"]
    endpoint = bucket(endpoint_matches)
    required_units = bucket(unit_matches)
    core_fields = bucket(core_matches)
    gates = {
        "endpoint_accuracy": endpoint["accuracy"] >= thresholds["minimum_endpoint_accuracy"],
        "required_unit_accuracy": required_units["accuracy"] >= thresholds["minimum_required_unit_accuracy"],
        "core_field_accuracy": core_fields["accuracy"] >= thresholds["minimum_core_field_accuracy"],
        "false_rejection_rate": false_rejections / len(factual) <= thresholds["maximum_false_rejection_rate"],
        "false_acceptance_rate": false_acceptances / len(unsupported) <= thresholds["maximum_false_acceptance_rate"],
        "protected_causal_cases": len(protected_failures) <= thresholds["protected_causal_errors_allowed"],
    }
    return {
        "endpoint": endpoint,
        "required_units": required_units,
        "core_fields": core_fields,
        "false_rejections": {
            **wilson_interval(false_rejections, len(factual)),
            "errors": false_rejections,
            "rate": false_rejections / len(factual),
        },
        "false_acceptances": {
            **wilson_interval(false_acceptances, len(unsupported)),
            "errors": false_acceptances,
            "rate": false_acceptances / len(unsupported),
        },
        "endpoint_changing_errors": sorted(
            case_id for case_id, result in zip((case["case_id"] for case in cases), endpoint_matches)
            if not result
        ),
        "protected_causal_failures": protected_failures,
        "category_errors": dict(category_errors),
        "case_results": results,
        "gates": gates,
        "qualified": all(gates.values()),
    }


def validate_freeze(freeze_path: Path, suite_path: Path) -> dict[str, Any]:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (
        freeze.get("schema") != "crane-contract-complete-luna-qualification-freeze/v1"
        or freeze.get("status") != "FROZEN_BEFORE_ANY_QUALIFICATION_CALL"
    ):
        raise ValueError("contract qualification freeze mismatch")
    expected = {
        "suite_sha256": suite_path,
        "prompt_sha256": PROMPT,
        "output_schema_sha256": OUTPUT_SCHEMA,
        "caller_source_sha256": CALLER,
        "runner_source_sha256": Path(__file__),
        "suite_builder_sha256": BUILDER,
    }
    for field, path in expected.items():
        if freeze.get(field) != digest_path(path):
            raise ValueError(f"contract qualification freeze {field} mismatch")
    if freeze.get("passes") != ["pass-1", "pass-2"]:
        raise ValueError("contract qualification pass inventory mismatch")
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
    report_path = args.output_root / "heldout-qualification.json"
    if report_path.exists():
        raise FileExistsError(f"refusing existing qualification result: {report_path}")
    passes: dict[str, Any] = {}
    cache_keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, cache_keys[pass_id], failures = run_pass(
            suite["cases"], pass_id, args.output_root
        )
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
            passes[pass_id]["qualified"] = all(passes[pass_id]["gates"].values())
    qualified = all(item["qualified"] for item in passes.values())
    report = {
        "schema": "crane-contract-complete-luna-qualification-result/v1",
        "status": "QUALIFIED" if qualified else "FAILED",
        "suite": suite_path.relative_to(ROOT).as_posix(),
        "suite_sha256": digest_path(suite_path),
        "freeze": freeze_path.relative_to(ROOT).as_posix(),
        "freeze_sha256": digest_path(freeze_path),
        "passes": passes,
        "call_cache_keys": cache_keys,
        "study_scoring_allowed": qualified,
        "fresh_pilot_responses_scored": 0,
        "confirmatory_responses_scored": 0,
        "confirmatory_alpha_consumed": 0.0,
    }
    atomic_write_json(report_path, report)
    print(json.dumps({"status": report["status"]}))


if __name__ == "__main__":
    main()
