#!/usr/bin/env python3
"""Reproducible QA and budgeting simulations for the prospective sequential design.

The mathematical validity of the monitor comes from its nonnegative-supermartingale proof.
These simulations check implementation behavior and estimate attainable stopping probabilities;
they are not a substitute for that proof and are never study observations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from sequential_diagnostic_monitor import protocol_sha256, validate_protocol


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = (
    ROOT
    / "research/explanation_fidelity/experiment_configs/prospective/"
    "diagnostic-sequential-protocol-v2.json"
)


def _paired_draw(
    rng: np.random.Generator,
    count: int,
    plus_probability: float,
    minus_probability: float,
) -> np.ndarray:
    if min(plus_probability, minus_probability) < 0.0:
        raise ValueError("paired discordance probabilities must be nonnegative")
    if plus_probability + minus_probability > 1.0:
        raise ValueError("paired discordance probabilities cannot exceed one")
    uniform = rng.random(count)
    return np.where(
        uniform < plus_probability,
        1.0,
        np.where(uniform < plus_probability + minus_probability, -1.0, 0.0),
    )


def _update_log_capital(
    log_capital: np.ndarray,
    values: np.ndarray,
    null_mean: float,
    fractions: np.ndarray,
    active: np.ndarray | None = None,
) -> None:
    bets = fractions / (1.0 + null_mean)
    increments = np.log1p((values[:, None] - null_mean) * bets[None, :])
    if active is not None:
        increments *= active[:, None]
    log_capital += increments


def _log_mixture(log_capital: np.ndarray) -> np.ndarray:
    maximum = np.max(log_capital, axis=1)
    return maximum + np.log(
        np.mean(np.exp(log_capital - maximum[:, None]), axis=1)
    )


def _wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    estimate = successes / total
    denominator = 1.0 + z * z / total
    center = (estimate + z * z / (2.0 * total)) / denominator
    half_width = (
        z
        * math.sqrt(
            estimate * (1.0 - estimate) / total + z * z / (4.0 * total * total)
        )
        / denominator
    )
    return [max(0.0, center - half_width), min(1.0, center + half_width)]


def simulate_endpoint_crossing(
    *,
    replicates: int,
    observations: int,
    plus_probability: float,
    minus_probability: float,
    null_mean: float,
    alpha: float,
    fractions: tuple[float, ...],
    seed: int,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    fraction_array = np.asarray(fractions, dtype=float)
    log_capital = np.zeros((replicates, len(fractions)), dtype=float)
    crossed = np.zeros(replicates, dtype=bool)
    first_crossing = np.zeros(replicates, dtype=np.int32)
    threshold = math.log(1.0 / alpha)
    for index in range(observations):
        values = _paired_draw(
            rng, replicates, plus_probability, minus_probability
        )
        _update_log_capital(
            log_capital, values, null_mean, fraction_array
        )
        newly_crossed = (~crossed) & (_log_mixture(log_capital) >= threshold)
        first_crossing[newly_crossed] = index + 1
        crossed |= newly_crossed
    successes = int(np.sum(crossed))
    positive = first_crossing[first_crossing > 0]
    return {
        "replicates": replicates,
        "observations": observations,
        "plus_probability": plus_probability,
        "minus_probability": minus_probability,
        "true_mean": plus_probability - minus_probability,
        "null_mean": null_mean,
        "alpha": alpha,
        "crossings": successes,
        "crossing_rate": successes / replicates,
        "crossing_rate_wilson_95": _wilson_interval(successes, replicates),
        "first_crossing_quantiles": (
            {
                "q10": float(np.quantile(positive, 0.1)),
                "q50": float(np.quantile(positive, 0.5)),
                "q90": float(np.quantile(positive, 0.9)),
            }
            if len(positive)
            else None
        ),
    }


def simulate_joint_campaign(
    *,
    protocol: dict[str, Any],
    replicates: int,
    seed: int,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    """Simulate simultaneous current-look success under the frozen 80/20 mixture."""

    rng = np.random.default_rng(seed)
    fractions = np.asarray(protocol["analysis"]["betting_fractions"], dtype=float)
    allocation = next(
        item
        for item in protocol["error_budget_ledger"]["allocations"]
        if item["allocation_id"] == "candidate-v1-confirmation"
    )
    alpha = float(allocation["alpha"])
    threshold = math.log(1.0 / alpha)
    maximum = int(protocol["stopping_rule"]["maximum_total_clusters"])
    floors = protocol["stopping_rule"]
    looks = sorted(
        set(int(item) for item in floors["futility_review_cluster_counts"])
        | {maximum}
    )
    capital = {
        key: np.zeros((replicates, len(fractions)), dtype=float)
        for key in ("primary", "material", "coverage", "ambiguity")
    }
    diagnosable_counts = np.zeros(replicates, dtype=np.int32)
    ambiguous_counts = np.zeros(replicates, dtype=np.int32)
    success_ever = np.zeros(replicates, dtype=bool)
    success_by_look: dict[str, float] = {}

    for index in range(maximum):
        ambiguous = rng.random(replicates) < 0.2
        diagnosable = ~ambiguous
        diagnosable_counts += diagnosable
        ambiguous_counts += ambiguous

        primary = _paired_draw(rng, replicates, **scenario["primary"])
        material = _paired_draw(rng, replicates, **scenario["material"])
        coverage = _paired_draw(rng, replicates, **scenario["coverage"])
        ambiguity = _paired_draw(rng, replicates, **scenario["ambiguity"])

        _update_log_capital(
            capital["primary"], primary, 0.15, fractions, diagnosable
        )
        # Material is specified in the natural P-minus-R error orientation. Negating it
        # converts the upper-bound guardrail into the monitor's lower-bound test.
        _update_log_capital(
            capital["material"], -material, -0.02, fractions
        )
        _update_log_capital(capital["coverage"], coverage, -0.05, fractions)
        _update_log_capital(
            capital["ambiguity"], ambiguity, -0.05, fractions, ambiguous
        )

        total = index + 1
        floors_met = (
            (total >= int(floors["minimum_total_clusters_before_success"]))
            & (
                diagnosable_counts
                >= int(floors["minimum_diagnosable_clusters_before_success"])
            )
            & (
                ambiguous_counts
                >= int(floors["minimum_ambiguous_clusters_before_success"])
            )
        )
        all_gates = floors_met.copy()
        for value in capital.values():
            all_gates &= _log_mixture(value) >= threshold
        success_ever |= all_gates
        if total in looks:
            success_by_look[str(total)] = float(np.mean(success_ever))

    successes = int(np.sum(success_ever))
    return {
        "scenario_id": scenario["scenario_id"],
        "assumptions": scenario,
        "replicates": replicates,
        "successes_by_maximum": successes,
        "success_probability_by_look": success_by_look,
        "success_probability_at_or_before_maximum": successes / replicates,
        "success_probability_wilson_95": _wilson_interval(successes, replicates),
    }


def build_report(
    protocol: dict[str, Any], *, null_replicates: int, alternative_replicates: int, seed: int
) -> dict[str, Any]:
    validate_protocol(protocol)
    fractions = tuple(float(item) for item in protocol["analysis"]["betting_fractions"])
    allocation = float(protocol["error_budget_ledger"]["allocations"][0]["alpha"])
    gate_alpha = allocation
    maximum = int(protocol["stopping_rule"]["maximum_total_clusters"])
    null_cases = (
        ("primary_boundary", maximum, 0.20, 0.05, 0.15),
        ("material_boundary", maximum, 0.01, 0.03, -0.02),
        ("coverage_boundary", maximum, 0.025, 0.075, -0.05),
        ("ambiguity_boundary", int(maximum * 0.2), 0.025, 0.075, -0.05),
    )
    null_results = {}
    for offset, (name, observations, plus, minus, null_mean) in enumerate(null_cases):
        null_results[name] = simulate_endpoint_crossing(
            replicates=null_replicates,
            observations=observations,
            plus_probability=plus,
            minus_probability=minus,
            null_mean=null_mean,
            alpha=gate_alpha,
            fractions=fractions,
            seed=seed + offset,
        )

    scenarios = (
        {
            "scenario_id": "large-primary-low-guardrail-discordance",
            "primary": {"plus_probability": 0.35, "minus_probability": 0.05},
            "material": {"plus_probability": 0.005, "minus_probability": 0.005},
            "coverage": {"plus_probability": 0.01, "minus_probability": 0.01},
            "ambiguity": {"plus_probability": 0.005, "minus_probability": 0.005},
        },
        {
            "scenario_id": "large-primary-moderate-guardrail-discordance",
            "primary": {"plus_probability": 0.35, "minus_probability": 0.05},
            "material": {"plus_probability": 0.01, "minus_probability": 0.01},
            "coverage": {"plus_probability": 0.025, "minus_probability": 0.025},
            "ambiguity": {"plus_probability": 0.01, "minus_probability": 0.01},
        },
        {
            "scenario_id": "worthwhile-boundary-low-guardrail-discordance",
            "primary": {"plus_probability": 0.20, "minus_probability": 0.05},
            "material": {"plus_probability": 0.005, "minus_probability": 0.005},
            "coverage": {"plus_probability": 0.01, "minus_probability": 0.01},
            "ambiguity": {"plus_probability": 0.005, "minus_probability": 0.005},
        },
    )
    alternatives = [
        simulate_joint_campaign(
            protocol=protocol,
            replicates=alternative_replicates,
            seed=seed + 100 + index,
            scenario=scenario,
        )
        for index, scenario in enumerate(scenarios)
    ]
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schema": "crane-diagnostic-sequential-simulation/v1",
        "status": "PLANNING_AND_IMPLEMENTATION_QA_NOT_VALIDITY_PROOF",
        "protocol_id": protocol["protocol_id"],
        "protocol_sha256": protocol_sha256(protocol),
        "analysis_script_sha256": script_hash,
        "numpy_version": np.__version__,
        "seed": seed,
        "null_replicates_per_endpoint": null_replicates,
        "alternative_replicates_per_scenario": alternative_replicates,
        "per_gate_alpha": gate_alpha,
        "null_boundary_checks": null_results,
        "alternative_budgeting": alternatives,
        "interpretation_rules": [
            "The supermartingale argument, not simulation, establishes anytime validity.",
            "Boundary-null crossing rates are Monte Carlo implementation checks and retain sampling uncertainty.",
            "Alternative scenarios are design sensitivities, not observed effect estimates or promised power.",
            "Campaign-specific planning must be rerun after qualified development labels estimate realistic discordance and invalid-run rates.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--null-replicates", type=int, default=20000)
    parser.add_argument("--alternative-replicates", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260923)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.null_replicates < 1 or args.alternative_replicates < 1:
        parser.error("replicate counts must be positive")
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    report = build_report(
        protocol,
        null_replicates=args.null_replicates,
        alternative_replicates=args.alternative_replicates,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
