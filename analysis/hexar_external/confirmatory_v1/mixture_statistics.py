"""Candidate fixed-N uniform betting-mixture paired superiority procedure.

One frozen statistic, not post-outcome selection over tests. No study data read.
For independent D_i in {-1,0,1}, E(mu)=integral_0^1 product_i
[1+lambda*(D_i-mu)/(1+abs(mu))] d lambda. Each constituent has
expectation <=1 under average E[D_i]<=mu by independence and AM-GM.
The nonnegative mixture therefore has expectation <=1; Markov controls size.
"""
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING, InvalidOperation
from fractions import Fraction
import math
from .statistics import tail,pmf
from functools import lru_cache


def check_counts(favorable,unfavorable,n):
    if any(type(v) is not int or v<0 for v in (favorable,unfavorable,n)) or n<1 or favorable+unfavorable>n:
        raise ValueError('nonnegative paired counts and positive fixed episode N required')


def evidence_fraction(favorable,unfavorable):
    """Exact rational integral at mu=0; ties contribute a factor of one.

    With m=f+u, E(0)=sum_{j=0}^f C(m+1,j) / [(m+1) C(m,f)].
    The beta-integral identity is algebra, not an IID-sign assumption.
    """
    if any(type(v) is not int or v<0 for v in (favorable,unfavorable)):raise ValueError('paired discordant counts required')
    m=favorable+unfavorable
    return Fraction(sum(math.comb(m+1,j) for j in range(favorable+1)),(m+1)*math.comb(m,favorable))


def reject(favorable,unfavorable,alpha=.01):
    level=Fraction(str(alpha))
    if not 0<level<1:raise ValueError('alpha in (0,1) required')
    return evidence_fraction(favorable,unfavorable)*level>=1


def integral_bounds(favorable,unfavorable,n,mu,precision=60):
    """Directed positive Bernstein arithmetic bounds for the same integral.

    Product endpoint factors are v_i=1+(D_i-mu)/(1+abs(mu))>=0.
    If e_k are their elementary symmetric sums, the integral is
    sum_k e_k/C(n,k)/(n+1). All arithmetic terms are nonnegative.
    Floor/ceiling decimal arithmetic supplies bounds without cancellation.
    """
    check_counts(favorable,unfavorable,n)
    try:target=Decimal(str(mu))
    except InvalidOperation as failure:raise ValueError('finite decimal effect required') from failure
    if not target.is_finite() or not -1<=target<=1:raise ValueError('effect in [-1,1] required')
    if type(precision) is not int or precision<30:raise ValueError('at least 30-digit bound arithmetic required')
    if abs(target.as_tuple().exponent)>1000 or len(target.as_tuple().digits)>1000:raise ValueError('bounded effect decimal scale required')
    # Keep 1 +/- mu and 1 - 2*mu exact before directed positive arithmetic.
    precision=max(precision,len(target.as_tuple().digits)+max(0,-target.as_tuple().exponent)+10)
    if target==0:
        exact=evidence_fraction(favorable,unfavorable)
        endpoints=[]
        for rounding in (ROUND_FLOOR,ROUND_CEILING):
            with localcontext() as context:
                context.prec=precision;context.rounding=rounding
                endpoints.append(Decimal(exact.numerator)/Decimal(exact.denominator))
        return tuple(endpoints)
    values=[]
    for rounding in (ROUND_FLOOR,ROUND_CEILING):
        with localcontext() as context:
            context.prec=precision;context.rounding=rounding
            if target>=0:
                denominator=1+target
                plus,zero,minus=Decimal(2)/denominator,Decimal(1)/denominator,Decimal(0)
            else:
                denominator=1-target
                plus,zero,minus=Decimal(2),(1-2*target)/denominator,(-2*target)/denominator
            endpoints=[plus]*favorable+[minus]*unfavorable+[zero]*(n-favorable-unfavorable)
            coefficients=[Decimal(1)]
            for endpoint in endpoints:
                coefficients.append(Decimal(0))
                for k in range(len(coefficients)-1,0,-1):
                    coefficients[k]+=endpoint*coefficients[k-1]
            values.append(sum((coefficient/Decimal(math.comb(n,k)) for k,coefficient in enumerate(coefficients)),Decimal(0))/Decimal(n+1))
    return tuple(values)


def lower_bound(favorable,unfavorable,n,alpha=.01,iterations=48):
    check_counts(favorable,unfavorable,n)
    level=Fraction(str(alpha))
    if not 0<level<1:raise ValueError('alpha in (0,1) required')
    if type(iterations) is not int or iterations<1:raise ValueError('positive fixed inversion iterations required')
    def certified_rejection(mu):
        if mu==0:return reject(favorable,unfavorable,alpha)
        for precision in (60,120,240):
            lo,hi=integral_bounds(favorable,unfavorable,n,mu,precision)
            # Threshold comparison uses exact rational decimals, with no float tolerance.
            if Fraction(lo)*level>=1:return True
            if Fraction(hi)*level<1:return False
        # Unseparated numerical boundary does not earn a rejection.
        return False
    if not certified_rejection(-1):return -1.
    low,high=-1.,1.
    for _ in range(iterations):
        middle=(low+high)/2
        if certified_rejection(middle):low=middle
        else:high=middle
    return low


def summary(favorable,unfavorable,n,alpha=.01):
    check_counts(favorable,unfavorable,n)
    evidence=evidence_fraction(favorable,unfavorable)
    p=min(Fraction(1),1/evidence)
    low=lower_bound(favorable,unfavorable,n,alpha)
    high=-lower_bound(unfavorable,favorable,n,alpha)
    return dict(procedure='fixed_N_uniform_paired_e_mixture_candidate',alpha=alpha,
        favorable=favorable,unfavorable=unfavorable,n=n,paired_absolute_risk_difference=(favorable-unfavorable)/n,
        evidence_exact=dict(numerator=str(evidence.numerator),denominator=str(evidence.denominator)),
        one_sided_p_value=float(p),p_exact=dict(numerator=str(p.numerator),denominator=str(p.denominator)),
        reject=reject(favorable,unfavorable,alpha),one_sided_lower=low,two_sided_interval=[low,high],
        interval_coverage_note='One-sided >=1-alpha; joint two-sided >=1-2*alpha. Refers to measured/mapped endpoint, not automatically latent complete-label truth.',
        primary_rejection_uses_exact_rational_arithmetic=True,independence_required=True,optional_stopping_authorized=False)


@lru_cache(None)
def critical_count(m,alpha=.01):
    if type(m) is not int or m<0:raise ValueError('discordant count required')
    level=Fraction(str(alpha))
    if not 0<level<1:raise ValueError('alpha in (0,1) required')
    prefix=0;term=1;choose=1
    for f in range(m+1):
        prefix+=term # C(m+1,f)
        if prefix*level.numerator>=(m+1)*choose*level.denominator:return f
        term=term*(m+1-f)//(f+1)
        choose=choose*(m-f)//(f+1)
    return m+1


@lru_cache(None)
def conditional_power(m,q,alpha=.01):
    return tail(m,critical_count(m,alpha),q)


def power(n,discordance,favorable_given_discordance,alpha=.01):
    if type(n) is not int or n<1 or not 0<=discordance<=1 or not 0<=favorable_given_discordance<=1:
        raise ValueError('fixed N and valid paired planning probabilities required')
    return math.fsum(probability*conditional_power(m,favorable_given_discordance,alpha)
                     for m,probability in enumerate(pmf(n,discordance)))
