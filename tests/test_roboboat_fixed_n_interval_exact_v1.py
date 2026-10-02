from fractions import Fraction
from itertools import product
import math
import pytest
import roboboat_fixed_n_interval_exact_v1 as exact


def test_root_brackets_certified_by_independent_constant_score_algebra():
    # All D=+1, lambda=1/2, alpha=1/4, N=2:
    # [1/2+1/(1+m)]**2 = 4 has exact root m=-1/3.
    lo, hi = exact.lower_bracket([6, 6], ['1/2'], [1], alpha='1/4')
    assert lo <= Fraction(-1, 3) < hi
    assert hi-lo == Fraction(2, 2**exact.STEPS)
    assert Fraction.from_float(exact.outward_float(lo, -1)) <= lo


def test_heterogeneous_average_null_exact_size_and_outcome_dependent_missingness():
    # Four independent Bernoulli scores, unequal p, average expectation zero.
    ps = list(map(Fraction, ['1/8', '3/8', '5/8', '7/8']))
    rejection = Fraction(0)
    for bits in product([0, 1], repeat=4):
        probability = math.prod(p if b else 1-p for p, b in zip(ps, bits))
        values = [6 if b else -6 for b in bits]
        lam, weights, alpha = exact.settings(['1/4', '3/4'], [1, 2], '1/4')
        ev = exact.e_value(values, Fraction(0), lam, weights)
        if ev*alpha >= 1:
            rejection += probability
        # Hide every favorable observation, deliberately informative missingness.
        adverse = [-6 if b else v for b, v in zip(bits, values)]
        favorable = [6 if b else v for b, v in zip(bits, values)]
        complete = exact.interval(values, values, ['1/4', '3/4'], [1, 2], alpha_per_tail='1/4')
        missing = exact.interval(adverse, favorable, ['1/4', '3/4'], [1, 2], alpha_per_tail='1/4')
        assert Fraction(missing['exact_outer_bounds'][0]) <= Fraction(complete['exact_outer_bounds'][0])
        assert Fraction(missing['exact_outer_bounds'][1]) >= Fraction(complete['exact_outer_bounds'][1])
    assert rejection <= Fraction(1, 4)


def test_missing_all_and_fractional_six_question_scores():
    r = exact.interval([-6]*20, [6]*20, ['1/4'], [1])
    assert r['bounds'] == [-1, 1]
    lo, hi = exact.lower_bracket([-5, -2, 0, 3, 4, 6], ['1/4', '1/2'], [1, 1])
    lam, weight, alpha = exact.settings(['1/4', '1/2'], [1, 1], '1/40')
    assert lo == -1 or exact.e_value([-5, -2, 0, 3, 4, 6], lo, lam, weight)*alpha >= 1
    assert exact.e_value([-5, -2, 0, 3, 4, 6], hi, lam, weight)*alpha < 1


def test_reject_invalid_lattice_or_empirical_activation():
    for values in ([], [0.0], [True], [7], [0]*5001):
        with pytest.raises(ValueError): exact.lower_bracket(values, ['1/4'], [1])
    with pytest.raises(ValueError): exact.lower_bracket([0], ['1/4'], [1], origin='DEVELOPMENT')
    with pytest.raises(ValueError): exact.lower_bracket([0], [.25], [1])
    with pytest.raises(ValueError): exact.interval([1], [0], ['1/4'], [1])
    with pytest.raises(ValueError): exact.interval([0, 1], [1], ['1/4'], [1])
