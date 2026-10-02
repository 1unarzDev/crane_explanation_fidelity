"""Candidate faster directed bounds for the unchanged paired mixture integral.

Group identical nonnegative factors and omit exactly zero coefficients. This
changes arithmetic organization, not the statistic, endpoint or confidence
construction. Separate from the adopted implementation pending qualification.
"""
from decimal import Decimal, InvalidOperation, localcontext, ROUND_FLOOR, ROUND_CEILING
from fractions import Fraction

from .mixture_statistics import check_counts, evidence_fraction, reject


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
    if abs(target.as_tuple().exponent) > 1000 or len(target.as_tuple().digits) > 1000:
        raise ValueError('bounded effect decimal scale required')
    precision = max(precision, len(target.as_tuple().digits) + max(0, -target.as_tuple().exponent) + 10)
    bounds = []
    for rounding in (ROUND_FLOOR, ROUND_CEILING):
        with localcontext() as context:
            context.prec = precision
            context.rounding = rounding
            if target == 0:
                exact = evidence_fraction(favorable, unfavorable)
                bounds.append(Decimal(exact.numerator) / Decimal(exact.denominator))
                continue
            if target >= 0:
                denominator = 1 + target
                plus, zero, minus = Decimal(2) / denominator, Decimal(1) / denominator, Decimal(0)
            else:
                denominator = 1 - target
                plus, zero, minus = Decimal(2), (1 - 2 * target) / denominator, (-2 * target) / denominator
            # Largest nonzero group is built directly using its binomial
            # expansion. Zero factors retain n in the integral denominators.
            groups = [(count, value) for count, value in
                      ((favorable, plus), (unfavorable, minus), (n-favorable-unfavorable, zero))
                      if count and value]
            groups.sort(key=lambda group: group[0], reverse=True)
            coefficients = [Decimal(1)]
            if groups:
                count, value = groups[0]
                choose, power = 1, Decimal(1)
                for k in range(1, count + 1):
                    choose = choose * (count-k+1) // k
                    power *= value
                    coefficients.append(Decimal(choose) * power)
                for count, value in groups[1:]:
                    for _ in range(count):
                        coefficients.append(Decimal(0))
                        for k in range(len(coefficients)-1, 0, -1):
                            coefficients[k] += value * coefficients[k-1]
            # Exact integer recurrence avoids recomputing C(n,k) from scratch.
            choose, total = 1, Decimal(0)
            for k, coefficient in enumerate(coefficients):
                total += coefficient / Decimal(choose)
                choose = choose * (n-k) // (k+1)
            bounds.append(total / Decimal(n+1))
    return tuple(bounds)


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
