import itertools
from decimal import Decimal, localcontext
import numpy as np
import pytest
from roboboat_fixed_n_interval_design_v2 import interval, lower_bound, NUMERICAL_MARGIN

BET=([.1,.2,.3,.4],[.25]*4)


def test_missing_api_does_not_use_adverse_upper_tail():
    assert interval([-1]*20,[1]*20,*BET)==[-1.,1.]
    assert interval([-1]*20,[-1]*20,*BET)[1]<0
    assert interval([1]*20,[1]*20,*BET)[0]>0


def test_exact_heterogeneous_coverage_with_outcome_dependent_missingness():
    means=[-.95,-.9,-.8,-.7,-.6,.1]
    mu=sum(means)/len(means)
    misses=0.
    complete_misses=0.
    mass=0.
    # Enumerate every independent draw; conceal cells based on their outcome,
    # so no missing-at-random premise can silently enter the coverage argument.
    for xs in itertools.product((-1.,1.),repeat=len(means)):
        probability=np.prod([(1+m*x)/2 for m,x in zip(means,xs)])
        adverse=list(xs);favorable=list(xs)
        for i,x in enumerate(xs):
            if x>0 or i==0:
                adverse[i],favorable[i]=-1,1
        lo,hi=interval(adverse,favorable,*BET)
        clo,chi=interval(xs,xs,*BET)
        assert lo<=clo and hi>=chi
        mass+=probability
        misses+=probability*(not lo<=mu<=hi)
        complete_misses+=probability*(not clo<=mu<=chi)
    assert mass==pytest.approx(1)
    assert misses<=complete_misses+1e-14
    assert misses<=.05


def test_guarded_root_is_below_independent_high_precision_constant_score_root():
    for d,n in [(-.9,4),(0.,20),(.5,20),(1.,20),(1.,400)]:
        with localcontext() as ctx:
            ctx.prec=110
            lam=Decimal.from_float(.25);alpha=Decimal.from_float(.025)
            dd=Decimal.from_float(d)
            root=lam*(dd+1)/((-alpha.ln()/Decimal(n)).exp()-1+lam)-1
            bound=Decimal.from_float(lower_bound([d]*n,[.25],[1]))
            assert bound<=root
            assert Decimal('0')<=root-bound<Decimal(str(NUMERICAL_MARGIN*1.01))


def test_complete_equal_arrays_and_support_endpoints():
    assert lower_bound([-1]*20,*BET)==-1
    assert interval([1]*20,[1]*20,*BET)[1]==1
    x=np.array([-1,0,1/6,1,1])
    lo,hi=interval(x,x,*BET)
    assert -1<=lo<=x.mean()<=hi<=1


def test_informative_bounds_expand_complete_interval():
    xs=np.array([1.,0.,1/6,-1/6,1.])
    adverse=xs.copy();favorable=xs.copy()
    adverse[[0,2]]=-1
    favorable[[0,2]]=1
    complete=interval(xs,xs,*BET)
    missing=interval(adverse,favorable,*BET)
    assert missing[0]<=complete[0] and missing[1]>=complete[1]


@pytest.mark.parametrize('adverse,favorable', [([0],[0,1]),([1],[0]),([] ,[]),([np.nan],[1]),([-1],[1.1])])
def test_invalid_arrays_refused(adverse,favorable):
    with pytest.raises(ValueError):
        interval(adverse,favorable,*BET)


def test_real_origin_and_invalid_parameters_refused():
    with pytest.raises(ValueError,match='SIMULATED'):
        interval([0],[0],*BET,origin='OBSERVED')
    with pytest.raises(ValueError):
        interval([0],[0],*BET,alpha_per_tail=0)
    with pytest.raises(ValueError):
        interval([0],[0],[1],[1])
