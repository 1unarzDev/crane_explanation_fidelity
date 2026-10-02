import itertools
from fractions import Fraction
import math
import pytest
from analysis.hexar_external.confirmatory_v1.mixture_statistics import evidence_fraction,integral_bounds,reject,summary,power


def test_exact_beta_integral_matches_direct_small_polynomials():
    for f in range(8):
        for u in range(8):
            coefficients=[1]
            for direction in [1]*f+[-1]*u:
                following=[0]*(len(coefficients)+1)
                for index,value in enumerate(coefficients):following[index]+=value;following[index+1]+=direction*value
                coefficients=following
            exact=sum((Fraction(value,index+1) for index,value in enumerate(coefficients)),Fraction(0))
            assert evidence_fraction(f,u)==exact
    assert reject(9,0) and not reject(8,0)


def test_nonidentical_mean_null_controls_integrated_expectation_and_size():
    regimes=[(0.,0.),(.1,.1),(.1,.3),(.3,.1),(.4,.4)] # (favorable, unfavorable)
    for family_pairs in itertools.product(regimes,repeat=3):
        if sum(f-u for f,u in family_pairs)>1e-12:continue
        expectation=size=0.
        for outcomes in itertools.product((-1,0,1),repeat=3):
            probability=math.prod((f if d==1 else u if d==-1 else 1-f-u) for (f,u),d in zip(family_pairs,outcomes))
            f,u=outcomes.count(1),outcomes.count(-1)
            expectation+=probability*float(evidence_fraction(f,u));size+=probability*reject(f,u)
        assert expectation<=1+1e-12 and size<=.01+1e-12


def test_directed_bernstein_bounds_match_exact_rational_integrals_with_ties():
    for mu in (Fraction(-1,2),Fraction(0),Fraction(1,2)):
        coefficients=[Fraction(1)]
        for d in (1,-1,0,1):
            a=(d-mu)/(1+abs(mu));following=[Fraction(0)]*(len(coefficients)+1)
            for index,value in enumerate(coefficients):following[index]+=value;following[index+1]+=a*value
            coefficients=following
        exact=sum((v/(i+1) for i,v in enumerate(coefficients)),Fraction(0))
        lo,hi=integral_bounds(2,1,4,float(mu))
        assert Fraction(lo)<=exact<=Fraction(hi)


def test_corresponding_interval_and_exact_test_preserve_direction():
    result=summary(14,1,30)
    assert (result['one_sided_lower']>0)==result['reject']
    reverse=summary(1,14,30)
    assert reverse['paired_absolute_risk_difference']<0 and not reverse['reject']
    assert result['two_sided_interval']==pytest.approx([-reverse['two_sided_interval'][1],-reverse['two_sided_interval'][0]],abs=1e-12)
    assert power(12,.5,.8)>power(12,.5,.6)


@pytest.mark.parametrize('args',[(True,0,12),(5,8,12),(1,0,0),(-1,0,12)])
def test_invalid_counts_fail(args):
    with pytest.raises(ValueError):summary(*args)


def test_nontrivial_rejection_size_under_balanced_opposing_family_means():
    def distribution(n,f,u):
        return [(a,b, Fraction(math.comb(n,a)*math.comb(n-a,b))*f**a*u**b*(1-f-u)**(n-a-b))
                for a in range(n+1) for b in range(n-a+1)]
    first=distribution(10,Fraction(3,5),Fraction(1,10))
    second=distribution(10,Fraction(1,10),Fraction(3,5))
    size=sum((p*q for f,u,p in first for g,v,q in second if reject(f+g,u+v)),Fraction(0))
    assert 0<size<=Fraction(1,100)


def test_monotone_integral_and_directed_bounds_with_tiny_effects():
    from decimal import Decimal
    last=None
    for target in ('-0.9','-0.5','-1e-80','0','0.3','0.8'):
        lo,hi=integral_bounds(8,2,20,Decimal(target),precision=30)
        assert lo<=hi
        if last is not None:
            previous_lo,previous_hi=last
            # For changes below arithmetic resolution, enclosing intervals overlap.
            assert hi<=previous_lo or lo<=previous_hi
        last=(lo,hi)
    assert power(1100,.1,.8)>=0.99 # stable binomial probabilities beyond float combinatorial overflow
