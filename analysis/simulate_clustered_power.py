#!/usr/bin/env python3
"""Sensitivity power simulation for paired, episode-clustered material-error outcomes.

This is a planning tool, not final inference. It gives each episode equal weight, simulates several
questions within an episode with a shared random effect, and tests the mean within-episode D-A risk
difference using a two-sided 95% normal approximation. Final analysis remains a clustered bootstrap
and, if supported, a mixed-effects model as specified in STUDY_DESIGN.md.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import json
import math
from pathlib import Path
import random
from statistics import NormalDist


NORMAL = NormalDist()
Z_975 = NORMAL.inv_cdf(0.975)


def logistic(value: float) -> float:
    if value >= 0:
        inverse = math.exp(-value)
        return 1.0 / (1.0 + inverse)
    exponential = math.exp(value)
    return exponential / (1.0 + exponential)


@lru_cache(maxsize=None)
def calibrate_intercept(target_risk: float, cluster_sd: float) -> float:
    """Calibrate the logistic intercept to the requested marginal risk deterministically."""
    if not 0.0 < target_risk < 1.0:
        raise ValueError("target risk must be strictly between zero and one")
    calibration_rng = random.Random(20260919)
    effects = [calibration_rng.gauss(0.0, cluster_sd) for _ in range(50_000)]
    low, high = -15.0, 15.0
    for _ in range(60):
        midpoint = (low + high) / 2.0
        marginal = sum(logistic(midpoint + effect) for effect in effects) / len(effects)
        if marginal < target_risk:
            low = midpoint
        else:
            high = midpoint
    return (low + high) / 2.0


def simulate_power(*, episodes: int, questions_per_episode: int, risk_a: float,
                   risk_d: float, cluster_icc: float, paired_latent_correlation: float,
                   simulations: int, seed: int) -> dict:
    if episodes < 3 or questions_per_episode < 1 or simulations < 1:
        raise ValueError("episodes >= 3, questions >= 1, and simulations >= 1 are required")
    if not 0.0 <= cluster_icc < 1.0:
        raise ValueError("cluster ICC must be in [0, 1)")
    if not 0.0 <= paired_latent_correlation < 1.0:
        raise ValueError("paired latent correlation must be in [0, 1)")
    logistic_residual_variance = math.pi * math.pi / 3.0
    cluster_sd = math.sqrt(
        cluster_icc * logistic_residual_variance / max(1e-12, 1.0 - cluster_icc))
    intercept_a = calibrate_intercept(risk_a, cluster_sd)
    intercept_d = calibrate_intercept(risk_d, cluster_sd)
    shared_weight = math.sqrt(paired_latent_correlation)
    residual_weight = math.sqrt(1.0 - paired_latent_correlation)
    rng = random.Random(seed)
    rejected = 0
    estimated_a = 0.0
    estimated_d = 0.0
    estimated_difference = 0.0
    for _ in range(simulations):
        cluster_differences = []
        total_a = total_d = 0
        for _episode in range(episodes):
            effect = rng.gauss(0.0, cluster_sd)
            probability_a = logistic(intercept_a + effect)
            probability_d = logistic(intercept_d + effect)
            threshold_a = NORMAL.inv_cdf(probability_a)
            threshold_d = NORMAL.inv_cdf(probability_d)
            errors_a = errors_d = 0
            for _question in range(questions_per_episode):
                common = rng.gauss(0.0, 1.0)
                latent_a = shared_weight * common + residual_weight * rng.gauss(0.0, 1.0)
                latent_d = shared_weight * common + residual_weight * rng.gauss(0.0, 1.0)
                errors_a += latent_a < threshold_a
                errors_d += latent_d < threshold_d
            total_a += errors_a
            total_d += errors_d
            cluster_differences.append(
                (errors_d - errors_a) / questions_per_episode)
        mean_difference = sum(cluster_differences) / episodes
        if episodes > 1:
            variance = sum(
                (value - mean_difference) ** 2 for value in cluster_differences
            ) / (episodes - 1)
        else:  # guarded above; retained for clarity
            variance = 0.0
        standard_error = math.sqrt(variance / episodes)
        upper_95 = mean_difference + Z_975 * standard_error
        if upper_95 < 0.0:
            rejected += 1
        denominator = episodes * questions_per_episode
        estimated_a += total_a / denominator
        estimated_d += total_d / denominator
        estimated_difference += mean_difference
    return {
        "episodes": episodes,
        "questions_per_episode": questions_per_episode,
        "simulations": simulations,
        "power_two_sided_95_cluster_normal": rejected / simulations,
        "mean_simulated_risk_a": estimated_a / simulations,
        "mean_simulated_risk_d": estimated_d / simulations,
        "mean_simulated_difference_d_minus_a": estimated_difference / simulations,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--simulations", type=int, default=2_000)
    parser.add_argument("--seed", type=int, default=2026091901)
    parser.add_argument("--episodes", type=int, nargs="+", default=[20, 30, 40, 50, 60, 80, 100])
    parser.add_argument("--questions-per-episode", type=int, default=6)
    parser.add_argument("--cluster-icc", type=float, default=0.10)
    parser.add_argument("--paired-latent-correlation", type=float, default=0.50)
    args = parser.parse_args()
    scenarios = [
        {
            "name": "minimum_practical_5pp",
            "risk_a": 0.08,
            "risk_d": 0.03,
            "interpretation": "Pre-specified five-percentage-point absolute risk reduction.",
        },
        {
            "name": "six_episode_descriptive_rates",
            "risk_a": 2 / 37,
            "risk_d": 1 / 37,
            "interpretation": (
                "Sensitivity only; unblinded six-episode rates are too sparse to be estimates."
            ),
        },
    ]
    results = []
    for scenario_index, scenario in enumerate(scenarios):
        rows = []
        for index, episodes in enumerate(args.episodes):
            rows.append(simulate_power(
                episodes=episodes,
                questions_per_episode=args.questions_per_episode,
                risk_a=scenario["risk_a"],
                risk_d=scenario["risk_d"],
                cluster_icc=args.cluster_icc,
                paired_latent_correlation=args.paired_latent_correlation,
                simulations=args.simulations,
                seed=args.seed + scenario_index * 10_000 + index,
            ))
        results.append({**scenario, "results": rows})
    payload = {
        "schema": "crane-explain-clustered-power-sensitivity/v1",
        "status": "DEVELOPMENT_PLANNING_ONLY_NOT_STUDY_FREEZE",
        "seed": args.seed,
        "assumptions": {
            "questions_per_episode": args.questions_per_episode,
            "cluster_icc": args.cluster_icc,
            "paired_latent_correlation": args.paired_latent_correlation,
            "test": (
                "episode-equal-weight mean D-A response risk; two-sided 95% normal interval "
                "entirely below zero"
            ),
            "final_analysis_difference": (
                "Final inference uses episode/scenario clustered bootstrap confidence intervals; "
                "this normal approximation is only a transparent sample-size sensitivity tool."
            ),
        },
        "scenarios": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
