from fractions import Fraction as F

import pytest

from analysis.hexar_external.confirmatory_v1.h1_rule_candidate_v1 import decision


def row(**changes):
    values = dict(look='FINAL', n=1200, favorable=7, unfavorable=0,
                  both_pass=1193, both_fail=0, b4_mean_coverage=F(95, 100),
                  coverage_difference=F(-5, 100))
    values.update(changes)
    return decision(**values)


def test_exact_threshold_and_both_coverage_boundaries():
    result = row()
    assert result['exact_p'] == F(1, 128)
    assert result['primary_scientific_success']
    assert not result['h2_activation_authorized']
    assert not result['full_h1_procedure_validity_attested']
    assert not row(favorable=6, both_pass=1194)['primary_scientific_success']
    assert not row(b4_mean_coverage=F(949, 1000))['primary_scientific_success']
    assert not row(b4_mean_coverage=F(94, 100), coverage_difference=F(-51, 1000))['primary_scientific_success']


def test_direction_and_reverse_discordance_are_preserved():
    assert row(favorable=0, unfavorable=7)['exact_p'] == 1
    assert not row(favorable=0, unfavorable=7)['primary_scientific_success']
    assert row(favorable=7, unfavorable=1, both_pass=1192)['exact_p'] == F(9, 256)
    assert not row(favorable=7, unfavorable=1, both_pass=1192)['primary_scientific_success']


def test_first_look_can_only_stop_for_zero_discordance_or_continue():
    zero = row(look='FIRST', n=600, favorable=0, both_pass=600)
    assert zero['exact_p'] == 1 and not zero['primary_scientific_success']
    positive = row(look='FIRST', n=600, favorable=10, both_pass=590)
    assert positive['exact_p'] is None
    assert positive['disposition'] == 'CONTINUE_TO_FROZEN_FINAL_N'
    assert not positive['terminal_gate_decision_available']


def test_shortfall_does_not_get_a_nominal_positive_p_value():
    short = row(n=599, favorable=10, both_pass=589)
    assert short['exact_p'] is None and not short['primary_scientific_success']
    assert not short['terminal_gate_decision_available']


@pytest.mark.parametrize('changes', [dict(favorable=True), dict(n=-1),
    dict(both_pass=1192), dict(look='UNFROZEN_INTERIM'), dict(b4_mean_coverage=.95),
    dict(coverage_difference=F(-51, 1000))])
def test_wrong_units_accounting_or_look_fail(changes):
    with pytest.raises(ValueError):
        row(**changes)
