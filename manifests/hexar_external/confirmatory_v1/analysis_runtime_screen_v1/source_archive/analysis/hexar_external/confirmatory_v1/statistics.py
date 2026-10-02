"""Prospective paired-recording statistics; standard-library exact enumeration.

Development data are never loaded here. Positive difference = prompt failure
minus contract failure. Conditional binomial test needs exchangeable discordance
signs under the null; the protocol must establish that assumption before freeze.
"""
import math
from functools import lru_cache


def pmf(n, p):
    if n < 0 or not 0 <= p <= 1:
        raise ValueError('invalid binomial parameters')
    if p in (0, 1):
        return [float(k == (n if p else 0)) for k in range(n + 1)]
    return [math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) -
                     math.lgamma(n - k + 1) + k * math.log(p) +
                     (n - k) * math.log1p(-p)) for k in range(n + 1)]


def tail(n, k, p=0.5):
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    return min(1.0, math.fsum(pmf(n, p)[k:]))


def paired_p(favorable, unfavorable):
    if any(type(x) is not int or x < 0 for x in (favorable, unfavorable)):
        raise ValueError('discordances must be nonnegative integers')
    return tail(favorable + unfavorable, favorable)


@lru_cache(None)
def rejection_threshold(m, alpha=0.01):
    probs = pmf(m, 0.5)
    cumulative = 0.0
    threshold = m + 1
    for k in range(m, -1, -1):
        cumulative += probs[k]
        if cumulative <= alpha:
            threshold = k
        else:
            break
    return threshold


@lru_cache(None)
def rejection_prob(m, q, alpha=0.01):
    return tail(m, rejection_threshold(m, alpha), q)


def exact_power(n, discordance, favorable_given_discordance, alpha=0.01):
    return math.fsum(prob * rejection_prob(m, favorable_given_discordance, alpha)
                     for m, prob in enumerate(pmf(n, discordance)))


def cp_bounds(k, n, tail_alpha):
    """Clopper-Pearson marginal bounds with each tail at tail_alpha."""
    def invert(target, count):
        lo, hi = 0.0, 1.0
        for _ in range(70):
            mid = (lo + hi) / 2
            if tail(n, count, mid) < target:
                lo = mid
            else:
                hi = mid
        return (lo + hi) / 2
    return (0.0 if k == 0 else invert(tail_alpha, k),
            1.0 if k == n else invert(1 - tail_alpha, k + 1))


def summary(favorable, unfavorable, both_success, both_failure):
    counts = (favorable, unfavorable, both_success, both_failure)
    if any(type(x) is not int or x < 0 for x in counts) or sum(counts) == 0:
        raise ValueError('invalid four-cell counts')
    n = sum(counts)
    # Bonferroni: P_f lower and P_u upper each spend .005 => lower >=99%.
    # All four tails each .005 => symmetric interval coverage >=98%.
    fl, fu = cp_bounds(favorable, n, 0.005)
    ul, uu = cp_bounds(unfavorable, n, 0.005)
    return dict(n=n, favorable=favorable, unfavorable=unfavorable,
                both_success=both_success, both_failure=both_failure,
                contract_failure_rate=(unfavorable + both_failure) / n,
                prompt_failure_rate=(favorable + both_failure) / n,
                prompt_minus_contract_failure_risk_difference=(favorable - unfavorable) / n,
                one_sided_99_lower_bound=fl - uu,
                two_sided_98_interval=[fl - uu, fu - ul],
                interval_method='conservative Bonferroni marginal exact binomial; IID pairs required; not inversion of conditional McNemar',
                one_sided_exact_p=paired_p(favorable, unfavorable))
