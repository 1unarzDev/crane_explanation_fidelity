"""Fixed-N paired e-test for an average-risk null under independent heterogeneity.

Candidate alternative only. No alpha allocated and no empirical inputs read.
D_i = prompt failure - contract failure in {-1,0,1}. For fixed lambda in (0,1),
E_mu = product_i [1 + lambda*(D_i-mu)/(1+abs(mu))]. Under the null that the
average expected D is <=mu, independence and AM-GM give E[E_mu] <=1.
Markov gives P(E_mu >=1/alpha) <=alpha. This needs no common discordance q.
All lambda, N, and test selection must be frozen before semantic generation.
"""
import math
from functools import lru_cache
from .statistics import pmf


def log_evalue(favorable, unfavorable, ties, mu=0., fraction=.6):
    if any(type(n) is not int or n<0 for n in (favorable,unfavorable,ties)):
        raise ValueError('integer nonnegative counts required')
    if not -1<=mu<=1 or not 0<fraction<1:
        raise ValueError('mu/fraction out of range')
    slope=fraction/(1+abs(mu))
    return math.fsum(count*math.log1p(slope*(difference-mu))
                     for count,difference in ((favorable,1),(unfavorable,-1),(ties,0)))


def lower_bound(favorable,unfavorable,ties,alpha=.01,fraction=.6):
    if not 0<alpha<1:
        raise ValueError('alpha out of range')
    threshold=-math.log(alpha)
    if log_evalue(favorable,unfavorable,ties,-1.,fraction)<threshold:
        return -1.
    lo,hi=-1.,1.
    for _ in range(80):
        mid=(lo+hi)/2
        if log_evalue(favorable,unfavorable,ties,mid,fraction)>=threshold:
            lo=mid
        else:
            hi=mid
    return (lo+hi)/2


def summarize(favorable,unfavorable,both_success,both_failure,fraction=.6):
    counts=(favorable,unfavorable,both_success,both_failure)
    if any(type(x) is not int or x<0 for x in counts) or not sum(counts):
        raise ValueError('four nonnegative paired counts with positive N required')
    n=sum(counts); ties=both_success+both_failure
    loge=log_evalue(favorable,unfavorable,ties,fraction=fraction)
    lower=lower_bound(favorable,unfavorable,ties,fraction=fraction)
    upper=-lower_bound(unfavorable,favorable,ties,fraction=fraction)
    return dict(n=n,favorable=favorable,unfavorable=unfavorable,
                both_success=both_success,both_failure=both_failure,
                prompt_failure_rate=(favorable+both_failure)/n,
                contract_failure_rate=(unfavorable+both_failure)/n,
                prompt_minus_contract_failure_risk_difference=(favorable-unfavorable)/n,
                frozen_fraction=fraction,log_evalue=loge,
                conservative_one_sided_p=math.exp(-max(0.,loge)),
                one_sided_99_lower_bound=lower,two_sided_98_interval=[lower,upper],
                procedure='fixed-N paired e-test; Markov finite-sample control; independent nonidentical pairs permitted',
                exact_mcnemar=False)


@lru_cache(None)
def rejection_probability(m,q,alpha,fraction):
    a=math.log1p(fraction); b=math.log1p(-fraction)
    cutoff=max(0, math.ceil((-math.log(alpha)-m*b)/(a-b)))
    return 0. if cutoff>m else math.fsum(pmf(m,q)[cutoff:])


def power(n,discordance,q,alpha=.01,fraction=.6):
    """Exact rejection probability enumeration; the e-test itself is conservative."""
    if not 0<alpha<1:
        raise ValueError('alpha out of range')
    return min(1., math.fsum(prob*rejection_probability(m,q,alpha,fraction)
                            for m,prob in enumerate(pmf(n,discordance))))
