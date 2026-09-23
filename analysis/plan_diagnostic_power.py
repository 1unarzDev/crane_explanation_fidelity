#!/usr/bin/env python3
"""Exact paired-binary power sensitivity for the prospective diagnostic endpoint."""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
from math import comb
from pathlib import Path


@lru_cache(maxsize=None)
def exact_two_sided_binomial_p(successes: int, trials: int) -> float:
    """Two-sided exact sign-test p-value for p=0.5, capped at one."""

    if not 0 <= successes <= trials:
        raise ValueError("successes must be in [0, trials]")
    tail = min(successes, trials - successes)
    probability = 2.0 * sum(comb(trials, value) for value in range(tail + 1)) / 2**trials
    return min(1.0, probability)


def paired_power(
    clusters: int,
    proposed_only_success: float,
    baseline_only_success: float,
    *,
    alpha: float = 0.05,
) -> float:
    """Unconditional exact power for a two-sided paired sign/McNemar test.

    Each independent cluster contributes one predeclared primary binary endpoint. The two
    discordant probabilities are P-success/R-failure and R-success/P-failure. Concordant outcomes
    do not affect the exact test but remain part of the sample-size distribution.
    """

    if clusters < 1:
        raise ValueError("clusters must be positive")
    if proposed_only_success < 0 or baseline_only_success < 0:
        raise ValueError("discordance probabilities must be nonnegative")
    discordance = proposed_only_success + baseline_only_success
    if discordance <= 0 or discordance > 1:
        raise ValueError("discordance probabilities must sum to a value in (0, 1]")
    proposed_given_discordant = proposed_only_success / discordance
    power = 0.0
    for discordant_count in range(clusters + 1):
        probability_discordant_count = (
            comb(clusters, discordant_count)
            * discordance**discordant_count
            * (1.0 - discordance) ** (clusters - discordant_count)
        )
        for proposed_wins in range(discordant_count + 1):
            probability_wins = (
                comb(discordant_count, proposed_wins)
                * proposed_given_discordant**proposed_wins
                * (1.0 - proposed_given_discordant) ** (discordant_count - proposed_wins)
            )
            if exact_two_sided_binomial_p(proposed_wins, discordant_count) < alpha:
                power += probability_discordant_count * probability_wins
    return power


def minimum_clusters(
    proposed_only_success: float,
    baseline_only_success: float,
    target_power: float,
    *,
    alpha: float = 0.05,
    maximum: int = 1000,
) -> int:
    for clusters in range(1, maximum + 1):
        if paired_power(
            clusters,
            proposed_only_success,
            baseline_only_success,
            alpha=alpha,
        ) >= target_power:
            return clusters
    raise ValueError("target power not reached within maximum cluster count")


def build_plan() -> dict:
    scenarios = (
        ("large_effect", 0.30, 0.05),
        ("moderate_effect", 0.25, 0.05),
        ("smallest_practically_meaningful", 0.20, 0.05),
        ("smaller_effect", 0.15, 0.05),
        ("symmetric_discordance", 0.20, 0.10),
    )
    planned_counts = (40, 48, 64, 80, 92, 96)
    rows = []
    for name, proposed_only, baseline_only in scenarios:
        rows.append(
            {
                "scenario": name,
                "proposed_only_success_probability": proposed_only,
                "baseline_only_success_probability": baseline_only,
                "net_supported_diagnostic_success_difference": proposed_only - baseline_only,
                "minimum_clusters_for_80_percent_power": minimum_clusters(
                    proposed_only, baseline_only, 0.80
                ),
                "minimum_clusters_for_90_percent_power": minimum_clusters(
                    proposed_only, baseline_only, 0.90
                ),
                "power_by_independent_primary_cluster_count": {
                    str(count): paired_power(count, proposed_only, baseline_only)
                    for count in planned_counts
                },
            }
        )
    return {
        "schema": "crane-diagnostic-study-power-sensitivity-v1",
        "status": "DESIGN_SENSITIVITY_NOT_OBSERVED_EFFECT_ESTIMATE",
        "test": "two-sided exact paired sign/McNemar test at alpha 0.05",
        "unit": "one predeclared primary binary endpoint per independent scenario instance",
        "target_power": [0.80, 0.90],
        "smallest_practically_meaningful_assumption": {
            "proposed_only_success_probability": 0.20,
            "baseline_only_success_probability": 0.05,
            "net_difference": 0.15,
            "basis": (
                "Prospective design threshold, not an estimate from unblinded development review. "
                "A smaller gain would not justify the specialized computation and verification cost."
            ),
        },
        "sensitivity": rows,
        "limitations": [
            "This exact calculation assumes one independent primary binary endpoint per scenario instance.",
            "Secondary questions and paraphrases do not increase the primary sample size.",
            "The calculation does not account for annotator error; adjudicated labels define the endpoint.",
            "If collection stops below target for deadline/resource reasons, report achieved precision and do not claim planned power.",
            "Observed labels or effect estimates must not be used to change the stopping target."
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_plan()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
