#!/usr/bin/env python3
"""Summarize adjudicated diagnostic development labels without inferential claims."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
from typing import Any


CONDITIONS = ("R", "P", "T", "N")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def condition_summary(rows: list[dict[str, Any]], condition: str) -> dict[str, Any]:
    selected = [row for row in rows if row["condition"] == condition]
    if not selected:
        raise ValueError(f"condition {condition} has no rows")
    totals = sum(row["required_units_total"] for row in selected)
    return {
        "responses": len(selected),
        "statistical_clusters": len({row["statistical_cluster_id"] for row in selected}),
        "supported_diagnostic_success_rate": mean(
            [float(row["supported_diagnostic_success"]) for row in selected]
        ),
        "material_error_rate": mean([float(row["material_error"]) for row in selected]),
        "causal_overclaim_rate": mean([float(row["causal_overclaim"]) for row in selected]),
        "unnecessary_abstention_rate": mean(
            [float(row["unnecessary_abstention"]) for row in selected]
        ),
        "qualification_correct_rate": mean(
            [float(row["qualification_correct"]) for row in selected]
        ),
        "required_unit_coverage": (
            sum(row["required_units_correct"] for row in selected) / totals if totals else None
        ),
        "template_fallback_rate": mean(
            [float(row["used_template_fallback"]) for row in selected]
        ),
    }


def paired_cluster_difference(
    rows: list[dict[str, Any]], baseline: str, method: str, field: str
) -> dict[str, Any]:
    by_item: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        item = (
            row["statistical_cluster_id"],
            row["evidence_variant"],
            row["question_id"],
        )
        by_item[item][row["condition"]] = float(row[field])
    incomplete = [
        item for item, values in by_item.items() if baseline not in values or method not in values
    ]
    if incomplete:
        raise ValueError(f"unpaired {baseline}/{method} items: {incomplete}")
    by_cluster: dict[str, list[float]] = defaultdict(list)
    for item, values in by_item.items():
        by_cluster[item[0]].append(values[method] - values[baseline])
    cluster_differences = {
        cluster: sum(values) / len(values) for cluster, values in sorted(by_cluster.items())
    }
    return {
        "baseline": baseline,
        "method": method,
        "field": field,
        "statistical_clusters": len(cluster_differences),
        "difference_method_minus_baseline": mean(list(cluster_differences.values())),
        "cluster_differences": cluster_differences,
        "confidence_interval": None,
        "inference_note": "Development-only descriptive cluster means; no interval, power estimate, or significance test.",
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        raise ValueError("no diagnostic annotation rows")
    present = {row.get("condition") for row in rows}
    if present != set(CONDITIONS):
        raise ValueError(f"expected R/P/T/N, found {sorted(present)}")
    if not all(row.get("diagnosable") is True for row in rows):
        raise ValueError("development primary summary expects diagnosable packet rows")
    response_ids = [row["response_id"] for row in rows]
    if len(response_ids) != len(set(response_ids)):
        raise ValueError("duplicate response IDs")
    clusters = {row["statistical_cluster_id"] for row in rows}
    return {
        "schema": "crane-diagnostic-development-summary/v1",
        "status": "DEVELOPMENT_ONLY_NOT_INFERENTIAL",
        "responses": len(rows),
        "statistical_clusters": len(clusters),
        "evidence_variants": sorted({row["evidence_variant"] for row in rows}),
        "conditions": {
            condition: condition_summary(rows, condition) for condition in CONDITIONS
        },
        "primary_candidate_p_vs_r": paired_cluster_difference(
            rows, "R", "P", "supported_diagnostic_success"
        ),
        "material_error_p_vs_r": paired_cluster_difference(rows, "R", "P", "material_error"),
        "deterministic_t_vs_p": paired_cluster_difference(
            rows, "P", "T", "supported_diagnostic_success"
        ),
        "ablation_n_vs_r": paired_cluster_difference(
            rows, "R", "N", "supported_diagnostic_success"
        ),
        "power_planning_status": "NOT_AUTHORIZED_FROM_TWO_CLUSTERS_ALONE",
        "freeze_status": "NOT_FROZEN",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = read_jsonl(args.annotations.resolve(strict=True))
    result = summarize(rows)
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("refusing to overwrite an existing development summary")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
