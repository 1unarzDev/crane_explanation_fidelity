#!/usr/bin/env python3
"""Development-only paired B0--B4 analysis; P11 must bind its exact plan."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from analyze_evidence_calibration import INPUT_SCHEMA, analyze
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


METHODS = {"B0", "B1", "B2", "B3", "B4"}
SECONDARY = ("B0", "B1", "B3")
OUTPUT_SCHEMA = "crane-evidence-calibration-five-method-analysis/v1-development"


def holm_adjusted_p(values: dict[str, float]) -> dict[str, float]:
    """Step-down familywise adjustment, retaining every declared contrast."""
    ordered = sorted(values, key=lambda method: (values[method], method))
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, method in enumerate(ordered):
        running = max(running, min(1.0, (len(ordered) - rank) * values[method]))
        adjusted[method] = running
    return adjusted


def _project_pair(data: dict[str, Any], comparator: str) -> dict[str, Any]:
    projected = copy.deepcopy(data)
    for episode in projected["episodes"]:
        for condition in episode["conditions"]:
            methods = condition["methods"]
            if set(methods) != METHODS:
                raise ValueError("every condition must contain exactly B0, B1, B2, B3, and B4")
            condition["methods"] = {"B2": methods[comparator], "B4": methods["B4"]}
    return projected


def analyze_five_methods(data: dict[str, Any], plan: dict[str, Any],
                         declaration: dict[str, Any]) -> dict[str, Any]:
    if data.get("schema") != INPUT_SCHEMA:
        raise ValueError("unsupported adjudicated-result schema")
    if (declaration.get("schema") != "crane-evidence-calibration-five-method-comparisons/v1-development"
            or declaration.get("methods") != ["B0", "B1", "B2", "B3", "B4"]
            or declaration.get("secondary_method_comparisons", {}).get("comparators") != list(SECONDARY)
            or declaration.get("primary_comparison", {}).get("comparator") != "B2"):
        raise ValueError("five-method comparison declaration is not the bound candidate")
    if declaration.get("confirmatory_semantic_output_authorized") is not False:
        raise ValueError("development comparison declaration cannot authorize confirmation")

    primary = analyze(_project_pair(data, "B2"), plan)
    secondary: dict[str, Any] = {}
    raw_p: dict[str, float] = {}
    for comparator in SECONDARY:
        result = analyze(_project_pair(data, comparator), plan)
        paired = result["paired_primary"]
        raw_p[comparator] = paired["exact_mcnemar_two_sided_p"]
        secondary[comparator] = {
            "comparator": comparator,
            "treatment": "B4",
            "independent_paired_episode_count": result["independent_episode_count"],
            "comparator_failures": result["method_metrics"]["B2"]["primary_failures"],
            "b4_failures": result["method_metrics"]["B4"]["primary_failures"],
            "neither_failure": paired["neither_failure"],
            "comparator_only_failure": paired["b2_only_failure"],
            "b4_only_failure": paired["b4_only_failure"],
            "both_failure": paired["both_failure"],
            "b4_minus_comparator_risk_difference": paired["b4_minus_b2_risk_difference"],
            "whole_episode_bootstrap_confidence_interval": paired["whole_episode_bootstrap_confidence_interval"],
            "exact_mcnemar_two_sided_p": raw_p[comparator],
            "nonprimary_family_descriptives": result["nonprimary_family_descriptives"],
        }
    adjusted = holm_adjusted_p(raw_p)
    for comparator in SECONDARY:
        secondary[comparator]["holm_adjusted_p_across_three_method_contrasts"] = adjusted[comparator]
    return {
        "schema": OUTPUT_SCHEMA,
        "disposition": "DEVELOPMENT_ONLY_NOT_P11_FROZEN",
        "input_sha256": canonical_sha256(data),
        "analysis_plan_sha256": canonical_sha256(plan),
        "comparison_declaration_sha256": canonical_sha256(declaration),
        "independent_unit": "episode_configuration",
        "primary_b2_vs_b4": primary,
        "secondary_method_family": secondary,
        "secondary_multiplicity": "HOLM_ACROSS_B4_VS_B0_B1_B3",
        "secondary_discovery_alpha_allocated": 0.0,
        "inconclusive_results_retained": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--comparison-declaration", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze_five_methods(json.loads(args.results.read_text()),
                                  json.loads(args.plan.read_text()),
                                  json.loads(args.comparison_declaration.read_text()))
    args.output.write_bytes(canonical_json_bytes(result) + b"\n")


if __name__ == "__main__":
    main()
