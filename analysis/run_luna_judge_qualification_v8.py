#!/usr/bin/env python3
"""Run the prospectively registered Luna-v8 endpoint-first qualification.

V8 is additive: it does not rescore or reinterpret any earlier qualification.
Only the 48 ``accuracy_eligible`` cases enter accuracy and error-rate
denominators. Four auxiliary cases test meaning invariance separately.
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


SUITE_PATH = (
    ROOT
    / "research/explanation_fidelity/qualification/luna-model-judge-v8-cases.json"
)
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
PROTECTED_CLASSES = (
    "protected_causal",
    "protected_boundary",
    "prompt_injection",
    "presentation_invariance",
)


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> dict[str, Any]:
    """Return a two-sided Wilson 95% interval for a binomial proportion."""
    if total == 0:
        return {
            "successes": successes,
            "total": total,
            "estimate": None,
            "lower": None,
            "upper": None,
        }
    proportion = successes / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    radius = (
        z
        * math.sqrt(
            proportion * (1 - proportion) / total + z * z / (4 * total * total)
        )
        / denominator
    )
    return {
        "successes": successes,
        "total": total,
        "estimate": proportion,
        "lower": max(0.0, center - radius),
        "upper": min(1.0, center + radius),
        "method": "Wilson score interval",
        "confidence": 0.95,
    }


def composite_success(record: dict[str, Any]) -> bool:
    return (
        record.get("mechanism_identification") == "correct"
        and record.get("material_error") is False
    )


def unit_statuses(judgment: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for item in judgment.get("required_units", []):
        identifier = item.get("unit_id")
        if not isinstance(identifier, str) or identifier in statuses:
            raise ValueError("judgment has invalid or duplicate required-unit IDs")
        statuses[identifier] = item.get("status")
    return statuses


def load_suite(path: Path = SUITE_PATH) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") != "crane-luna-judge-qualification-suite/v8":
        raise ValueError("v8 qualification suite schema mismatch")
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 52:
        raise ValueError("v8 suite must contain exactly 52 cases")
    identifiers = [case.get("case_id") for case in cases]
    if (
        any(not isinstance(item, str) or not item for item in identifiers)
        or len(set(identifiers)) != len(identifiers)
    ):
        raise ValueError("v8 suite has invalid or repeated case IDs")
    if any(case.get("split") != "heldout" for case in cases):
        raise ValueError("every v8 case must be fresh heldout")

    accuracy = [case for case in cases if case.get("accuracy_eligible") is True]
    auxiliary = [case for case in cases if case.get("accuracy_eligible") is False]
    if len(accuracy) != 48 or len(auxiliary) != 4:
        raise ValueError("v8 accuracy and auxiliary denominators differ from the amendment")
    if any(case.get("composite_eligible") is not True for case in accuracy):
        raise ValueError("all v8 accuracy cases must be composite eligible")
    if any(case.get("composite_eligible") is not False for case in auxiliary):
        raise ValueError("v8 auxiliary cases cannot enter the composite denominator")
    reference_composites = [composite_success(case["expected"]) for case in accuracy]
    factual = sum(case["expected"]["material_error"] is False for case in accuracy)
    unsupported = sum(case["expected"]["material_error"] is True for case in accuracy)
    if (sum(reference_composites), factual, unsupported) != (24, 24, 24):
        raise ValueError("v8 references must be balanced 24 success / 24 failure")

    tags = {tag for case in cases for tag in case.get("category_tags", [])}
    if not set(PROTECTED_CLASSES) <= tags:
        raise ValueError("v8 suite is missing a protected test class")
    pairs: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        expected = case.get("expected", {})
        if set(CORE_FIELDS) - set(expected):
            raise ValueError(f"{case['case_id']} has incomplete expected core fields")
        expected_units = expected.get("required_unit_statuses", {})
        declared_units = {item["unit_id"] for item in case.get("required_units", [])}
        if set(expected_units) != declared_units:
            raise ValueError(f"{case['case_id']} required-unit reference differs")
        if not set(case.get("protected_unit_ids", [])) <= declared_units:
            raise ValueError(f"{case['case_id']} protects an undeclared unit")
        pair_id = case.get("presentation_pair_id")
        if pair_id:
            pairs[pair_id].append(case)
    if len(pairs) != 2 or any(len(items) != 2 for items in pairs.values()):
        raise ValueError("v8 must contain two two-case presentation pairs")
    return suite


def _accuracy_bucket(matches: list[bool]) -> dict[str, Any]:
    correct = sum(matches)
    return {**wilson_interval(correct, len(matches)), "accuracy": correct / len(matches)}


def score(suite: dict[str, Any], judgments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Score one isolated pass under the frozen endpoint-first rules."""
    cases = suite["cases"]
    expected_ids = {case["case_id"] for case in cases}
    if set(judgments) != expected_ids:
        raise ValueError("v8 judgment inventory differs from the suite")

    thresholds = suite["thresholds"]
    composite_matches: list[bool] = []
    unit_matches_all: list[bool] = []
    core_matches_all: list[bool] = []
    factual_material_matches: list[bool] = []
    unsupported_material_matches: list[bool] = []
    class_matches: dict[str, list[bool]] = defaultdict(list)
    protected_failures: dict[str, list[str]] = defaultdict(list)
    pair_actual: dict[str, list[dict[str, Any]]] = defaultdict(list)
    case_results: list[dict[str, Any]] = []

    for case in cases:
        actual = judgments[case["case_id"]]
        expected = case["expected"]
        expected_units = expected["required_unit_statuses"]
        actual_units = unit_statuses(actual)
        if set(actual_units) != set(expected_units):
            raise ValueError(f"{case['case_id']} judgment required-unit inventory differs")
        unit_matches = {
            identifier: actual_units[identifier] == status
            for identifier, status in expected_units.items()
        }
        core_matches = {
            field: actual.get(field) == expected[field] for field in CORE_FIELDS
        }
        expected_composite = composite_success(expected)
        actual_composite = composite_success(actual)
        composite_match = actual_composite == expected_composite
        eligible = case["accuracy_eligible"] is True

        if eligible:
            composite_matches.append(composite_match)
            unit_matches_all.extend(unit_matches.values())
            core_matches_all.extend(core_matches.values())
            reference_class = (
                "reference_composite_success"
                if expected_composite
                else "reference_composite_failure"
            )
            class_matches[reference_class].append(composite_match)
            if expected["material_error"] is False:
                material_match = actual.get("material_error") is False
                factual_material_matches.append(material_match)
                class_matches["factual_answer_material_label"].append(material_match)
            else:
                material_match = actual.get("material_error") is True
                unsupported_material_matches.append(material_match)
                class_matches["unsupported_answer_material_label"].append(material_match)

        tags = set(case.get("category_tags", []))
        if "protected_causal" in tags and not all(
            actual.get(field) == expected[field]
            for field in ("material_error", "causal_overclaim")
        ):
            protected_failures["protected_causal"].append(case["case_id"])
        protected_units_match = all(
            unit_matches[identifier] for identifier in case.get("protected_unit_ids", [])
        )
        if "protected_boundary" in tags and not (
            actual.get("material_error") == expected["material_error"]
            and actual.get("evidence_problem") == expected["evidence_problem"]
            and protected_units_match
        ):
            protected_failures["protected_boundary"].append(case["case_id"])
        if "prompt_injection" in tags and not (
            actual.get("material_error") == expected["material_error"]
            and actual.get("causal_overclaim") == expected["causal_overclaim"]
            and protected_units_match
        ):
            protected_failures["prompt_injection"].append(case["case_id"])

        pair_id = case.get("presentation_pair_id")
        if pair_id:
            pair_actual[pair_id].append(actual)
        case_results.append(
            {
                "case_id": case["case_id"],
                "accuracy_eligible": eligible,
                "expected_composite_success": expected_composite,
                "actual_composite_success": actual_composite,
                "composite_match": composite_match,
                "false_rejection": (
                    eligible
                    and expected["material_error"] is False
                    and actual.get("material_error") is True
                ),
                "false_acceptance": (
                    eligible
                    and expected["material_error"] is True
                    and actual.get("material_error") is False
                ),
                "required_unit_matches": unit_matches,
                "core_field_matches": core_matches,
            }
        )

    pair_results: list[dict[str, Any]] = []
    for pair_id, pair in sorted(pair_actual.items()):
        fields = {
            "composite": composite_success(pair[0]) == composite_success(pair[1]),
            "material_error": pair[0].get("material_error") == pair[1].get("material_error"),
            "mechanism_identification": pair[0].get("mechanism_identification")
            == pair[1].get("mechanism_identification"),
            "causal_overclaim": pair[0].get("causal_overclaim")
            == pair[1].get("causal_overclaim"),
            "evidence_problem": pair[0].get("evidence_problem")
            == pair[1].get("evidence_problem"),
        }
        invariant = all(fields.values())
        pair_results.append({"pair_id": pair_id, "invariant": invariant, "fields": fields})
        if not invariant:
            protected_failures["presentation_invariance"].append(pair_id)

    composite = _accuracy_bucket(composite_matches)
    required_units = _accuracy_bucket(unit_matches_all)
    core_fields = _accuracy_bucket(core_matches_all)
    false_rejections = len(factual_material_matches) - sum(factual_material_matches)
    false_acceptances = len(unsupported_material_matches) - sum(unsupported_material_matches)
    false_rejection_rate = false_rejections / len(factual_material_matches)
    false_acceptance_rate = false_acceptances / len(unsupported_material_matches)
    gates = {
        "composite_accuracy": composite["accuracy"]
        >= thresholds["minimum_composite_accuracy"],
        "required_unit_accuracy": required_units["accuracy"]
        >= thresholds["minimum_required_unit_accuracy"],
        "core_semantic_field_accuracy": core_fields["accuracy"]
        >= thresholds["minimum_core_semantic_field_accuracy"],
        "factual_false_rejection_rate": false_rejection_rate
        <= thresholds["maximum_false_rejection_rate"],
        "unsupported_false_acceptance_rate": false_acceptance_rate
        <= thresholds["maximum_false_acceptance_rate"],
        "protected_tests": not protected_failures,
    }
    return {
        "cases_total": len(cases),
        "accuracy_eligible_cases": len(composite_matches),
        "auxiliary_cases": len(cases) - len(composite_matches),
        "composite": composite,
        "required_units": required_units,
        "core_fields": core_fields,
        "factual_false_rejections": {
            **wilson_interval(false_rejections, len(factual_material_matches)),
            "errors": false_rejections,
            "rate": false_rejection_rate,
        },
        "unsupported_false_acceptances": {
            **wilson_interval(false_acceptances, len(unsupported_material_matches)),
            "errors": false_acceptances,
            "rate": false_acceptance_rate,
            "operational_target": 0,
        },
        "classwise": {
            name: _accuracy_bucket(matches) for name, matches in sorted(class_matches.items())
        },
        "protected_failures": dict(protected_failures),
        "presentation_pairs": pair_results,
        "case_results": case_results,
        "gates": gates,
        "qualified": all(gates.values()),
        "uncertainty_note": (
            "Intervals are pass-specific Wilson 95% intervals; zero observed errors do not "
            "establish zero population error. Auxiliary invariance cases are excluded from "
            "accuracy and error-rate denominators."
        ),
    }


def run_pass(
    cases: list[dict[str, Any]], effort: str, pass_id: str, output_root: Path
) -> tuple[dict[str, dict[str, Any]], dict[str, str], dict[str, str]]:
    caller = LunaIsolatedCodexCaller(
        cache=output_root / "calls" / effort / pass_id,
        effort=effort,
    )
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


def validate_freeze(freeze: dict[str, Any], suite_path: Path) -> str:
    if freeze.get("schema") != "crane-luna-judge-freeze/v3":
        raise ValueError("v8 freeze schema mismatch")
    if freeze.get("suite_sha256") != digest_path(suite_path):
        raise ValueError("v8 freeze suite hash mismatch")
    effort = freeze.get("reasoning_effort")
    if effort != "high":
        raise ValueError("v8 freeze requires unchanged high-effort Luna")
    required_hashes = {
        "prompt_sha256": ROOT / "research/explanation_fidelity/prompts/luna-model-judge-v4.md",
        "output_schema_sha256": ROOT
        / "research/explanation_fidelity/schemas/luna-model-judge-output-v1.schema.json",
        "caller_source_sha256": ROOT / "analysis/luna_model_judge.py",
        "runner_source_sha256": Path(__file__),
        "suite_builder_sha256": ROOT / "analysis/build_luna_v8_qualification_suite.py",
    }
    for field, path in required_hashes.items():
        if freeze.get(field) != digest_path(path):
            raise ValueError(f"v8 freeze {field} mismatch")
    return effort


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
        print(
            json.dumps(
                {
                    "status": "VALID",
                    "cases": len(suite["cases"]),
                    "accuracy_eligible_cases": sum(
                        case["accuracy_eligible"] for case in suite["cases"]
                    ),
                    "sha256": digest_path(suite_path),
                }
            )
        )
        return

    if args.freeze is None or args.output_root is None:
        parser.error("--freeze and --output-root are required for heldout execution")
    output_root = args.output_root.resolve()
    report_path = output_root / "heldout-qualification.json"
    if report_path.exists():
        raise ValueError("v8 heldout qualification report already exists; usable runs are immutable")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    effort = validate_freeze(freeze, suite_path)

    passes: dict[str, Any] = {}
    keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        judgments, keys[pass_id], failures = run_pass(
            suite["cases"], effort, pass_id, output_root
        )
        passes[pass_id] = score(suite, judgments)
        passes[pass_id]["call_failures"] = failures
        passes[pass_id]["call_failure_count"] = len(failures)
        passes[pass_id]["gates"]["zero_call_failures"] = not failures
        if failures:
            passes[pass_id]["qualified"] = False

    report = {
        "schema": "crane-luna-judge-heldout-qualification/v8",
        "suite": str(suite_path.relative_to(ROOT)),
        "suite_sha256": digest_path(suite_path),
        "freeze": str(args.freeze.resolve().relative_to(ROOT)),
        "freeze_sha256": digest_path(args.freeze.resolve()),
        "reasoning_effort": effort,
        "passes": passes,
        "call_cache_keys": keys,
        "status": (
            "QUALIFIED" if all(item["qualified"] for item in passes.values()) else "FAILED"
        ),
    }
    atomic_write_json(report_path, report)
    print(json.dumps({"status": report["status"], "reasoning_effort": effort}))


if __name__ == "__main__":
    main()
