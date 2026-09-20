#!/usr/bin/env python3
"""Frozen paired episode-cluster analysis for adjudicated F/G/H annotations."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] * (upper - position) + ordered[upper] * (position - lower)


def exact_mcnemar(baseline_only: int, method_only: int) -> float:
    discordant = baseline_only + method_only
    if not discordant:
        return 1.0
    tail = min(baseline_only, method_only)
    probability = sum(math.comb(discordant, index) for index in range(tail + 1)) / 2**discordant
    return min(1.0, 2 * probability)


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def apply_holm(comparisons: list[dict[str, Any]]) -> None:
    ordered = sorted(
        enumerate(comparisons),
        key=lambda item: item[1]["mcnemar_exact_two_sided_secondary"],
    )
    running = 0.0
    count = len(ordered)
    for rank, (index, comparison_result) in enumerate(ordered):
        adjusted = min(
            1.0,
            (count - rank) * comparison_result["mcnemar_exact_two_sided_secondary"],
        )
        running = max(running, adjusted)
        comparisons[index]["mcnemar_holm_adjusted_secondary"] = running


def episode_mean(rows: list[dict[str, Any]], condition: str, metric: Callable[[dict], float]) -> float:
    grouped: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["condition"] == condition:
            grouped[row["episode_id"]].append(metric(row))
    return sum(sum(values) / len(values) for values in grouped.values()) / len(grouped)


def comparison(
    rows: list[dict[str, Any]], baseline: str, method: str, simulations: int, seed: int
) -> dict[str, Any]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_episode[row["episode_id"]].append(row)
    episode_ids = sorted(
        episode_id
        for episode_id, episode_rows in by_episode.items()
        if {row["condition"] for row in episode_rows}.issuperset({baseline, method})
    )
    if not episode_ids:
        raise ValueError(f"no paired episodes for {baseline} versus {method}")

    def difference(selected: list[str], field: str) -> float:
        values = []
        for episode_id in selected:
            episode_rows = by_episode[episode_id]
            baseline_values = [float(row[field]) for row in episode_rows if row["condition"] == baseline]
            method_values = [float(row[field]) for row in episode_rows if row["condition"] == method]
            values.append(sum(method_values) / len(method_values) - sum(baseline_values) / len(baseline_values))
        return sum(values) / len(values)

    rng = random.Random(seed)
    risk_draws, coverage_draws = [], []
    for _ in range(simulations):
        sample = [rng.choice(episode_ids) for _ in episode_ids]
        risk_draws.append(difference(sample, "material_error"))
        coverage_draws.append(difference(sample, "substantive_answer"))
    paired = {
        (row["episode_id"], row["question_kind"], row["condition"]): bool(row["material_error"])
        for row in rows
    }
    baseline_only = method_only = 0
    for episode_id in episode_ids:
        for question_kind in sorted({row["question_kind"] for row in by_episode[episode_id]}):
            b = paired[(episode_id, question_kind, baseline)]
            m = paired[(episode_id, question_kind, method)]
            baseline_only += int(b and not m)
            method_only += int(m and not b)
    return {
        "baseline": baseline,
        "method": method,
        "risk_difference_method_minus_baseline": difference(episode_ids, "material_error"),
        "risk_difference_cluster_bootstrap_95_percentile_interval": [
            quantile(risk_draws, 0.025), quantile(risk_draws, 0.975)
        ],
        "coverage_difference_method_minus_baseline": difference(episode_ids, "substantive_answer"),
        "coverage_difference_cluster_bootstrap_95_percentile_interval": [
            quantile(coverage_draws, 0.025), quantile(coverage_draws, 0.975)
        ],
        "mcnemar_exact_two_sided_secondary": exact_mcnemar(baseline_only, method_only),
        "discordance": {
            "baseline_error_method_correct": baseline_only,
            "method_error_baseline_correct": method_only,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotations", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--simulations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=2026092001)
    args = parser.parse_args()
    rows = read_jsonl(args.annotations)
    required_conditions = {"F", "G", "H"}
    mechanistic_conditions = {"A", "B", "C", "D", "E"}
    keys = defaultdict(set)
    for row in rows:
        keys[(row["episode_id"], row["question_kind"])].add(row["condition"])
    incomplete = [
        key
        for key, conditions in keys.items()
        if not conditions.issuperset(required_conditions)
        or (conditions.intersection(mechanistic_conditions) not in (set(), mechanistic_conditions))
    ]
    if incomplete:
        raise SystemExit(f"incomplete paired condition rows: {incomplete}")
    present_conditions = sorted({row["condition"] for row in rows})
    conditions = {}
    for condition in present_conditions:
        selected = [row for row in rows if row["condition"] == condition]
        source_references = sum(row["source_reference_count"] for row in selected)
        answerable_source_references = sum(
            row["source_references_total_answerable"] for row in selected
        )
        physical_claims = sum(row["physical_evidence_claim_count"] for row in selected)
        unanswerable = [row for row in selected if not row["requested_conclusion_answerable"]]
        conditions[condition] = {
            "responses": len(selected),
            "material_error_rate_episode_weighted": episode_mean(
                rows, condition, lambda row: float(row["material_error"])
            ),
            "substantive_coverage_episode_weighted": episode_mean(
                rows, condition, lambda row: float(row["substantive_answer"])
            ),
            "answerable_information_coverage": sum(row["answerable_units_correct"] for row in selected)
            / sum(row["answerable_units_total"] for row in selected),
            "full_partial_abstained_nonanswer": {
                label: sum(row["disposition"] == label for row in selected)
                for label in ("full", "partial", "abstained", "nonanswer")
            },
            "causal_overclaim_rate": sum(bool(row["causal_overclaim"]) for row in selected)
            / len(selected),
            "unsupported_claim_rate": ratio(
                sum(row["unsupported_claim_count"] for row in selected),
                sum(row["claim_count"] for row in selected),
            ),
            "source_citation_precision": ratio(
                sum(row["correct_source_reference_count"] for row in selected),
                source_references,
            ),
            "source_citation_recall": ratio(
                sum(row["correct_source_reference_count"] for row in selected),
                answerable_source_references,
            ),
            "physical_evidence_correctness": ratio(
                sum(row["correct_physical_evidence_claim_count"] for row in selected),
                physical_claims,
            ),
            "qualification_correct_rate": sum(
                bool(row["qualification_correct"]) for row in selected
            )
            / len(selected),
            "correct_abstention_rate_on_unanswerable": ratio(
                sum(bool(row["correct_abstention"]) for row in unanswerable),
                len(unanswerable),
            ),
        }
    h_vs_g = comparison(rows, "H", "G", args.simulations, args.seed + 1)
    mechanistic = [
        comparison(rows, baseline, method, args.simulations, args.seed + 2 + index)
        for index, (baseline, method) in enumerate(
            (("A", "B"), ("B", "D"), ("C", "D"), ("D", "G"), ("D", "E"))
        )
        if baseline in present_conditions and method in present_conditions
    ]
    secondary = [h_vs_g, *mechanistic]
    apply_holm(secondary)
    result = {
        "schema": "crane-provenance-final-analysis/v1",
        "status": "SEALED_TEST_ANALYSIS",
        "episodes": len({row["episode_id"] for row in rows}),
        "conditions": conditions,
        "native_risk_coverage_points": [
            {
                "condition": condition,
                "coverage": conditions[condition]["substantive_coverage_episode_weighted"],
                "risk": conditions[condition]["material_error_rate_episode_weighted"],
            }
            for condition in present_conditions
        ],
        "primary_comparison": comparison(rows, "F", "G", args.simulations, args.seed),
        "secondary_comparison_h_vs_g": h_vs_g,
        "mechanistic_secondary_comparisons": mechanistic,
        "bootstrap_simulations": args.simulations,
        "bootstrap_seed": args.seed,
        "multiplicity": "Primary F-vs-G is unadjusted; exact McNemar p-values for all reported secondary comparisons use Holm adjustment; bootstrap effect intervals are descriptive and other analyses are exploratory.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
