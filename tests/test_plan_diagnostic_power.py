from plan_diagnostic_power import (
    build_plan,
    exact_two_sided_binomial_p,
    minimum_clusters,
    paired_power,
)


def test_exact_two_sided_binomial_p_is_symmetric():
    assert exact_two_sided_binomial_p(1, 10) == exact_two_sided_binomial_p(9, 10)
    assert exact_two_sided_binomial_p(5, 10) == 1.0


def test_power_increases_with_independent_cluster_count_for_design_case():
    assert paired_power(96, 0.20, 0.05) > paired_power(48, 0.20, 0.05)
    assert paired_power(96, 0.20, 0.05) >= 0.80


def test_minimum_cluster_counts_are_reproducible():
    assert minimum_clusters(0.20, 0.05, 0.80) == 92
    assert minimum_clusters(0.30, 0.05, 0.80) == 45


def test_plan_does_not_present_sensitivity_as_observed_effect():
    plan = build_plan()
    assert plan["status"] == "DESIGN_SENSITIVITY_NOT_OBSERVED_EFFECT_ESTIMATE"
    assert plan["smallest_practically_meaningful_assumption"]["net_difference"] == 0.15
    assert any("must not" in item for item in plan["limitations"])
