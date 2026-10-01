import numpy as np
import pytest

from plan_roboboat_population_power import cluster_variance
from simulate_roboboat_fixed_n_power_v1 import (
    SCORES, LAMBDAS, score_distribution, log_e_value,
    simulate_families, wilson, build_report,
)


def test_exact_moments_match_six_question_cluster_variance():
    for delta in (.05,.1,.15):
        for q in (.2,.4,.6):
            for rho in (0,.25,1):
                pmf = score_distribution(delta,q,rho)
                assert pmf.sum() == pytest.approx(1)
                assert pmf@SCORES == pytest.approx(delta)
                assert pmf@(SCORES-delta)**2 == pytest.approx(cluster_variance(delta,q,rho))


def test_shared_draw_extreme_is_primitive_paired_distribution():
    pmf = score_distribution(.1,.4,1)
    assert pmf[[0,6,12]].tolist() == pytest.approx([.15,.6,.25])
    assert np.count_nonzero(pmf) == 3


def test_log_e_matches_direct_mixture_and_stays_finite_at_extreme_n():
    counts = np.zeros(13, dtype=np.int64)
    counts[[0,5,12]] = [3,6,9]
    direct = np.prod((1+SCORES[:,None]*LAMBDAS[None,:])**counts[:,None],axis=0).mean()
    assert log_e_value(counts) == pytest.approx(np.log(direct))
    for index in (0,6,12):
        counts = np.zeros(13, dtype=np.int64)
        counts[index] = 1_000_000
        assert np.isfinite(log_e_value(counts))
    counts = np.zeros((2,13),dtype=int)
    counts[:,6] = 4000
    assert log_e_value(counts).tolist() == pytest.approx([0,0])


def test_weak_null_expectation_bound_allows_positive_family_means():
    # Positive family null is false; balanced average null is true.
    families = [score_distribution(.2,.4,.25),score_distribution(-.2,.6,1)]
    report = simulate_families(families,[50,50],100,np.random.default_rng(3))
    assert report['population_mean_score'] == pytest.approx(0)
    assert report['exact_expected_e_value'] <= 1
    exact = np.mean(((1+LAMBDAS*.2)*(1-LAMBDAS*.2))**50)
    assert report['exact_expected_e_value'] == pytest.approx(exact)
    # Further negative family mean is also a valid weak null.
    report = simulate_families(families,[25,75],100,np.random.default_rng(3))
    assert report['population_mean_score'] < 0
    assert report['exact_expected_e_value'] <= 1


def test_null_stress_rejections_fit_nominal_bound_and_reproducibility():
    args = ([score_distribution(0,.6,1)],[100],10000)
    first = simulate_families(*args,np.random.default_rng(41))
    second = simulate_families(*args,np.random.default_rng(41))
    assert first == second
    assert first['estimated_rejection_probability'] < .025


def test_missing_annotation_can_reverse_real_advantage():
    pmf = .9*score_distribution(.1,.4,.25)+.1*np.eye(13)[0]
    assert pmf@SCORES == pytest.approx(-.01)


def test_wilson_includes_empirical_rate_and_handles_extremes():
    assert wilson(0,100)[0] == 0
    assert wilson(100,100)[1] == 1
    low,high = wilson(90,100)
    assert low < .9 < high


@pytest.mark.parametrize('args',[(.3,.2,.25),(.1,.4,1.1),(np.nan,.4,0)])
def test_impossible_distribution_rejected(args):
    with pytest.raises(ValueError):
        score_distribution(*args)


def test_real_inputs_and_invalid_lambdas_rejected():
    with pytest.raises(ValueError,match='SIMULATED'):
        simulate_families([score_distribution(.1,.4,1)],[100],10,np.random.default_rng(1),origin='OBSERVED')
    with pytest.raises(ValueError):
        log_e_value(np.zeros(13),lambdas=[1])
    with pytest.raises(ValueError):
        log_e_value(np.full(13,.5))


def test_report_is_explicitly_noninferential_and_stresses_weak_null():
    report = build_report(seed=1,repetitions=5)
    assert report['alpha_consumed'] == report['confirmation_n'] == 0
    assert report['inferential_activation_authorized'] is False
    assert report['confirmation_n_selected'] is None
    assert len(report['alternative_scenarios']) == 18
    weak_null = next(s for s in report['stress_scenarios'] if s['name']=='heterogeneous_balanced_family_weak_null')
    assert all(r['population_mean_score'] < 1e-14 and r['exact_expected_e_value'] <= 1+1e-14 for r in weak_null['results'])


def test_extreme_n_expectation_uses_finite_log_without_overflow():
    result = simulate_families([score_distribution(.2,.4,1)],[1000000],2,np.random.default_rng(1))
    assert np.isfinite(result['exact_log_expected_e_value'])
    assert result['exact_expected_e_value'] is None
    assert result['estimated_rejection_probability'] == 1
