import numpy as np
import pytest
from statistics import NormalDist
from roboboat_cluster_score_design_v1 import (
    evaluate_simulated_counts,simulate,welch_critical_cf3,point_mass,scenarios,build_report,
)
from simulate_roboboat_fixed_n_power_v1 import score_distribution


def test_stratified_mean_and_variance_by_hand():
    counts=np.zeros((1,6,13),dtype=int)
    counts[:, :, 6]=2
    counts[:, :, 12]=2
    result=evaluate_simulated_counts(counts)
    # Each family has observations 0,0,1,1: sample variance 1/3.
    assert result['estimated_equal_family_mean'][0] == .5
    assert result['estimated_variance_of_mean'][0] == pytest.approx(1/72)
    assert result['welch_effective_df'][0] == pytest.approx(18)


def test_zero_sample_variance_does_not_produce_false_normal_certainty():
    counts=np.zeros((2,6,13),dtype=int)
    counts[0,:,7]=25
    counts[1,:,6]=25
    result=evaluate_simulated_counts(counts)
    assert result['zero_estimated_variance'].tolist()==[True,True]
    assert not result['stratified_wald'].any()
    assert not result['stratified_welch_t_cf3'].any()


def test_t_approximation_limits_and_known_quantile():
    z=NormalDist().inv_cdf(.975)
    assert welch_critical_cf3(1e8) == pytest.approx(z,rel=1e-7)
    assert welch_critical_cf3(24) == pytest.approx(2.063899,abs=1e-5)
    assert welch_critical_cf3(9)>welch_critical_cf3(24)>z


def test_heterogeneous_positive_families_can_have_weak_average_null():
    families=[point_mass(7)]*5+[score_distribution(-5/6,1,1)]
    result=simulate(families,150,repetitions=100,seed=1)
    assert result['equal_family_population_mean']==pytest.approx(0,abs=1e-15)
    assert result['true_variance_of_equal_family_mean']>0


def test_concentrated_skew_null_is_a_real_conventional_failure_case():
    scenario=next(s for s in scenarios() if s['name']=='variance_concentrated_in_one_family_left_skew_null')
    result=simulate(scenario['families'],150,repetitions=20000,seed=22)
    assert result['equal_family_population_mean']==pytest.approx(0,abs=1e-15)
    assert result['methods']['stratified_wald']['estimated_rejection_probability']>.07
    assert result['methods']['stratified_welch_t_cf3']['estimated_rejection_probability']>.07
    assert result['methods']['fixed_lambda_mixture']['estimated_rejection_probability']<.025


def test_simulation_reproducible_and_unresolved_can_reverse_effect():
    families=[score_distribution(.1,.4,.25)]*6
    assert simulate(families,120,repetitions=100,seed=1)==simulate(families,120,repetitions=100,seed=1)
    scenario=next(s for s in scenarios() if s['name']=='ten_point_effect_unresolved_clusters-0.1')
    assert simulate(scenario['families'],120,100)['equal_family_population_mean']==pytest.approx(-.01)


def test_real_inputs_and_unbalanced_allocations_refused():
    with pytest.raises(ValueError,match='SIMULATED'):
        simulate([point_mass(6)]*6,120,origin='OBSERVED')
    with pytest.raises(ValueError,match='divisible'):
        simulate([point_mass(6)]*6,100)
    counts=np.zeros((1,6,13),dtype=int)
    counts[:,:,6]=10
    counts[:,0,6]=11
    with pytest.raises(ValueError,match='balanced'):
        evaluate_simulated_counts(counts)
    with pytest.raises(ValueError,match='SIMULATED'):
        evaluate_simulated_counts(counts,origin='OBSERVED')


def test_report_has_no_selected_test_or_confirmation_n():
    report=build_report(repetitions=2)
    assert report['confirmation_test_selected'] is None
    assert report['confirmation_n_selected'] is None
    assert report['alpha_consumed']==report['confirmation_n']==0
    assert report['inferential_activation_authorized'] is False
    assert 'asymptotic' in report['conventional_test_limits']


def test_exact_null_event_exceeds_nominal_alpha_despite_t_critical():
    # Five deterministic-zero families; sixth has 24*(1/6) and 1*(-1).
    counts=np.zeros((1,6,13),dtype=int)
    counts[:,:5,6]=25
    counts[:,5,7]=24
    counts[:,5,0]=1
    result=evaluate_simulated_counts(counts)
    assert result['welch_effective_df'][0]==pytest.approx(24)
    assert result['stratified_wald'][0]
    assert result['stratified_welch_t_cf3'][0]
    assert 25*(1/7)*(6/7)**24 > .088
