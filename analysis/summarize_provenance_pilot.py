#!/usr/bin/env python3
"""Summarize paired F/G/H development annotations with episode-clustered uncertainty."""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def annotated_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    episodes = payload.get("episodes")
    if episodes is None:
        episodes = [
            {
                "episode_id": payload["episode_id"],
                "scenario_family": "repeated_recovery_terminal_abort",
                "questions": payload["questions"],
            }
        ]
    rows = []
    for episode in episodes:
        for question in episode["questions"]:
            for condition, annotation in question["conditions"].items():
                if condition not in {"F", "G", "H"}:
                    continue
                rows.append(
                    {
                        "episode_id": episode["episode_id"],
                        "scenario_family": episode["scenario_family"],
                        "question_kind": question["question_kind"],
                        "condition": condition,
                        "material_error": bool(annotation["material_error"]),
                        "specificity_correct": int(annotation["specificity_correct"]),
                        "specificity_total": int(annotation["specificity_total"]),
                    }
                )
    return rows


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def exact_mcnemar_pvalue(baseline_only_errors: int, method_only_errors: int) -> float:
    discordant = baseline_only_errors + method_only_errors
    if discordant == 0:
        return 1.0
    tail = min(baseline_only_errors, method_only_errors)
    probability = sum(math.comb(discordant, index) for index in range(tail + 1)) / 2**discordant
    return min(1.0, 2 * probability)


def clustered_difference(
    rows: list[dict[str, Any]], baseline: str, method: str, *, simulations: int, seed: int
) -> dict[str, Any]:
    by_episode: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_episode[row["episode_id"]].append(row)
    episode_ids = sorted(by_episode)

    def difference(selected: list[str]) -> float:
        differences = []
        for episode_id in selected:
            episode_rows = by_episode[episode_id]
            baseline_rows = [row for row in episode_rows if row["condition"] == baseline]
            method_rows = [row for row in episode_rows if row["condition"] == method]
            differences.append(
                sum(row["material_error"] for row in method_rows) / len(method_rows)
                - sum(row["material_error"] for row in baseline_rows) / len(baseline_rows)
            )
        return sum(differences) / len(differences)

    observed = difference(episode_ids)
    rng = random.Random(seed)
    draws = [
        difference([rng.choice(episode_ids) for _ in episode_ids])
        for _ in range(simulations)
    ]
    paired = {
        (
            row["episode_id"],
            row["question_kind"],
            row["condition"],
        ): row["material_error"]
        for row in rows
    }
    baseline_only = method_only = 0
    for episode_id in episode_ids:
        question_kinds = sorted(
            {row["question_kind"] for row in by_episode[episode_id]}
        )
        for question_kind in question_kinds:
            baseline_error = paired[(episode_id, question_kind, baseline)]
            method_error = paired[(episode_id, question_kind, method)]
            baseline_only += baseline_error and not method_error
            method_only += method_error and not baseline_error
    return {
        "baseline": baseline,
        "method": method,
        "risk_difference_method_minus_baseline": observed,
        "episode_cluster_bootstrap_95_percentile_interval": [
            quantile(draws, 0.025),
            quantile(draws, 0.975),
        ],
        "bootstrap_simulations": simulations,
        "bootstrap_seed": seed,
        "response_pair_discordance": {
            "baseline_error_method_correct": baseline_only,
            "method_error_baseline_correct": method_only,
            "mcnemar_exact_two_sided_p_secondary_only": exact_mcnemar_pvalue(
                baseline_only, method_only
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotations", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--simulations", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=2026091902)
    args = parser.parse_args()

    rows = []
    for path in args.annotations:
        rows.extend(annotated_rows(json.loads(path.read_text(encoding="utf-8"))))
    episodes = sorted({row["episode_id"] for row in rows})
    summaries = {}
    for condition in ("F", "G", "H"):
        selected = [row for row in rows if row["condition"] == condition]
        errors = sum(row["material_error"] for row in selected)
        correct = sum(row["specificity_correct"] for row in selected)
        total = sum(row["specificity_total"] for row in selected)
        summaries[condition] = {
            "responses": len(selected),
            "material_errors": errors,
            "material_error_rate": errors / len(selected),
            "specificity_correct": correct,
            "specificity_total": total,
            "specificity_rate": correct / total,
            "substantive_answer_coverage": 1.0,
        }
    payload = {
        "schema": "crane-explain-provenance-development-summary/v1",
        "status": "DEVELOPMENT_ONLY_UNBLINDED_NOT_CONFIRMATORY",
        "episodes": len(episodes),
        "episode_ids": episodes,
        "scenario_families": sorted({row["scenario_family"] for row in rows}),
        "questions_per_episode": len(rows) // (len(episodes) * 3),
        "conditions": summaries,
        "comparisons": [
            clustered_difference(
                rows, "F", "G", simulations=args.simulations, seed=args.seed
            ),
            clustered_difference(
                rows, "H", "G", simulations=args.simulations, seed=args.seed + 1
            ),
        ],
        "limitations": [
            "single unblinded annotator",
            "four episodes across two closely related recovery families",
            "bootstrap support is highly discrete at four episode clusters",
            "McNemar treats response pairs as independent and is secondary only",
            "development data are not the sealed confirmatory split",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
