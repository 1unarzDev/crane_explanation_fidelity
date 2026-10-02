import itertools
import numpy as np
import pytest
from roboboat_fixed_bet_sensitivity_v1 import (
    CANDIDATES,log_bet_e_value,log_expected_e_value,simulate,build_report,
)
from simulate_roboboat_fixed_n_power_v1 import SCORES,score_distribution,log_e_value


def test_log_e_matches_independent_small_product_reconstruction():
    sequence=[-1,-1/6,0,1/3,1]
    counts=np.zeros(13,dtype=int)
    for x in sequence:
        counts[int(round(6*x))+6]+=1
    for b in CANDIDATES.values():
        direct=sum(w*np.prod([1+lam*x for x in sequence]) for lam,w in zip(b['lambdas'],b['weights']))
        assert np.exp(log_bet_e_value(counts,**b))==pytest.approx(direct)
    assert log_bet_e_value(counts,**CANDIDATES['retained_eleven_equal_weight'])==pytest.approx(log_e_value(counts))


def test_heterogeneous_weighted_average_null_exact_expectation():
    # Independent X_i in {-1,+1}, heterogeneous means and unequal allocations.
    means=[.2,-.1,-.4]
    allocations=[2,2,1]
    expanded=[mu for mu,n in zip(means,allocations) for _ in range(n)]
    assert np.dot(means,allocations)<0
    for b in CANDIDATES.values():
        expected=0.
        for xs in itertools.product((-1,1),repeat=5):
            probability=np.prod([(1+mu*x)/2 for mu,x in zip(expanded,xs)])
            value=sum(w*np.prod([1+lam*x for x in xs]) for lam,w in zip(b['lambdas'],b['weights']))
            expected+=probability*value
        exact=np.exp(log_expected_e_value(means,allocations,**b))
        assert exact==pytest.approx(expected)
        assert exact<=1
    # Positive-family means are permitted under a zero weighted-average null.
    for b in CANDIDATES.values():
        assert log_expected_e_value([.3,-.1],[1,3],**b)<=1e-14


def test_no_unadjusted_maximization_of_components():
    counts=np.zeros(13,dtype=int)
    counts[12]=10
    b=CANDIDATES['narrow_four_equal_weight']
    mean_value=np.exp(log_bet_e_value(counts,**b))
    component_values=[(1+lam)**10 for lam in b['lambdas']]
    assert mean_value==pytest.approx(sum(component_values)/4)
    assert mean_value<max(component_values)


def test_extreme_counts_are_stable():
    for i in (0,6,12):
        counts=np.zeros(13,dtype=int)
        counts[i]=1000000
        for b in CANDIDATES.values():
            assert np.isfinite(log_bet_e_value(counts,**b))


def test_fixed_bet_negative_growth_can_miss_a_real_positive_effect():
    pmf=score_distribution(.05,.6,1)
    assert pmf@SCORES==pytest.approx(.05)
    assert pmf@np.log1p(.25*SCORES)<0
    # The narrow mixture's smallest component has positive growth here.
    assert pmf@np.log1p(.1*SCORES)>0


def test_complete_registered_scenarios_and_no_selection():
    report=build_report(repetitions=2)
    assert len(report['scenarios'])==34
    assert report['all_registered_candidates']==CANDIDATES
    assert report['confirmation_test_selected'] is report['confirmation_n_selected'] is None
    assert report['confirmation_n']==report['alpha_consumed']==0
    names={s['name'] for s in report['scenarios']}
    assert 'variance_concentrated_in_one_family_left_skew_null' in names
    assert 'symmetric_sparse_discordance_null' in names
    assert 'ten_point_effect_unresolved_clusters-0.1' in names


def test_reproducibility_real_input_refusal_and_parameter_validation():
    families=[score_distribution(.1,.4,1)]*6
    assert simulate(families,120,100)==simulate(families,120,100)
    with pytest.raises(ValueError,match='SIMULATED'):
        simulate(families,120,origin='OBSERVED')
    with pytest.raises(ValueError,match='SIMULATED'):
        log_bet_e_value(np.zeros(13),[.25],[1],origin='OBSERVED')
    with pytest.raises(ValueError):
        log_bet_e_value(np.zeros(13),[.25,.5],[.5,.6])
    with pytest.raises(ValueError):
        log_bet_e_value(np.zeros(13),[1],[1])
    with pytest.raises(ValueError):
        log_expected_e_value([.2],[-1],[.25],[1])
