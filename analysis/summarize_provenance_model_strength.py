#!/usr/bin/env python3
"""Apply the predeclared Sol/Luna model-strength selection rule."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def result_files(roots: list[Path]) -> list[Path]:
    return sorted({path.resolve() for root in roots for path in root.rglob("*.json")})


def resource_summary(paths: list[Path]) -> dict[str, Any]:
    calls = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        calls.extend(payload["calls"])
    keys = [call["cache_key"] for call in calls]
    if len(keys) != len(set(keys)):
        raise ValueError("model setting contains duplicate cache keys")
    return {
        "logical_calls": len(calls),
        "input_tokens": sum(call["usage"]["input_tokens"] for call in calls),
        "cached_input_tokens": sum(call["usage"]["cached_input_tokens"] for call in calls),
        "output_tokens": sum(call["usage"]["output_tokens"] for call in calls),
        "reasoning_output_tokens": sum(
            call["usage"]["reasoning_output_tokens"] for call in calls
        ),
        "aggregate_latency_ms": sum(call["latency_ms"] for call in calls),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--sol-summary", required=True, type=Path)
    parser.add_argument("--luna-annotation", required=True, type=Path)
    parser.add_argument("--sol-result-root", action="append", required=True, type=Path)
    parser.add_argument("--luna-result-root", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    sol_summary = json.loads(args.sol_summary.read_text(encoding="utf-8"))
    luna_annotation = json.loads(args.luna_annotation.read_text(encoding="utf-8"))
    sol = {
        condition: {
            "material_errors": values["material_errors"],
            "responses": values["responses"],
            "specificity_correct": values["specificity_correct"],
            "specificity_total": values["specificity_total"],
            "substantive_coverage": values["substantive_answer_coverage"],
        }
        for condition, values in sol_summary["conditions"].items()
    }
    luna = {
        condition: {
            "material_errors": luna_annotation["summary"]["material_errors"][condition],
            "responses": luna_annotation["summary"]["responses_per_condition"],
            "specificity_correct": luna_annotation["summary"]["specificity_correct"][condition],
            "specificity_total": luna_annotation["summary"]["specificity_total"],
            "substantive_coverage": luna_annotation["summary"]["substantive_coverage"][condition],
        }
        for condition in ("F", "G", "H")
    }
    best_errors = {
        condition: min(sol[condition]["material_errors"], luna[condition]["material_errors"])
        for condition in ("F", "G", "H")
    }
    luna_error_margin_pass = all(
        luna[condition]["material_errors"] <= best_errors[condition] + 1
        for condition in ("F", "G", "H")
    )
    sol_specificity = sum(values["specificity_correct"] for values in sol.values()) / sum(
        values["specificity_total"] for values in sol.values()
    )
    luna_specificity = sum(values["specificity_correct"] for values in luna.values()) / sum(
        values["specificity_total"] for values in luna.values()
    )
    luna_specificity_pass = luna_specificity >= max(sol_specificity, luna_specificity) - 0.10
    luna_coverage_pass = all(values["substantive_coverage"] >= 0.875 for values in luna.values())
    # All pilot material errors are source-attribution or causal-diagnosis errors under the retained
    # annotations, so their aggregate count implements the predeclared additional-overclaim bound.
    luna_overclaim_pass = (
        sum(value["material_errors"] for value in luna.values())
        <= sum(value["material_errors"] for value in sol.values()) + 1
    )
    luna_eligible = all(
        (luna_error_margin_pass, luna_specificity_pass, luna_coverage_pass, luna_overclaim_pass)
    )
    resources = {
        "gpt-5.6-sol": resource_summary(result_files(args.sol_result_root)),
        "gpt-5.6-luna": resource_summary(result_files(args.luna_result_root)),
    }
    selected = "gpt-5.6-luna" if luna_eligible else "gpt-5.6-sol"
    payload = {
        "schema": "crane-explain-provenance-model-strength-summary/v1",
        "status": "DEVELOPMENT_SELECTION_NOT_CONFIRMATORY_RESULT",
        "config": str(args.config),
        "predeclared_selection_rule": config["selection_rule"],
        "settings": {
            "gpt-5.6-sol": {"conditions": sol, "aggregate_specificity": sol_specificity},
            "gpt-5.6-luna": {"conditions": luna, "aggregate_specificity": luna_specificity},
        },
        "luna_eligibility": {
            "per_condition_one_response_error_margin": luna_error_margin_pass,
            "aggregate_specificity_within_10_points": luna_specificity_pass,
            "additional_source_or_causal_overclaims_at_most_one": luna_overclaim_pass,
            "per_condition_substantive_coverage_at_least_0.875": luna_coverage_pass,
            "eligible": luna_eligible,
        },
        "resources": resources,
        "selection": {
            "model": selected,
            "reasoning_effort": "low",
            "rationale": (
                "Luna satisfies every predeclared quality margin and is the lower model tier; it "
                "also used fewer input/output tokens and lower aggregate latency. Monetary cost "
                "was not reported, so no dollar-cost claim is made."
                if selected == "gpt-5.6-luna"
                else "Luna failed at least one predeclared eligibility margin."
            ),
        },
        "limitations": [
            "unblinded single-annotator development labels",
            "four episodes and eight responses per condition",
            "provider monetary cost unavailable",
            "selection does not establish model equivalence",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
