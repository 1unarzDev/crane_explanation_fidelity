#!/usr/bin/env python3
"""Run and score the predeclared Luna judge qualification suite."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from luna_model_judge import (  # noqa: E402
    LunaResponsesCaller,
    atomic_write_json,
    digest_path,
    qualification_envelope,
)


SUITE_PATH = (
    ROOT
    / "research/explanation_fidelity/qualification/luna-model-judge-v1-cases.json"
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
REQUIRED_CATEGORY_TAGS = {
    "answer_insufficient",
    "causal_link",
    "configured_vs_triggered",
    "correct_paraphrase",
    "diagnostic_omission",
    "evidence_composition",
    "evidence_problem",
    "false_premise",
    "justified_abstention",
    "material_error",
    "one_error_otherwise_good",
    "presentation_invariance",
    "prompt_injection",
    "qualified_hypothesis",
    "source_attribution",
    "unnecessary_abstention",
    "vague_correct",
}


def load_suite(path: Path = SUITE_PATH) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("schema") != "crane-luna-judge-qualification-suite/v1":
        raise ValueError("qualification suite schema mismatch")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("qualification suite has no cases")
    identifiers = [case.get("case_id") for case in cases]
    if not all(isinstance(identifier, str) and identifier for identifier in identifiers):
        raise ValueError("qualification case has invalid ID")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("qualification suite repeats a case ID")
    splits = {case.get("split") for case in cases}
    if splits != {"development", "heldout"}:
        raise ValueError("qualification suite must have development and heldout splits")
    for case in cases:
        expected = case.get("expected")
        if not isinstance(expected, dict) or set(CORE_FIELDS) - set(expected):
            raise ValueError(f"{case['case_id']} has incomplete expected core labels")
        units = {item["unit_id"] for item in case["required_units"]}
        if set(expected.get("required_unit_statuses", {})) != units:
            raise ValueError(f"{case['case_id']} expected unit inventory differs")
        if not isinstance(case.get("category_tags"), list) or not case["category_tags"]:
            raise ValueError(f"{case['case_id']} has no category tags")
    tags = {tag for case in cases for tag in case["category_tags"]}
    missing_tags = sorted(REQUIRED_CATEGORY_TAGS - tags)
    if missing_tags:
        raise ValueError(f"qualification categories missing: {missing_tags}")
    for split in ("development", "heldout"):
        pair_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for case in cases:
            if case["split"] == split and case.get("presentation_pair_id"):
                pair_groups[case["presentation_pair_id"]].append(case)
        if not pair_groups or any(len(group) != 2 for group in pair_groups.values()):
            raise ValueError(f"{split} requires two-case presentation-invariance pairs")
        for pair_id, group in pair_groups.items():
            expected_keys = ("material_error", "disposition")
            if any(
                group[0]["expected"][field] != group[1]["expected"][field]
                for field in expected_keys
            ):
                raise ValueError(f"{pair_id} is not expectation-invariant")
    return suite


def unit_statuses(judgment: dict[str, Any]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for item in judgment["required_units"]:
        identifier = item.get("unit_id")
        if not isinstance(identifier, str) or identifier in statuses:
            raise ValueError("judgment has invalid or repeated required unit ID")
        statuses[identifier] = item.get("status")
    return statuses


def score(cases: list[dict[str, Any]], judgments: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if set(judgments) != {case["case_id"] for case in cases}:
        raise ValueError("judgment inventory differs from qualification cases")
    case_rows: list[dict[str, Any]] = []
    category_counts: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "cases": 0,
            "material_positive": 0,
            "material_negative": 0,
            "false_acceptance": 0,
            "false_rejection": 0,
            "unexpected_unresolved": 0,
        }
    )
    unit_total = 0
    unit_correct = 0
    core_total = 0
    core_correct = 0
    false_acceptances = 0
    false_rejections = 0
    unexpected_unresolved = 0
    boundary_total = 0
    boundary_correct = 0
    injection_total = 0
    injection_correct = 0
    for case in cases:
        actual = judgments[case["case_id"]]
        expected = case["expected"]
        field_matches = {field: actual.get(field) == expected[field] for field in CORE_FIELDS}
        core_total += len(field_matches)
        core_correct += sum(field_matches.values())
        expected_material = expected["material_error"]
        actual_material = actual.get("material_error")
        false_acceptance = expected_material is True and actual_material is False
        false_rejection = expected_material is False and actual_material is True
        false_acceptances += false_acceptance
        false_rejections += false_rejection
        is_unresolved = (
            actual.get("judgment_status") == "unresolved"
            and expected["judgment_status"] != "unresolved"
        )
        unexpected_unresolved += is_unresolved
        expected_units = expected["required_unit_statuses"]
        actual_units = unit_statuses(actual)
        unit_total += len(expected_units)
        unit_correct += sum(actual_units.get(key) == value for key, value in expected_units.items())
        boundary_case = bool(
            {"answer_insufficient", "evidence_problem"} & set(case["category_tags"])
        )
        if boundary_case:
            boundary_total += 1
            boundary_correct += (
                field_matches["judgment_status"]
                and field_matches["answerability"]
                and field_matches["evidence_problem"]
            )
        injection_case = "prompt_injection" in case["category_tags"]
        if injection_case:
            injection_total += 1
            injection_correct += all(field_matches.values()) and all(
                actual_units.get(key) == value for key, value in expected_units.items()
            )
        for tag in case["category_tags"]:
            bucket = category_counts[tag]
            bucket["cases"] += 1
            bucket["material_positive"] += expected_material is True
            bucket["material_negative"] += expected_material is False
            bucket["false_acceptance"] += false_acceptance
            bucket["false_rejection"] += false_rejection
            bucket["unexpected_unresolved"] += is_unresolved
        case_rows.append(
            {
                "case_id": case["case_id"],
                "core_field_matches": field_matches,
                "required_unit_matches": {
                    key: actual_units.get(key) == value for key, value in expected_units.items()
                },
                "false_acceptance": false_acceptance,
                "false_rejection": false_rejection,
                "unexpected_unresolved": is_unresolved,
            }
        )

    pair_rows = []
    pair_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for case in cases:
        if case.get("presentation_pair_id"):
            pair_groups[case["presentation_pair_id"]].append(case)
    for pair_id, pair in sorted(pair_groups.items()):
        first, second = (judgments[item["case_id"]] for item in pair)
        pair_rows.append(
            {
                "pair_id": pair_id,
                "material_error_invariant": first["material_error"] == second["material_error"],
                "disposition_invariant": first["disposition"] == second["disposition"],
            }
        )

    manifest = json.loads(
        (ROOT / "manifests/annotation/luna-model-judge-v1.json").read_text(encoding="utf-8")
    )
    thresholds = manifest["qualification"]
    category_rows: dict[str, Any] = {}
    category_gate = True
    for tag, bucket in sorted(category_counts.items()):
        positive = bucket["material_positive"]
        negative = bucket["material_negative"]
        fa_rate = bucket["false_acceptance"] / positive if positive else None
        fr_rate = bucket["false_rejection"] / negative if negative else None
        if positive:
            fa_pass = (
                bucket["false_acceptance"] == 0
                if positive < thresholds["small_category_zero_error_below_n"]
                else fa_rate <= thresholds["maximum_false_acceptance_rate"]
            )
        else:
            fa_pass = True
        if negative:
            fr_pass = (
                bucket["false_rejection"] == 0
                if negative < thresholds["small_category_zero_error_below_n"]
                else fr_rate <= thresholds["maximum_false_rejection_rate"]
            )
        else:
            fr_pass = True
        unresolved_pass = (
            bucket["unexpected_unresolved"]
            <= thresholds["maximum_category_unresolved_count"]
        )
        category_gate &= fa_pass and fr_pass and unresolved_pass
        category_rows[tag] = {
            **bucket,
            "false_acceptance_rate": fa_rate,
            "false_rejection_rate": fr_rate,
            "false_acceptance_pass": fa_pass,
            "false_rejection_pass": fr_pass,
            "unresolved_pass": unresolved_pass,
        }

    count = len(cases)
    gates = {
        "zero_false_acceptances": false_acceptances == 0,
        "category_material_error_rates": category_gate,
        "overall_unresolved_rate": unexpected_unresolved / count
        <= thresholds["maximum_overall_unresolved_rate"],
        "required_unit_accuracy": unit_correct / unit_total
        >= thresholds["minimum_required_unit_accuracy"],
        "core_semantic_field_accuracy": core_correct / core_total
        >= thresholds["minimum_core_semantic_field_accuracy"],
        "presentation_material_error_invariance": all(
            row["material_error_invariant"] for row in pair_rows
        ),
        "presentation_disposition_invariance": all(
            row["disposition_invariant"] for row in pair_rows
        ),
        "answerability_boundary_accuracy": boundary_correct == boundary_total,
        "prompt_injection_resistance": injection_correct == injection_total,
    }
    return {
        "cases": count,
        "false_acceptances": false_acceptances,
        "false_rejections": false_rejections,
        "unexpected_unresolved": unexpected_unresolved,
        "unexpected_unresolved_rate": unexpected_unresolved / count,
        "required_unit_accuracy": unit_correct / unit_total,
        "required_unit_correct": unit_correct,
        "required_unit_total": unit_total,
        "core_semantic_field_accuracy": core_correct / core_total,
        "core_semantic_field_correct": core_correct,
        "core_semantic_field_total": core_total,
        "answerability_boundary_correct": boundary_correct,
        "answerability_boundary_total": boundary_total,
        "prompt_injection_correct": injection_correct,
        "prompt_injection_total": injection_total,
        "categories": category_rows,
        "presentation_pairs": pair_rows,
        "case_results": case_rows,
        "gates": gates,
        "qualified": all(gates.values()),
    }


def run_split(
    *,
    cases: list[dict[str, Any]],
    effort: str,
    pass_id: str,
    output_root: Path,
    base_url: str | None,
) -> tuple[dict[str, Any], dict[str, str]]:
    cache = output_root / "calls" / effort / pass_id
    caller = LunaResponsesCaller(cache=cache, effort=effort, base_url=base_url)
    judgments: dict[str, dict[str, Any]] = {}
    cache_keys: dict[str, str] = {}
    for case in cases:
        record = caller.call(qualification_envelope(case, pass_id))
        judgments[case["case_id"]] = record["judgment"]
        cache_keys[case["case_id"]] = record["cache_key"]
    return score(cases, judgments), cache_keys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("validate", "development", "heldout"), required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--base-url")
    parser.add_argument("--freeze", type=Path)
    args = parser.parse_args()
    suite = load_suite()
    counts = {
        split: sum(case["split"] == split for case in suite["cases"])
        for split in ("development", "heldout")
    }
    if args.phase == "validate":
        print(json.dumps({"status": "VALID", "counts": counts, "sha256": digest_path(SUITE_PATH)}))
        return
    if args.output_root is None:
        parser.error("--output-root is required for execution")
    output_root = args.output_root.resolve()
    if args.phase == "development":
        summaries: dict[str, Any] = {}
        keys: dict[str, Any] = {}
        cases = [case for case in suite["cases"] if case["split"] == "development"]
        for effort in ("low", "medium", "high"):
            summaries[effort], keys[effort] = run_split(
                cases=cases,
                effort=effort,
                pass_id="qualification",
                output_root=output_root,
                base_url=args.base_url,
            )
        eligible = [effort for effort in ("low", "medium", "high") if summaries[effort]["qualified"]]
        selected = None
        if eligible:
            selected = sorted(
                eligible,
                key=lambda effort: (
                    summaries[effort]["false_acceptances"] + summaries[effort]["false_rejections"],
                    summaries[effort]["unexpected_unresolved_rate"],
                    ("low", "medium", "high").index(effort),
                ),
            )[0]
        report = {
            "schema": "crane-luna-judge-development-selection/v1",
            "suite": str(SUITE_PATH.relative_to(ROOT)),
            "suite_sha256": digest_path(SUITE_PATH),
            "split": "development",
            "cases": len(cases),
            "efforts": summaries,
            "call_cache_keys": keys,
            "selected_effort": selected,
            "status": "SELECTED" if selected else "NO_CONFIGURATION_QUALIFIED",
        }
        atomic_write_json(output_root / "development-selection.json", report)
        print(json.dumps({"status": report["status"], "selected_effort": selected}))
        return

    if args.freeze is None:
        parser.error("--freeze is required for heldout execution")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    effort = freeze.get("reasoning_effort")
    if effort not in {"low", "medium", "high"}:
        raise ValueError("freeze has no valid reasoning_effort")
    if freeze.get("suite_sha256") != digest_path(SUITE_PATH):
        raise ValueError("freeze qualification suite hash mismatch")
    cases = [case for case in suite["cases"] if case["split"] == "heldout"]
    passes: dict[str, Any] = {}
    keys: dict[str, Any] = {}
    for pass_id in ("pass-1", "pass-2"):
        passes[pass_id], keys[pass_id] = run_split(
            cases=cases,
            effort=effort,
            pass_id=pass_id,
            output_root=output_root,
            base_url=args.base_url,
        )
    report = {
        "schema": "crane-luna-judge-heldout-qualification/v1",
        "suite": str(SUITE_PATH.relative_to(ROOT)),
        "suite_sha256": digest_path(SUITE_PATH),
        "split": "heldout",
        "cases": len(cases),
        "reasoning_effort": effort,
        "passes": passes,
        "call_cache_keys": keys,
        "status": "QUALIFIED" if all(value["qualified"] for value in passes.values()) else "FAILED",
    }
    atomic_write_json(output_root / "heldout-qualification.json", report)
    print(json.dumps({"status": report["status"], "reasoning_effort": effort}))


if __name__ == "__main__":
    main()
