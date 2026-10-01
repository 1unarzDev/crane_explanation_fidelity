"""SIMULATED-only fixed-N intervals with pointwise missing-score bounds.

Decimal inversion and declared numerical slack improve conservativeness; this is
not an interval-arithmetic certification or an anytime-valid study monitor.
"""
import math
from collections import Counter
from decimal import Decimal, localcontext
import numpy as np
from roboboat_fixed_bet_sensitivity_v1 import checked_bets
from roboboat_fixed_n_interval_design_v1 import scores_checked

DECIMAL_PRECISION = 80
BISECTION_STEPS = 180
NUMERICAL_MARGIN = 1e-12
LOW_ENDPOINT_OFFSET = Decimal('1e-30')


def _decimal_log_e(x, m, lambdas, weights):
    logs = []
    for lam in lambdas:
        logs.append(sum((count*(1-lam+lam*(d+1)/(1+m)).ln() for d,count in x.items()), Decimal(0)))
    top = max(logs)
    return top + sum((w*(v-top).exp() for w,v in zip(weights,logs)), Decimal(0)).ln()


def lower_bound(scores, lambdas, weights, *, alpha=.025, origin='SIMULATED'):
    """Lower inversion bracket minus fixed numerical slack, clipped to support.

    The margin is an engineering safeguard, not a proof bounding Decimal error
    for every possible N/parameter. Input float values are the declared values.
    """
    x = scores_checked(scores, origin)
    lam, weight = checked_bets(lambdas, weights)
    if not math.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('alpha in (0,1) required')
    with localcontext() as ctx:
        ctx.prec = DECIMAL_PRECISION
        dx = Counter(Decimal.from_float(float(v)) for v in x)
        dl = [Decimal.from_float(float(v)) for v in lam]
        dw = [Decimal.from_float(float(v)) for v in weight]
        # Treat normalized fixed weights as summing to exactly one in the
        # high-precision statistic, rather than retaining float summation error.
        denominator = sum(dw, Decimal(0))
        dw = [w/denominator for w in dw]
        critical = -Decimal.from_float(float(alpha)).ln()
        lo, hi = Decimal(-1)+LOW_ENDPOINT_OFFSET, Decimal(1)
        if _decimal_log_e(dx, lo, dl, dw) < critical:
            return -1.0
        for _ in range(BISECTION_STEPS):
            middle = (lo+hi)/2
            if _decimal_log_e(dx, middle, dl, dw) >= critical:
                lo = middle
            else:
                hi = middle
        guarded = lo-Decimal(str(NUMERICAL_MARGIN))
        return max(-1.0, math.nextafter(float(guarded), -math.inf))


def interval(adverse_scores, favorable_scores, lambdas, weights, *, alpha_per_tail=.025,
             origin='SIMULATED'):
    """Return L(adverse), U(favorable), never both tails on adverse scores.

    Missingness can be informative: require only pointwise adverse<=latent<=
    favorable. Independence applies to latent complete geometry scores, not to
    missingness. Geometry identity/order matching is the caller's responsibility.
    """
    adverse = scores_checked(adverse_scores, origin)
    favorable = scores_checked(favorable_scores, origin)
    if adverse.shape != favorable.shape or np.any(adverse > favorable):
        raise ValueError('matching N and pointwise adverse<=favorable required')
    result = [lower_bound(adverse, lambdas, weights, alpha=alpha_per_tail, origin=origin),
              -lower_bound(-favorable, lambdas, weights, alpha=alpha_per_tail, origin=origin)]
    if result[0] > result[1]:
        raise ArithmeticError('inconsistent numerical confidence brackets')
    return result
