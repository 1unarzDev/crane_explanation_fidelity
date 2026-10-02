from fractions import Fraction
import pytest

from analysis.hexar_external.acquisition.technical_reliability import upper_bound, summarize


def test_zero_failure_bound_and_conservative_direction():
    bound = upper_bound(0, 24)
    exact_float = 1 - (1/120)**(1/24)
    assert float(bound) == pytest.approx(exact_float, abs=4e-15)
    assert (1-bound)**24 <= Fraction(1, 120)
    assert bound < Fraction(1, 5)
    assert upper_bound(1, 24) > Fraction(1, 5)
    assert upper_bound(24, 24) == 1


def test_closed_complete_schedule_and_no_failure_replacement():
    families = [str(i) for i in range(6)]
    rows = [dict(episode_id=f'{family}-{j}', family=family, technical_valid=True)
            for family in families for j in range(24)]
    assert summarize(rows, families)['engineering_criterion_passed']
    rows[0]['technical_valid'] = False
    result = summarize(rows, families)
    assert not result['engineering_criterion_passed']
    assert result['families'][0]['technical_invalid'] == 1
    assert result['families'][0]['attempts'] == 24
    for missing in (rows[:-1], [dict(r, technical_valid=None) for r in rows]):
        with pytest.raises(ValueError):
            summarize(missing, families)
