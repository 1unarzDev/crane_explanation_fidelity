"""Synthetic qualification of unchanged H1 arithmetic, not H2 admission.

No filesystem/result reader exists here. Full immutable-result and raw-input
reproduction remains required in a separately qualified activation adapter.
"""
from fractions import Fraction
from math import comb

FREEZE_SHA256 = '77e0c6ac4f8da3eccfeeb5ed31990d504a907953f63e8c19822e4e0c4e540ac2'


def decision(*, look, n, favorable, unfavorable, both_pass, both_fail,
             b4_mean_coverage, coverage_difference):
    values = (n, favorable, unfavorable, both_pass, both_fail)
    if any(type(v) is not int or v < 0 for v in values) or sum(values[1:]) != n:
        raise ValueError('nonnegative whole-episode paired counts must sum to N')
    if look not in ('FIRST', 'FINAL'):
        raise ValueError('unchanged H1 look required')
    if not isinstance(b4_mean_coverage, Fraction) or not isinstance(coverage_difference, Fraction):
        raise ValueError('exact episode-mean coverage fractions required for candidate arithmetic')
    if not 0 <= b4_mean_coverage <= 1 or not -1 <= coverage_difference <= 1:
        raise ValueError('coverage outside its range')
    if not 0 <= b4_mean_coverage - coverage_difference <= 1:
        raise ValueError('implied B2 coverage outside its range')
    base = dict(freeze_sha256=FREEZE_SHA256, h2_activation_authorized=False,
                full_h1_procedure_validity_attested=False, real_h1_results_read=False)
    expected_n = 600 if look == 'FIRST' else 1200
    if n != expected_n:
        return dict(base, disposition='SHORTFALL_OR_WRONG_LOOK_N_NO_POSITIVE_CLAIM',
                    terminal_gate_decision_available=False, primary_scientific_success=False,
                    exact_p=None)
    discordance = favorable + unfavorable
    if look == 'FIRST' and discordance:
        return dict(base, disposition='CONTINUE_TO_FROZEN_FINAL_N',
                    terminal_gate_decision_available=False, primary_scientific_success=False,
                    exact_p=None)
    p = Fraction(sum(comb(discordance, k) for k in range(favorable, discordance+1)), 2**discordance)
    covered = b4_mean_coverage >= Fraction(95, 100) and coverage_difference >= Fraction(-5, 100)
    significant = p <= Fraction(1, 100) and favorable > unfavorable
    return dict(base, disposition='TERMINAL_ARITHMETIC_ONLY', terminal_gate_decision_available=True,
                exact_p=p, significant_superiority=significant,
                useful_coverage_requirement_passed=covered,
                primary_scientific_success=significant and covered)
