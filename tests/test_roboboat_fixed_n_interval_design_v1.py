import math
import itertools
import numpy as np
import pytest
from roboboat_fixed_n_interval_design_v1 import log_e_value,lower_bound,interval


BET=([.1,.2,.3,.4],[.25]*4)


def test_zero_null_reproduces_existing_fixed_bet_statistic():
    x=np.array([-1,-1/6,0,1/6,1])
    expected=np.mean([np.prod(1+lam*x) for lam in BET[0]])
    assert math.exp(log_e_value(x,0,*BET))==pytest.approx(expected)


def test_centered_evalue_expectation_valid_for_heterogeneous_average_null():
    means=np.array([-.8,.6,-.4,.2]);mu=means.mean()
    expectation=0
    for x in itertools.product((-1,1),repeat=4):
        probability=np.prod([(1+m)/2 if value==1 else (1-m)/2 for value,m in zip(x,means)])
        expectation+=probability*math.exp(log_e_value(x,mu,*BET))
    assert expectation<=1+1e-12
    expected=np.mean([np.prod(1+lam*(means-mu)/(1+mu)) for lam in BET[0]])
    assert expectation==pytest.approx(expected)


def test_inversion_is_monotone_bracketed_and_respects_endpoints():
    x=np.tile([1,1,0,-1],100)
    logs=[log_e_value(x,mu,*BET) for mu in (-.5,0,.2,.4,.8)]
    assert logs==sorted(logs,reverse=True)
    lo,hi=interval(x,*BET)
    assert -1 <= lo <= x.mean() <= hi <= 1
    assert log_e_value(x,lo,*BET)==pytest.approx(math.log(40),abs=1e-9)
    assert lower_bound([-1]*20,*BET)==-1
    assert interval([1]*20,*BET)[1]==1


def test_unknown_adverse_bounds_do_not_increase_superiority_statistic():
    actual=np.array([1,0,1/6,-1/6,1])
    adverse=actual.copy();adverse[[0,2]]=-1
    for mu in (-.5,0,.5):assert log_e_value(adverse,mu,*BET)<=log_e_value(actual,mu,*BET)
    assert lower_bound(adverse,*BET)<=lower_bound(actual,*BET)


def test_real_origin_invalid_scores_and_settings_refused():
    with pytest.raises(ValueError,match='SIMULATED'):interval([0],*BET,origin='CONFIRMATION')
    for x in ([],[float('nan')],[1.1],[[0,1]]):
        with pytest.raises(ValueError):interval(x,*BET)
    with pytest.raises(ValueError):lower_bound([0],*BET,alpha=0)
    with pytest.raises(ValueError):log_e_value([0],-1,*BET)
