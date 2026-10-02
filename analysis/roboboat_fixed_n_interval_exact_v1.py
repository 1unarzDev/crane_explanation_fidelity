"""SIMULATED-only exact inversion candidate for six-question geometry scores.

Integer numerators preserve the declared endpoint lattice. Rational arithmetic
certifies the inversion bracket; no empirical test, N or betting panel is chosen.
"""
from collections import Counter
from fractions import Fraction
import math

STEPS = 48
MAX_N = 5000


def checked_numerators(values, origin):
    if origin != 'SIMULATED':
        raise ValueError('simulation-only candidate')
    values = list(values)
    if not 0 < len(values) <= MAX_N or any(type(v) is not int or not -6 <= v <= 6 for v in values):
        raise ValueError('1..5000 integer geometry numerators in [-6,6] required')
    return values


def rational(value):
    if isinstance(value, float) or isinstance(value, bool):
        raise ValueError('exact rational strings/integers/Fractions required, no floats')
    return Fraction(value)


def settings(lambdas, weights, alpha):
    lambdas, weights = tuple(map(rational, lambdas)), tuple(map(rational, weights))
    alpha = rational(alpha)
    if not 0 < len(lambdas) == len(weights) <= 8 or any(not 0 < v < 1 for v in lambdas):
        raise ValueError('1..8 positive bets below one required')
    if any(v <= 0 for v in weights) or not 0 < alpha < 1:
        raise ValueError('positive mixture weights and alpha in (0,1) required')
    total = sum(weights)
    return lambdas, tuple(w/total for w in weights), alpha


def e_value(numerators, m, lambdas, weights):
    """Exact mixture at rational m>-1, each D_i = numerator_i/6."""
    counts = Counter(numerators)
    result = Fraction(0)
    for lam, weight in zip(lambdas, weights):
        product = Fraction(1)
        for value, count in counts.items():
            product *= (1-lam+lam*Fraction(value+6, 6)/(1+m)) ** count
        result += weight*product
    return result


def lower_bracket(numerators, lambdas, weights, *, alpha='1/40', origin='SIMULATED'):
    values = checked_numerators(numerators, origin)
    lambdas, weights, alpha = settings(lambdas, weights, alpha)
    if all(v == -6 for v in values):
        return Fraction(-1), Fraction(-1)
    # At least one score exceeds -1, so every positive-bet product diverges
    # at -1. At +1 every factor is <=1 and cannot reach 1/alpha>1.
    lo, hi = Fraction(-1), Fraction(1)
    for _ in range(STEPS):
        middle = (lo+hi)/2
        if e_value(values, middle, lambdas, weights)*alpha >= 1:
            lo = middle
        else:
            hi = middle
    return lo, hi


def outward_float(value, direction):
    candidate = float(value)
    exact_candidate = Fraction.from_float(candidate)
    if (direction < 0 and exact_candidate > value) or (direction > 0 and exact_candidate < value):
        candidate = math.nextafter(candidate, -math.inf if direction < 0 else math.inf)
    return candidate


def interval(adverse_numerators, favorable_numerators, lambdas, weights, *,
             alpha_per_tail='1/40', origin='SIMULATED'):
    adverse = checked_numerators(adverse_numerators, origin)
    favorable = checked_numerators(favorable_numerators, origin)
    if len(adverse) != len(favorable) or any(a > f for a, f in zip(adverse, favorable)):
        raise ValueError('matching ordered geometries and pointwise bounds required')
    lower, lower_inner = lower_bracket(adverse, lambdas, weights, alpha=alpha_per_tail, origin=origin)
    upper_neg, upper_inner_neg = lower_bracket([-v for v in favorable], lambdas, weights,
                                               alpha=alpha_per_tail, origin=origin)
    upper = -upper_neg
    return {'origin': origin, 'inferential_activation_authorized': False,
            'geometry_count': len(adverse), 'score_denominator': 6,
            'bounds': [outward_float(lower, -1), outward_float(upper, 1)],
            'exact_outer_bounds': [str(lower), str(upper)],
            'exact_lower_root_bracket': [str(lower), str(lower_inner)],
            'exact_upper_root_bracket': [str(-upper_inner_neg), str(upper)],
            'maximum_root_bracket_width': str(Fraction(2, 2**STEPS)),
            'anytime_valid': False, 'alpha_consumed': 0}
