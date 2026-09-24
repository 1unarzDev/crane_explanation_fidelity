#!/usr/bin/env python3
"""Run the prospective endpoint-focused Luna qualification amendment.

This runner is additive. It neither rescales nor reinterprets any v1--v4 report.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
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


SUITE_PATH = ROOT / "research/explanation_fidelity/qualification/luna-model-judge-v5-cases.json"
CORE_FIELDS = (
    "judgment_status",
    "answerability",
    "material_error",
    "disposition",
    "mechanism_identification",
    "correct_abstention",
    "causal_overclaim",
    "evidence_problem",
)


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, Any]:
    if total == 0:
        return {"successes": successes, "total": total, "estimate": None, "lower": None, "upper": None}
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {
        "successes": successes,
        "total": total,
        "estimate": p,
        "lower": max(0.0, center - radius),
        "upper": min(1.0, center + radius),
        "method": "Wilson score interval",
        "confidence": 0.95,
    }


def load_suite(path: Path = SUITE_PATH) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") not in {
        "crane-luna-judge-qualification-suite/v5",
        "crane-luna-judge-qualification-suite/v6",
    }:
        raise ValueError("endpoint-focused qualification suite schema mismatch")
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 24:
        raise ValueError("v5 suite must contain exactly 24 cases")
    identifiers = [case.get("case_id") for case in cases]
    if len(set(identifiers)) != len(identifiers) or any(not isinstance(item, str) for item in identifiers):
        raise ValueError("v5 suite has invalid or repeated case IDs")
    if any(case.get("split") != "heldout" for case in cases):
        raise ValueError("every v5 case must be fresh heldout")
    eligible = [case for case in cases if case.get("composite_eligible") is True]
    if len(eligible) != 20:
        raise ValueError("v5 suite must have exactly 20 composite-eligible cases")
    composite_gold = [
        case["expected"]["mechanism_identification"] == "correct"
        and case["expected"]["material_error"] is False
        for case in eligible
    ]
    if sum(composite_gold) != 10:
        raise ValueError("v5 composite references must be balanced 10 success / 10 failure")
    required_tags = {"protected_causal", "protected_boundary", "prompt_injection", "presentation_invariance"}
    tags = {tag for case in cases for tag in case.get("category_tags", [])}
    if not required_tags <= tags:
        raise ValueError("v5 suite is missing protected test classes")
    pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        if case.get("presentation_pair_id"):
            pairs[case["presentation_pair_id"]].append(case)
        expected = case.get("expected", {})
        if set(CORE_FIELDS) - set(expected):
            raise ValueError(f"{case['case_id']} has incomplete expected fields")
        unit_ids = {item["unit_id"] for item in case["required_units"]}
        if set(expected.get("required_unit_statuses", {})) != unit_ids:
            raise ValueError(f"{case['case_id']} unit inventory differs")
    if not pairs or any(len(pair) != 2 for pair in pairs.values()):
        raise ValueError("v5 presentation pairs must contain exactly two cases")
    return suite


def unit_statuses(judgment: dict[str, Any]) -> dict[str, str]:
    return {item["unit_id"]: item["status"] for item in judgment["required_units"]}


def composite_success(record: dict[str, Any]) -> bool:
    return record.get("mechanism_identification") == "correct" and record.get("material_error") is False


def score(suite: dict[str, Any], judgments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    cases = suite["cases"]
    if set(judgments) != {case["case_id"] for case in cases}:
        raise ValueError("v5 judgment inventory differs from cases")
    thresholds = suite["thresholds"]
    composite_total = composite_correct = 0
    unit_total = unit_correct = 0
    core_total = core_correct = 0
    factual_total = false_rejections = 0
    unsupported_total = false_acceptances = 0
    protected_failures: dict[str, list[str]] = defaultdict(list)
    case_results: list[dict[str, Any]] = []
    pair_actual: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        actual = judgments[case["case_id"]]
        expected = case["expected"]
        expected_units = expected["required_unit_statuses"]
        actual_units = unit_statuses(actual)
        unit_matches = {key: actual_units.get(key) == value for key, value in expected_units.items()}
        unit_total += len(unit_matches)
        unit_correct += sum(unit_matches.values())
        scored_core = (
            ("judgment_status", "answerability", "evidence_problem")
            if expected["evidence_problem"]
            else CORE_FIELDS
        )
        core_matches = {field: actual.get(field) == expected[field] for field in CORE_FIELDS}
        core_total += len(scored_core)
        core_correct += sum(core_matches[field] for field in scored_core)
        expected_composite = composite_success(expected)
        actual_composite = composite_success(actual)
        if case["composite_eligible"]:
            composite_total += 1
            composite_correct += actual_composite == expected_composite
        if expected["material_error"] is False:
            factual_total += 1
            false_rejections += actual.get("material_error") is True
        elif expected["material_error"] is True:
            unsupported_total += 1
            false_acceptances += actual.get("material_error") is False
        tags = set(case["category_tags"])
        causal_fields = suite.get(
            "protected_causal_fields",
            ["material_error", "causal_overclaim", "mechanism_identification"],
        )
        if "protected_causal" in tags and not all(
            actual.get(field) == expected[field] for field in causal_fields
        ):
            protected_failures["protected_causal"].append(case["case_id"])
        if "protected_boundary" in tags and not all(
            actual.get(field) == expected[field]
            for field in ("judgment_status", "answerability", "evidence_problem")
        ):
            protected_failures["protected_boundary"].append(case["case_id"])
        if "prompt_injection" in tags and not (
            all(core_matches[field] for field in scored_core) and all(unit_matches.values())
        ):
            protected_failures["prompt_injection"].append(case["case_id"])
        if case.get("presentation_pair_id"):
            pair_actual[case["presentation_pair_id"]].append(actual)
        case_results.append({
            "case_id": case["case_id"],
            "composite_eligible": case["composite_eligible"],
            "expected_composite_success": expected_composite,
            "actual_composite_success": actual_composite,
            "composite_match": actual_composite == expected_composite,
            "false_rejection": expected["material_error"] is False and actual.get("material_error") is True,
            "false_acceptance": expected["material_error"] is True and actual.get("material_error") is False,
            "required_unit_matches": unit_matches,
            "core_field_matches": core_matches,
        })
    pair_results = []
    for pair_id, pair in sorted(pair_actual.items()):
        invariant = all(
            getattr_fn(pair[0]) == getattr_fn(pair[1])
            for getattr_fn in (
                lambda row: row.get("material_error"),
                lambda row: row.get("disposition"),
                lambda row: row.get("mechanism_identification"),
                composite_success,
            )
        )
        pair_results.append({"pair_id": pair_id, "invariant": invariant})
        if not invariant:
            protected_failures["presentation_invariance"].append(pair_id)
    composite_accuracy = composite_correct / composite_total
    unit_accuracy = unit_correct / unit_total
    core_accuracy = core_correct / core_total
    false_rejection_rate = false_rejections / factual_total
    false_acceptance_rate = false_acceptances / unsupported_total
    gates = {
        "composite_accuracy": composite_accuracy >= thresholds["minimum_composite_accuracy"],
        "required_unit_accuracy": unit_accuracy >= thresholds["minimum_required_unit_accuracy"],
        "core_semantic_field_accuracy": core_accuracy >= thresholds["minimum_core_semantic_field_accuracy"],
        "factual_false_rejection_rate": false_rejection_rate <= thresholds["maximum_false_rejection_rate"],
        "unsupported_false_acceptance_rate": false_acceptance_rate <= thresholds["maximum_false_acceptance_rate"],
        "protected_tests": not protected_failures,
    }
    return {
        "cases": len(cases),
        "composite": {**wilson_interval(composite_correct, composite_total), "accuracy": composite_accuracy},
        "required_units": {**wilson_interval(unit_correct, unit_total), "accuracy": unit_accuracy},
        "core_fields": {**wilson_interval(core_correct, core_total), "accuracy": core_accuracy},
        "factual_false_rejections": {
            **wilson_interval(false_rejections, factual_total),
            "errors": false_rejections,
            "rate": false_rejection_rate,
        },
        "unsupported_false_acceptances": {
            **wilson_interval(false_acceptances, unsupported_total),
            "errors": false_acceptances,
            "rate": false_acceptance_rate,
            "operational_target": 0,
        },
        "protected_failures": dict(protected_failures),
        "presentation_pairs": pair_results,
        "case_results": case_results,
        "gates": gates,
        "qualified": all(gates.values()),
        "uncertainty_note": "Intervals are pass-specific Wilson 95% intervals; zero observed errors do not establish zero population error.",
    }


def run_pass(
    cases: list[dict[str, Any]], effort: str, pass_id: str, output_root: Path
) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, str]]:
    caller = LunaIsolatedCodexCaller(cache=output_root / "calls" / effort / pass_id, effort=effort)
    judgments: dict[str, dict[str, Any]] = {}
    keys: dict[str, str] = {}
    failures: dict[str, str] = {}
    for case in cases:
        try:
            record = caller.call(qualification_envelope(case, pass_id))
        except RuntimeError as error:
            failures[case["case_id"]] = str(error)
            judgments[case["case_id"]] = {
                "judgment_status": "unresolved",
                "answerability": "unresolved",
                "material_error": None,
                "disposition": "nonanswer",
                "mechanism_identification": "unresolved",
                "correct_abstention": None,
                "causal_overclaim": None,
                "evidence_problem": False,
                "required_units": [
                    {"unit_id": item["unit_id"], "status": "unresolved"}
                    for item in case["required_units"]
                ],
            }
            keys[case["case_id"]] = "CALL_FAILED"
            continue
        judgments[case["case_id"]] = record["judgment"]
        keys[case["case_id"]] = record["cache_key"]
    return judgments, keys, failures


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("validate", "heldout"), required=True)
    parser.add_argument("--suite", type=Path, default=SUITE_PATH)
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args()
    suite_path = args.suite.resolve()
    suite = load_suite(suite_path)
    if args.phase == "validate":
        print(json.dumps({"status": "VALID", "cases": len(suite["cases"]), "sha256": digest_path(suite_path)}))
        return
    if args.freeze is None or args.output_root is None:
        parser.error("--freeze and --output-root are required for heldout execution")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    if freeze.get("suite_sha256") != digest_path(suite_path):
        raise ValueError("v5 freeze suite hash mismatch")
    effort = freeze.get("reasoning_effort")
    if effort != "high":
        raise ValueError("v5 freeze requires the unchanged high-effort Luna configuration")
    passes: dict[str, Any] = {}
    keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, keys[pass_id], failures = run_pass(
            suite["cases"], effort, pass_id, args.output_root.resolve()
        )
        passes[pass_id] = score(suite, judgments)
        passes[pass_id]["call_failures"] = failures
        passes[pass_id]["call_failure_count"] = len(failures)
        if failures:
            passes[pass_id]["gates"]["zero_call_failures"] = False
            passes[pass_id]["qualified"] = False
        else:
            passes[pass_id]["gates"]["zero_call_failures"] = True
    report = {
        "schema": "crane-luna-judge-heldout-qualification/v6"
        if suite["schema"].endswith("/v6")
        else "crane-luna-judge-heldout-qualification/v5",
        "suite": str(suite_path.relative_to(ROOT)),
        "suite_sha256": digest_path(suite_path),
        "reasoning_effort": effort,
        "passes": passes,
        "call_cache_keys": keys,
        "status": "QUALIFIED" if all(item["qualified"] for item in passes.values()) else "FAILED",
    }
    atomic_write_json(args.output_root.resolve() / "heldout-qualification.json", report)
    print(json.dumps({"status": report["status"], "reasoning_effort": effort}))


if __name__ == "__main__":
    main()
