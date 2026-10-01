import math

import pytest

from plan_roboboat_population_power import (
    binomial_at_least, build_plan, cluster_variance, collection_budget,
    hoeffding_planning_n, hoeffding_power_lower_bound, normal_planning_n, normal_power,
)


def test_six_questions_are_not_six_independent_configurations():
    assert cluster_variance(.1, .4, 0) == pytest.approx((.4-.01)/6)
    assert cluster_variance(.1, .4, 1) == pytest.approx(.4-.01)
    assert normal_planning_n(.1, .4, 1) >= 5 * normal_planning_n(.1, .4, 0)


def test_variance_matches_explicit_joint_mixture():
    # With probability rho all six Y share one draw; otherwise six iid draws.
    # Y probabilities are (.15, .60, .25) for (-1,0,1).
    marginal_mean = -.15+.25
    marginal_second = .15+.25
    rho = .25
    second_cluster_mean = rho*marginal_second + (1-rho)*(marginal_second/6+5*marginal_mean**2/6)
    assert cluster_variance(.1, .4, rho) == pytest.approx(second_cluster_mean-marginal_mean**2)


def test_n_attains_normal_target_and_preceding_n_does_not():
    for power in (.8, .9):
        n = normal_planning_n(.1, .4, .5, power)
        assert normal_power(n, .1, .4, .5) >= power
        assert normal_power(n-1, .1, .4, .5) < power
    assert normal_planning_n(.05, .4, .5) > normal_planning_n(.1, .4, .5)


def test_hoeffding_n_guarantees_requested_bound():
    for delta in (.05, .1, .2):
        n = hoeffding_planning_n(delta, .9)
        assert hoeffding_power_lower_bound(n, delta) >= .9
        assert hoeffding_power_lower_bound(n-1, delta) < .9
    assert hoeffding_power_lower_bound(10, .1) == 0


def test_binomial_tail_against_enumeration_and_boundary_cases():
    for needed in range(7):
        expected = sum(math.comb(6,k)*.8**k*.2**(6-k) for k in range(needed,7))
        assert binomial_at_least(6, needed, .8) == pytest.approx(expected)
    assert binomial_at_least(6, 7, .8) == 0
    assert binomial_at_least(6, 1, 0) == 0
    assert binomial_at_least(6, 6, 1) == 1


def test_collection_budget_targets_both_variant_valid_configurations():
    budget = collection_budget(100, .1)
    total = budget['attempted_configurations_for_assurance']
    assert budget['expected_attempted_configurations'] == 112
    assert binomial_at_least(total, 100, .9) >= .95
    assert binomial_at_least(total-1, 100, .9) < .95
    assert budget['physical_variant_recordings_for_assurance'] == total*2
    assert collection_budget(100, 0)['attempted_configurations_for_assurance'] == 100


@pytest.mark.parametrize('args', [(.3,.2,0), (.1,.4,1.1), (.1,math.nan,0), (-.1,.4,0)])
def test_invalid_moments_rejected(args):
    with pytest.raises(ValueError):
        cluster_variance(*args)


def test_invalid_planning_and_acquisition_inputs_rejected():
    with pytest.raises(ValueError):
        normal_planning_n(0, .4, 0)
    with pytest.raises(ValueError):
        normal_planning_n(.1, .4, 0, .01, .025)
    with pytest.raises(ValueError):
        collection_budget(100, 1)
    with pytest.raises(ValueError):
        collection_budget(1.2, .1)
    with pytest.raises(ValueError):
        hoeffding_planning_n(.1, 1)


def test_report_marks_assumptions_and_preserves_development_boundary():
    report = build_plan()
    assert report['inferential_activation_authorized'] is False
    assert report['alpha_consumed'] == 0
    assert report['development_observations']['confirmatory_n'] == 0
    assert report['development_observations']['approach_clusters'] == 3
    assert len(report['sensitivity']) == 96
    assert report['resource_planning_example']['valid_n'] > 400
    assert report['annotation_uncertainty']['effective_effect_lower_bound_examples'][-1]['adverse_mean_effect_lower_bound'] == 0
