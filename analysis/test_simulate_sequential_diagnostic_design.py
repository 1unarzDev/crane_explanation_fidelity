import json
from pathlib import Path

from simulate_sequential_diagnostic_design import (
    build_report,
    simulate_endpoint_crossing,
)


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = json.loads(
    (
        ROOT
        / "research/explanation_fidelity/experiment_configs/prospective/"
        "diagnostic-sequential-protocol-v2.json"
    ).read_text(encoding="utf-8")
)
FRACTIONS = tuple(PROTOCOL["analysis"]["betting_fractions"])


def test_boundary_null_simulation_does_not_show_gross_inflation():
    result = simulate_endpoint_crossing(
        replicates=4000,
        observations=400,
        plus_probability=0.20,
        minus_probability=0.05,
        null_mean=0.15,
        alpha=0.005,
        fractions=FRACTIONS,
        seed=7,
    )
    assert result["crossing_rate"] < 0.015
    assert result["crossing_rate_wilson_95"][1] < 0.02


def test_clear_alternative_crosses_more_often_than_boundary_null():
    null = simulate_endpoint_crossing(
        replicates=1000,
        observations=300,
        plus_probability=0.20,
        minus_probability=0.05,
        null_mean=0.15,
        alpha=0.005,
        fractions=FRACTIONS,
        seed=11,
    )
    alternative = simulate_endpoint_crossing(
        replicates=1000,
        observations=300,
        plus_probability=0.40,
        minus_probability=0.05,
        null_mean=0.15,
        alpha=0.005,
        fractions=FRACTIONS,
        seed=12,
    )
    assert alternative["crossing_rate"] > 0.9
    assert alternative["crossing_rate"] > null["crossing_rate"]


def test_small_report_is_reproducible_and_never_calls_it_validity_proof():
    first = build_report(PROTOCOL, null_replicates=20, alternative_replicates=20, seed=19)
    second = build_report(PROTOCOL, null_replicates=20, alternative_replicates=20, seed=19)
    assert first == second
    assert first["status"] == "PLANNING_AND_IMPLEMENTATION_QA_NOT_VALIDITY_PROOF"
    assert len(first["null_boundary_checks"]) == 4
    assert len(first["alternative_budgeting"]) == 3
