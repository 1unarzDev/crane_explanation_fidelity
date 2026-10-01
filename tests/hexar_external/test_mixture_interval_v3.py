from fractions import Fraction

import pytest

from analysis.hexar_external.confirmatory_v1 import mixture_statistics as original
from analysis.hexar_external.confirmatory_v1 import mixture_interval_v3 as candidate


def exact_integral(f, u, n, mu):
    # Independent direct rational polynomial, including zero and tied factors.
    coefficients = [Fraction(1)]
    for d in [1]*f + [-1]*u + [0]*(n-f-u):
        factor = Fraction(d-mu, 1+abs(mu))
        updated = [Fraction(0)]*(len(coefficients)+1)
        for k, c in enumerate(coefficients):
            updated[k] += c
            updated[k+1] += c*factor
        coefficients = updated
    return sum(c/(k+1) for k, c in enumerate(coefficients))


def test_directed_grouped_bounds_enclose_independent_exact_polynomial():
    for n in range(1, 10):
        for f in range(n+1):
            for u in range(n-f+1):
                for mu in (Fraction(-1), Fraction(-2, 5), Fraction(0), Fraction(1, 5), Fraction(1)):
                    decimal = str(float(mu))
                    lo, hi = candidate.integral_bounds(f, u, n, decimal, precision=30)
                    exact = exact_integral(f, u, n, mu)
                    assert Fraction(lo) <= exact <= Fraction(hi)


def test_full_summary_preserves_adopted_decision_and_interval_inversion():
    for f, u, n in ((0,0,6), (0,6,6), (6,0,6), (5,1,12), (40,32,72), (63,51,114)):
        assert candidate.summary(f, u, n) == original.summary(f, u, n)


@pytest.mark.parametrize('mu', ['NaN', 'Infinity', '1.1', '-1.1'])
def test_invalid_effects_still_fail_closed(mu):
    with pytest.raises(ValueError):
        candidate.integral_bounds(2, 1, 6, mu)


def test_tiny_effect_and_near_boundary_beta_sums_enclose_exact_integrals():
    from decimal import Decimal
    for f,u in ((0,8),(1,7),(4,4),(8,0)):
        for value in ('-1e-80','1e-80','-0.999999999999999999999999999999',
                      '0.999999999999999999999999999999'):
            target = Decimal(value)
            lo,hi = candidate.integral_bounds(f,u,f+u,target,precision=30)
            exact = exact_integral(f,u,f+u,Fraction(target))
            assert Fraction(lo) <= exact <= Fraction(hi)


def test_completed_runtime_summaries_match_retained_original_exact_results():
    import json
    from pathlib import Path
    base = Path(__file__).resolve().parents[2]/'manifests/hexar_external/confirmatory_v1'
    old = json.loads((base/'analysis_runtime_screen_v1/report.json').read_text())
    new = json.loads((base/'analysis_runtime_screen_v3/report.json').read_text())
    assert all(r['status']=='COMPLETE' for r in new['rows'])
    assert [r['parsed'] for r in old['rows'][:3]] == [r['parsed'] for r in new['rows'][:3]]
    assert new['rows'][3]['n'] == 3072
