import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "analysis" / "simulate_clustered_power.py"
SPEC = importlib.util.spec_from_file_location("simulate_clustered_power", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_simulation_is_deterministic_and_preserves_risk_order():
    arguments = dict(
        episodes=12,
        questions_per_episode=4,
        risk_a=0.10,
        risk_d=0.04,
        cluster_icc=0.10,
        paired_latent_correlation=0.50,
        simulations=40,
        seed=19,
    )
    first = MODULE.simulate_power(**arguments)
    second = MODULE.simulate_power(**arguments)
    assert first == second
    assert first["mean_simulated_risk_a"] > first["mean_simulated_risk_d"]
    assert 0.0 <= first["power_two_sided_95_cluster_normal"] <= 1.0


def test_invalid_probability_is_rejected():
    try:
        MODULE.calibrate_intercept(0.0, 0.5)
    except ValueError as error:
        assert "strictly between" in str(error)
    else:
        raise AssertionError("zero risk unexpectedly accepted")
