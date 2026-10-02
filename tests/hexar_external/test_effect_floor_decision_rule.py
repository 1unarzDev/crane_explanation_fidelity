from fractions import Fraction
import json
import math
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.effect_floor_decision_rule import (
    homogeneous_power,technical_failure_probability,reserve,regimes,
)
from analysis.hexar_external.confirmatory_v1.mixture_statistics import critical_count,power


def test_enumerated_probability_matches_independent_standard_library_small_n():
    n=24
    thresholds=[critical_count(m) for m in range(n+1)]
    for d in (.1,.25,.5,1.):
        for q in (.55,.8,1.):
            assert homogeneous_power(n,d,q,thresholds)==pytest.approx(power(n,d,q),abs=1e-12)


def test_exact_reserve_recurrence_matches_direct_binomial_sum_and_minimum_cap():
    for quota in (1,3,8):
        for attempts in (quota,quota+5):
            for p in (Fraction(1,20),Fraction(1,10),Fraction(1,5)):
                direct=sum((Fraction(math.comb(attempts,k))*(1-p)**k*p**(attempts-k)
                            for k in range(quota)),Fraction(0))
                assert technical_failure_probability(quota,attempts,p)==direct
        p=Fraction(1,5)
        row=reserve(quota,p)
        cap=row['maximum_attempts_per_family']
        assert 1-6*technical_failure_probability(quota,cap,p)>=Fraction(99,100)
        assert cap==quota or 1-6*technical_failure_probability(quota,cap-1,p)<Fraction(99,100)


def test_grid_recommendation_is_conditional_and_every_primary_family_mean_is_preserved():
    base=Path(__file__).resolve().parents[2]/'manifests/hexar_external/confirmatory_v1'
    r=json.loads((base/'effect_floor_decision_rule_v1.json').read_text())
    assert r['final_n'] is None and r['accepted_effect_floor'] is None
    assert r['confirmatory_N']==r['alpha_consumed']==0
    assert r['conditional_grid_recommendation']==3072
    assert len(r['rows'])==108
    for scenario in regimes():
        assert sum(scenario['effects'])/6==pytest.approx(.1 if scenario['primary'] else .3)
        assert all(abs(effect)<=d+1e-12 for effect,d in zip(scenario['effects'],scenario['discordance']))
    assert all(row['simultaneous_MC_lower']>=.9 for row in r['rows'] if row['n']==3072 and row['primary'])
    for n in (72,114,768,1296,1920):
        assert any(row['simultaneous_MC_lower']<.9 for row in r['rows'] if row['n']==n and row['primary'])
