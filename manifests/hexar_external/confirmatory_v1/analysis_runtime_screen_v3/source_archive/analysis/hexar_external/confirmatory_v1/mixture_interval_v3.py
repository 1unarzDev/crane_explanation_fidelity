"""Candidate exact-integral directed bounds using finite binomial beta sums.

No inferential change. For no ties use algebraic beta integrals; otherwise use
qualified grouped Bernstein arithmetic. All operations enclose the same E(mu).
"""
from decimal import Decimal, localcontext, ROUND_FLOOR, ROUND_CEILING, InvalidOperation
from fractions import Fraction
import math

from .mixture_statistics import check_counts, evidence_fraction, reject
from .mixture_interval_v2 import integral_bounds as grouped_bounds


def _rounded(fn, precision, rounding):
    with localcontext() as context:
        context.prec = precision
        context.rounding = rounding
        return fn()


def _multiply(a, b, precision):
    return (_rounded(lambda:a[0]*b[0], precision, ROUND_FLOOR),
            _rounded(lambda:a[1]*b[1], precision, ROUND_CEILING))


def _divide(a, b, precision):
    if b[0] <= 0:
        raise ValueError('positive directed denominator required')
    return (_rounded(lambda:a[0]/b[1], precision, ROUND_FLOOR),
            _rounded(lambda:a[1]/b[0], precision, ROUND_CEILING))


def _power(value, exponent, precision):
    result, base = (Decimal(1), Decimal(1)), (value, value)
    while exponent:
        if exponent % 2:
            result = _multiply(result, base, precision)
        exponent //= 2
        if exponent:
            base = _multiply(base, base, precision)
    return result


def _tail(m, k, p, precision):
    if p == 0:
        return Decimal(0), Decimal(0)
    if p == 1:
        return Decimal(1), Decimal(1)
    q = _rounded(lambda:1-p, precision, ROUND_FLOOR) # exact at input-derived precision
    choose = Decimal(math.comb(m, k))
    term = _multiply((choose, choose), _multiply(_power(p, k, precision),
        _power(q, m-k, precision), precision), precision)
    total = term
    for j in range(k, m):
        value = Decimal(m-j)
        term = _multiply(term, (value, value), precision)
        value = Decimal(j+1)
        term = _divide(term, (value, value), precision)
        term = _multiply(term, (p, p), precision)
        term = _divide(term, (q, q), precision)
        total = (_rounded(lambda:total[0]+term[0], precision, ROUND_FLOOR),
                 _rounded(lambda:total[1]+term[1], precision, ROUND_CEILING))
    return total


def integral_bounds(favorable, unfavorable, n, mu, precision=60):
    check_counts(favorable, unfavorable, n)
    try:
        target = Decimal(str(mu))
    except InvalidOperation as exc:
        raise ValueError('finite decimal effect required') from exc
    if not target.is_finite() or not -1 <= target <= 1:
        raise ValueError('effect in [-1,1] required')
    if type(precision) is not int or precision < 30:
        raise ValueError('at least 30-digit bound arithmetic required')
    if abs(target.as_tuple().exponent)>1000 or len(target.as_tuple().digits)>1000:
        raise ValueError('bounded effect decimal scale required')
    if favorable+unfavorable != n:
        return grouped_bounds(favorable, unfavorable, n, mu, precision)
    precision = max(precision, len(target.as_tuple().digits)+max(0,-target.as_tuple().exponent)+len(str(n))+10)
    def exact_fraction(value):
        return (_rounded(lambda:Decimal(value.numerator)/Decimal(value.denominator), precision, ROUND_FLOOR),
                _rounded(lambda:Decimal(value.numerator)/Decimal(value.denominator), precision, ROUND_CEILING))
    if target == 0:
        return exact_fraction(evidence_fraction(favorable, unfavorable))
    if target == -1:
        return exact_fraction(Fraction(2**(favorable+1)-1, favorable+1))
    if target == 1:
        return exact_fraction(Fraction(1, unfavorable+1))
    # 1 +/- target and division by 2 are exact at the input-derived precision.
    a = _rounded(lambda:1+target, precision, ROUND_FLOOR)
    b = _rounded(lambda:1-target, precision, ROUND_FLOOR)
    if target > 0:
        probability = _rounded(lambda:b/2, precision, ROUND_FLOOR)
        beta_mass = _tail(n+1, unfavorable+1, probability, precision)
        denominator = _multiply(_power(a, favorable, precision),
                                _power(b, unfavorable+1, precision), precision)
    else:
        lower_probability = _rounded(lambda:a/2, precision, ROUND_FLOOR)
        high = _tail(n+1, favorable+1, a, precision)
        low = _tail(n+1, favorable+1, lower_probability, precision)
        beta_mass = (max(Decimal(0), _rounded(lambda:high[0]-low[1], precision, ROUND_FLOOR)),
                     max(Decimal(0), _rounded(lambda:high[1]-low[0], precision, ROUND_CEILING)))
        denominator = _multiply(_power(b, unfavorable, precision),
                                _power(a, favorable+1, precision), precision)
    coefficient = Decimal((n+1)*math.comb(n, favorable))
    denominator = _multiply(denominator, (coefficient, coefficient), precision)
    numerator = Decimal(2**(n+1))
    scale = _divide((numerator, numerator), denominator, precision)
    return _multiply(scale, beta_mass, precision)


def lower_bound(favorable, unfavorable, n, alpha=.01, iterations=48):
    check_counts(favorable, unfavorable, n)
    level = Fraction(str(alpha))
    if not 0 < level < 1:
        raise ValueError('alpha in (0,1) required')
    if type(iterations) is not int or iterations < 1:
        raise ValueError('positive fixed inversion iterations required')
    def certified_rejection(mu):
        if mu == 0:
            return reject(favorable, unfavorable, alpha)
        for precision in (60, 120, 240):
            lo, hi = integral_bounds(favorable, unfavorable, n, mu, precision)
            if Fraction(lo)*level >= 1:
                return True
            if Fraction(hi)*level < 1:
                return False
        return False
    if not certified_rejection(-1):
        return -1.
    low, high = -1., 1.
    for _ in range(iterations):
        middle = (low+high)/2
        if certified_rejection(middle):
            low = middle
        else:
            high = middle
    return low


def summary(favorable, unfavorable, n, alpha=.01):
    check_counts(favorable, unfavorable, n)
    evidence = evidence_fraction(favorable, unfavorable)
    p = min(Fraction(1), 1/evidence)
    low = lower_bound(favorable, unfavorable, n, alpha)
    high = -lower_bound(unfavorable, favorable, n, alpha)
    return dict(procedure='fixed_N_uniform_paired_e_mixture_candidate', alpha=alpha,
        favorable=favorable, unfavorable=unfavorable, n=n,
        paired_absolute_risk_difference=(favorable-unfavorable)/n,
        evidence_exact=dict(numerator=str(evidence.numerator), denominator=str(evidence.denominator)),
        one_sided_p_value=float(p), p_exact=dict(numerator=str(p.numerator), denominator=str(p.denominator)),
        reject=reject(favorable, unfavorable, alpha), one_sided_lower=low, two_sided_interval=[low, high],
        interval_coverage_note='One-sided >=1-alpha; joint two-sided >=1-2*alpha. Refers to measured/mapped endpoint, not automatically latent complete-label truth.',
        primary_rejection_uses_exact_rational_arithmetic=True, independence_required=True,
        optional_stopping_authorized=False)
