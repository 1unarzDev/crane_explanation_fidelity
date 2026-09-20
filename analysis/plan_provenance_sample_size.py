#!/usr/bin/env python3
"""Development-only clustered power sensitivity for the F-versus-G provenance study."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simulate_clustered_power import simulate_power


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--simulations", type=int, default=5_000)
    parser.add_argument("--seed", type=int, default=2026091903)
    parser.add_argument("--episodes", nargs="+", type=int, default=[20, 30, 40, 50, 60, 80])
    args = parser.parse_args()
    scenarios = (
        {
            "name": "minimum_practical_15pp",
            "risk_f": 0.30,
            "risk_g": 0.15,
            "interpretation": (
                "Planning assumption: a 15-point absolute reduction is the smallest practical "
                "RQ4 effect worth the cost of provenance instrumentation."
            ),
        },
        {
            "name": "four_episode_observed_sensitivity_only",
            "risk_f": 0.50,
            "risk_g": 0.01,
            "interpretation": (
                "The observed G rate was zero; 0.01 avoids treating a four-episode zero as a true "
                "zero risk. This scenario is sensitivity only, not the collection target."
            ),
        },
    )
    results = []
    for scenario_index, scenario in enumerate(scenarios):
        rows = []
        for episode_index, episodes in enumerate(args.episodes):
            rows.append(
                simulate_power(
                    episodes=episodes,
                    questions_per_episode=2,
                    risk_a=scenario["risk_f"],
                    risk_d=scenario["risk_g"],
                    cluster_icc=0.15,
                    paired_latent_correlation=0.50,
                    simulations=args.simulations,
                    seed=args.seed + scenario_index * 10_000 + episode_index,
                )
            )
        results.append({**scenario, "results": rows})
    payload = {
        "schema": "crane-explain-provenance-power-sensitivity/v1",
        "status": "DEVELOPMENT_PLANNING_ONLY_NOT_STUDY_FREEZE",
        "seed": args.seed,
        "assumptions": {
            "questions_per_episode": 2,
            "cluster_icc": 0.15,
            "paired_latent_correlation": 0.50,
            "test": "episode-equal-weight F/G paired risk-difference cluster-normal approximation",
            "warning": (
                "Final inference uses an episode/scenario-clustered bootstrap; this simulation "
                "does not estimate ICC or generalization from four pilot episodes."
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
