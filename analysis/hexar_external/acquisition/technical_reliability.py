"""Exact binomial technical-invalidity bounds for development reserve planning.

These describe acquisition reliability, not a semantic superiority hypothesis.
The within-family identical-process/independence assumptions remain explicit.
"""
from fractions import Fraction
from math import comb


def cdf(k, n, p):
    return sum((Fraction(comb(n, i)) * p**i * (1-p)**(n-i)
                for i in range(k+1)), Fraction(0))


def upper_bound(k, n, tail=Fraction(1, 120), iterations=48):
    if (type(n) is not int or n < 1 or type(k) is not int or not 0 <= k <= n
            or not isinstance(tail, Fraction) or not 0 < tail < 1
            or type(iterations) is not int or iterations < 1):
        raise ValueError('integer failure/attempt counts and exact tail probability required')
    if k == n:
        return Fraction(1)
    lo, hi = Fraction(0), Fraction(1)
    for _ in range(iterations):
        mid = (lo+hi)/2
        if cdf(k, n, mid) > tail:
            lo = mid
        else:
            hi = mid
    return hi  # Conservative outward bound; never round downward for a decision.


def summarize(rows, families, attempts_per_family=24):
    if len(set(families)) != 6 or len(rows) != 6 * attempts_per_family:
        raise ValueError('complete fixed six-family reliability campaign required')
    if len({r['episode_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate qualification attempt')
    if any(type(r.get('technical_valid')) is not bool for r in rows):
        raise ValueError('all technical dispositions must be closed explicitly')
    if set(r['family'] for r in rows) != set(families):
        raise ValueError('undeclared or missing qualification family')
    output = []
    for family in families:
        group = [r for r in rows if r['family'] == family]
        if len(group) != attempts_per_family:
            raise ValueError('fixed qualification quota changed')
        failures = sum(not r['technical_valid'] for r in group)
        bound = upper_bound(failures, len(group))
        output.append(dict(family=family, attempts=len(group), technical_invalid=failures,
                           observed_invalid_rate=failures/len(group),
                           upper_bound=float(bound), exact_upper_bound=str(bound),
                           candidate_20_percent_ceiling_met=bound <= Fraction(1, 5)))
    return dict(families=output, all_attempts_valid=all(r['technical_valid'] for r in rows),
        engineering_criterion_passed=all(r['technical_valid'] for r in rows)
            and all(r['candidate_20_percent_ceiling_met'] for r in output),
        simultaneous_planning_coverage=.95, per_family_tail_exact='1/120',
        assumptions='independent identically generated technical-validity outcomes within each fixed family',
        semantic_inference=False, alpha_consumed=0)
