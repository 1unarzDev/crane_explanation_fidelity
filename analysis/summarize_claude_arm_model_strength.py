#!/usr/bin/env python3
"""Apply the predeclared Claude-arm model-strength selection rule.

This mirrors ``summarize_provenance_model_strength.py``, which implemented the frozen Sol/Luna
rule, with two deliberate differences. Both Claude settings are newly annotated here, so neither is
read from a prior summary; and monetary cost is available from the Claude Code CLI, so the "least
expensive eligible setting" clause is decided on reported cost rather than on tier and tokens
alone.

The rule is read from the predeclared config rather than restated, and eligibility is evaluated
strictly within the Claude arm. The frozen Luna arm is never the reference setting, because this
arm makes no cross-family comparison claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent
CONDITIONS = ("F", "G", "H")


def parse_pairs(items: list[str], flag: str) -> dict[str, Path]:
    pairs: dict[str, Path] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"{flag} expects NAME=PATH, got {item}")
        name, _, value = item.partition("=")
        pairs[name] = Path(value)
    return pairs


def setting_summary(annotation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    summary = annotation["summary"]
    return {
        condition: {
            "material_errors": summary["material_errors"][condition],
            "responses": summary["responses_per_condition"],
            "specificity_correct": summary["specificity_correct"][condition],
            "specificity_total": summary["specificity_total"],
            "substantive_coverage": summary["substantive_coverage"][condition],
        }
        for condition in CONDITIONS
    }


def resource_summary(root: Path) -> dict[str, Any]:
    calls = []
    for path in sorted((WORKSPACE / root).rglob("*.json")):
        calls.extend(json.loads(path.read_text(encoding="utf-8"))["calls"])
    keys = [call["cache_key"] for call in calls]
    if len(keys) != len(set(keys)):
        raise SystemExit(f"setting at {root} contains duplicate cache keys")
    costs = [call.get("cost_usd") for call in calls]
    return {
        "logical_calls": len(calls),
        "input_tokens": sum(call["usage"]["input_tokens"] for call in calls),
        "cached_input_tokens": sum(call["usage"]["cached_input_tokens"] for call in calls),
        "output_tokens": sum(call["usage"]["output_tokens"] for call in calls),
        "reasoning_output_tokens": sum(call["usage"]["reasoning_output_tokens"] for call in calls),
        "aggregate_latency_ms": sum(call["latency_ms"] for call in calls),
        "aggregate_cost_usd": sum(costs) if all(cost is not None for cost in costs) else None,
        "read_only_workspace_verified": all(
            call.get("workspace_unmodified", False) for call in calls
        ),
    }


def aggregate_specificity(setting: dict[str, dict[str, Any]]) -> float:
    return sum(value["specificity_correct"] for value in setting.values()) / sum(
        value["specificity_total"] for value in setting.values()
    )


def eligibility(
    candidate: dict[str, dict[str, Any]],
    settings: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Evaluate the four predeclared margins against the best tested Claude setting."""

    best_errors = {
        condition: min(setting[condition]["material_errors"] for setting in settings.values())
        for condition in CONDITIONS
    }
    best_specificity = max(aggregate_specificity(setting) for setting in settings.values())
    least_errors = min(
        sum(value["material_errors"] for value in setting.values())
        for setting in settings.values()
    )
    checks = {
        "per_condition_one_response_error_margin": all(
            candidate[condition]["material_errors"] <= best_errors[condition] + 1
            for condition in CONDITIONS
        ),
        "aggregate_specificity_within_10_points": (
            aggregate_specificity(candidate) >= best_specificity - 0.10
        ),
        "additional_source_or_causal_overclaims_at_most_one": (
            sum(value["material_errors"] for value in candidate.values()) <= least_errors + 1
        ),
        "per_condition_substantive_coverage_at_least_0.875": all(
            value["substantive_coverage"] >= 0.875 for value in candidate.values()
        ),
    }
    return {**checks, "eligible": all(checks.values())}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--annotation", action="append", required=True, metavar="MODEL=PATH")
    parser.add_argument("--result-root", action="append", required=True, metavar="MODEL=ROOT")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    config = json.loads((WORKSPACE / args.config).read_text(encoding="utf-8"))
    annotations = parse_pairs(args.annotation, "--annotation")
    roots = parse_pairs(args.result_root, "--result-root")
    declared = {item["model"]: item for item in config["settings"]}
    if set(annotations) != set(declared) or set(roots) != set(declared):
        raise SystemExit(
            "annotations and result roots must cover exactly the predeclared settings: "
            f"{sorted(declared)}"
        )

    settings = {
        model: setting_summary(json.loads((WORKSPACE / path).read_text(encoding="utf-8")))
        for model, path in annotations.items()
    }
    resources = {model: resource_summary(root) for model, root in roots.items()}
    eligible = {model: eligibility(setting, settings) for model, setting in settings.items()}

    fallback = config["selection_rule"]["tie_or_ineligible"].split()[1]
    candidates = [model for model, verdict in eligible.items() if verdict["eligible"]]
    costed = [
        model for model in candidates if resources[model]["aggregate_cost_usd"] is not None
    ]
    if len(costed) == len(candidates) and candidates:
        selected = min(candidates, key=lambda model: resources[model]["aggregate_cost_usd"])
        basis = "reported provider monetary cost"
    elif candidates:
        selected = min(
            candidates,
            key=lambda model: (
                resources[model]["input_tokens"] + resources[model]["output_tokens"]
            ),
        )
        basis = "measured token use, because monetary cost was unavailable"
    else:
        selected = fallback
        basis = "predeclared fallback, because no setting met every margin"

    payload = {
        "schema": "crane-explain-claude-arm-model-strength-summary/v1",
        "status": "DEVELOPMENT_SELECTION_NOT_CONFIRMATORY_RESULT",
        "arm": config["arm"],
        "config": str(args.config),
        "predeclared_selection_rule": config["selection_rule"],
        "settings": {
            model: {
                "conditions": setting,
                "aggregate_specificity": aggregate_specificity(setting),
                "eligibility": eligible[model],
            }
            for model, setting in settings.items()
        },
        "resources": resources,
        "selection": {
            "model": selected,
            "reasoning_effort": "low",
            "selection_basis": basis,
            "eligible_settings": sorted(candidates),
        },
        "limitations": [
            "unblinded single-annotator development labels",
            "the single annotator is an automated assistant session, not an independent human",
            "four episodes and eight responses per condition",
            "selection does not establish model equivalence, within or across families",
            "this selects a configuration for a secondary arm and is not evidence for RQ4",
        ],
    }
    output_path = WORKSPACE / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
