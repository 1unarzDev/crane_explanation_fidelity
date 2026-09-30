import copy
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
from report_evidence_calibration_five_methods_v2 import report,DECLARATION
from test_evidence_calibration_analysis import five_method_dataset,plan,response
from analyze_evidence_calibration_five_methods import analyze_five_methods


def declaration():return json.loads(DECLARATION.read_text())


def test_all_contrasts_include_rates_coverage_and_original_effects_p_values():
    data=five_method_dataset();p=plan();old=analyze_five_methods(data,p,declaration())
    output=report(data,p,declaration())
    assert set(output['comparisons'])=={'B0','B1','B2','B3'}
    for method,row in output['comparisons'].items():
        assert row['independent_paired_episode_count']==4
        assert row['method_failure_rates'][method]==row['method_failures'][method]/4
        assert row['method_failure_rates']['B4']==row['method_failures']['B4']/4
        assert row['useful_coverage']['B4']['supported_diagnostic_recall']==1
        assert row['confirmatory_rejection_decision'] is None
        interval=row['whole_episode_percentile_bootstrap_interval']
        assert interval['nominal_confidence_level']==0.95 and not interval['multiplicity_adjusted']
        if method=='B2':
            reference=old['primary_b2_vs_b4']['paired_primary']
            assert row['b4_minus_comparator_absolute_risk_difference']==reference['b4_minus_b2_risk_difference']
            assert row['holm_adjusted_p_across_three_secondary_method_contrasts'] is None
        else:
            reference=old['secondary_method_family'][method]
            assert row['b4_minus_comparator_absolute_risk_difference']==reference['b4_minus_comparator_risk_difference']
            assert row['holm_adjusted_p_across_three_secondary_method_contrasts']==reference['holm_adjusted_p_across_three_method_contrasts']
        assert row['exact_mcnemar_two_sided_p']==reference['exact_mcnemar_two_sided_p']
        assert interval['bounds']==reference['whole_episode_bootstrap_confidence_interval']


def test_tied_no_discordance_intervals_do_not_claim_equivalence():
    data=five_method_dataset()
    for episode in data['episodes']:
        for method in episode['conditions'][0]['methods']:
            episode['conditions'][0]['methods'][method]=response(False)
    output=report(data,plan(),declaration())
    for row in output['comparisons'].values():
        interval=row['whole_episode_percentile_bootstrap_interval']
        assert interval['bounds']==[0,0] and interval['degenerate'] and interval['zero_is_in_interval']
        assert 'not evidence of population equivalence' in interval['interpretation_note']
        assert not row['equivalence_claim_authorized']
        assert row['exact_mcnemar_two_sided_p']==1


def test_unfavorable_b4_effect_and_inconclusive_corrected_results_remain_present():
    data=five_method_dataset()
    for episode in data['episodes']:
        episode['conditions'][0]['methods']['B3']=response(False)
    row=report(data,plan(),declaration())['comparisons']['B3']
    assert row['b4_minus_comparator_absolute_risk_difference']==0.25
    assert row['effect_direction']=='B4_HIGHER_FAILURE_RISK'
    assert row['holm_adjusted_p_across_three_secondary_method_contrasts']==1
    assert not row['inconclusive_or_unfavorable_result_omitted']


def test_controls_use_actual_method_names_and_do_not_change_primary_n():
    data=five_method_dataset();control=copy.deepcopy(data['episodes'][0]);control['episode_id']='control';control['mechanism_family']='nominal'
    control['conditions'][0]['methods']['B0']=response(False)
    control['conditions'][0]['methods']['B4']=response(True)
    data['episodes'].append(control)
    output=report(data,plan(),declaration())
    row=output['comparisons']['B0'];controls=row['controls_and_secondary_geometry']['nominal']
    assert row['independent_paired_episode_count']==4
    assert controls['method_failures']=={'B0':0,'B4':1} and not controls['pooled_into_primary']
    assert controls['method_failure_rates']=={'B0':0,'B4':1}
    assert not controls['inferential_test_performed']


@pytest.mark.parametrize('field',['treatment','multiplicity','authorization'])
def test_changed_declaration_does_not_silently_change_reporting_family(field):
    declared=declaration()
    if field=='treatment':declared['secondary_method_comparisons']['treatment']='B1'
    elif field=='multiplicity':declared['secondary_method_comparisons']['multiplicity']='NONE'
    else:declared['confirmatory_semantic_output_authorized']=True
    with pytest.raises(ValueError,match='exact bound'):
        report(five_method_dataset(),plan(),declared)


def test_extra_ladder_condition_does_not_increase_episode_n():
    data=five_method_dataset();extra=copy.deepcopy(data['episodes'][0]['conditions'][0]);extra.update(condition_id='extra',level_index=2)
    data['episodes'][0]['conditions'].append(extra)
    assert all(row['independent_paired_episode_count']==4 for row in report(data,plan(),declaration())['comparisons'].values())
