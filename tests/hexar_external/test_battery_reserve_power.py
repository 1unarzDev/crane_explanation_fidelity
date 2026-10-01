import math
import numpy as np
import pytest
from analysis.hexar_external.confirmatory_v1.battery_reserve_power import (
    battery_pairs,completion_probability,minimum_reserve)


def test_exact_reserve_completion_and_minimality():
    assert completion_probability(12,0,.1)==pytest.approx(.9**72)
    one_family=sum(math.comb(20,k)*.1**k*.9**(20-k) for k in range(5))
    assert completion_probability(16,4,.1)==pytest.approx(one_family**6)
    for invalid in (0.,.05,.1,.2):
        r=minimum_reserve(16,invalid)
        assert completion_probability(16,r,invalid)>=.99
        if r:assert completion_probability(16,r-1,invalid)<.99
    assert minimum_reserve(12,1.) is None


def test_independent_answer_battery_matches_analytic_episode_cells():
    n=100000
    f,u,ss,ff=np.array(battery_pairs(np.random.default_rng(711),n,.04,.10,0.,0.))/n
    cf=1-.96**9;pf=1-.90**9
    assert [f,u,ss,ff]==pytest.approx([(1-cf)*pf,cf*(1-pf),(1-cf)*(1-pf),cf*pf],abs=.005)
    assert u>0 # No imposed zero-unfavorable/nested-error model.


def test_full_dependence_and_equal_marginals_produce_identical_methods():
    cells=battery_pairs(np.random.default_rng(712),10000,.1,.1,1.,1.)
    assert cells[0]==cells[1]==0
    assert sum(cells)==10000
