#!/usr/bin/env python3
"""Prospective power simulation driven by independent discordant episodes."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
from typing import Any

from analyze_evidence_calibration import exact_mcnemar_p
from evidence_calibration_io import canonical_json_bytes, canonical_sha256


SCHEMA = "crane-evidence-calibration-power-scenarios/v1-development"
OUTPUT_SCHEMA = "crane-evidence-calibration-power-analysis/v1-development"


def simulate(config: dict[str, Any]) -> dict[str, Any]:
    if config.get("schema") != SCHEMA:
        raise ValueError("unsupported power scenario schema")
    rng = random.Random(config["simulation_seed"])
    results = []
    for scenario in config["scenarios"]:
        probabilities = [scenario[key] for key in ("neither", "b2_only_failure", "b4_only_failure", "both")]
        if any(value < 0 for value in probabilities) or abs(sum(probabilities) - 1) > 1e-9:
            raise ValueError("paired outcome probabilities must sum to one")
        for acquired_n in config["acquired_episode_counts"]:
            rejected, valid_counts, discordances, reductions = 0, [], [], []
            for _ in range(config["replicates"]):
                counts = Counter()
                valid = 0
                for _ in range(acquired_n):
                    if rng.random() < scenario["invalid_episode_rate"]:
                        continue
                    valid += 1
                    draw = rng.random()
                    cumulative = 0.0
                    for label, probability in zip(("neither", "b2_only_failure", "b4_only_failure", "both"), probabilities):
                        cumulative += probability
                        if draw <= cumulative:
                            counts[label] += 1
                            break
                p_value = exact_mcnemar_p(counts["b2_only_failure"], counts["b4_only_failure"])
                reduction = (counts["b2_only_failure"] - counts["b4_only_failure"]) / valid if valid else 0
                rejected += p_value <= config["alpha"] and reduction > 0
                valid_counts.append(valid)
                discordances.append(counts["b2_only_failure"] + counts["b4_only_failure"])
                reductions.append(reduction)
            results.append({
                "scenario_id": scenario["scenario_id"], "acquired_episode_count": acquired_n,
                "estimated_power": rejected / config["replicates"],
                "mean_valid_independent_episodes": sum(valid_counts) / len(valid_counts),
                "mean_discordant_independent_episodes": sum(discordances) / len(discordances),
                "mean_b2_minus_b4_risk_difference": sum(reductions) / len(reductions),
            })
    return {
        "schema": OUTPUT_SCHEMA, "config_sha256": canonical_sha256(config),
        "independent_unit": "episode_configuration", "masks_as_independent_samples": False,
        "alpha": config["alpha"], "replicates": config["replicates"], "results": results,
        "interpretation": "Development-only planning sensitivity; not an effect estimate and not alpha spending."
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = simulate(json.loads(args.config.read_text()))
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
