from analysis.hexar_external.existing_v16_exploratory_v1.analyze import paired_report
from analysis.hexar_external.existing_v16_exploratory_v1.inventory import FAMILIES


def cohort(c='PASS',p='PASS'):
    return [dict(family=f,states={'HX-CONTRACT':c,'HX-PROMPT':p}) for f in FAMILIES for _ in range(6)]


def test_four_paired_directions_and_episode_denominator():
    rows=cohort()
    rows[0]['states']['HX-PROMPT']='FAIL'
    rows[1]['states']['HX-CONTRACT']='FAIL'
    rows[2]['states']={'HX-CONTRACT':'FAIL','HX-PROMPT':'FAIL'}
    v=paired_report(rows)
    assert v['scheduled_n']==36 and v['complete_paired_n']==36
    assert list(v['paired_cells'].values())==[1,1,33,1]
    assert v['complete_case_risk_difference']==0
    assert v['exploratory_one_sided_e_value_derived_p']==1


def test_unknown_never_improves_conservative_contract_effect():
    rows=cohort('PASS','FAIL');before=paired_report(rows)
    rows[0]['states']={'HX-CONTRACT':'UNRESOLVED','HX-PROMPT':'UNRESOLVED'}
    after=paired_report(rows)
    assert after['complete_paired_n']==35 and after['unknown_paired_n']==1
    assert after['full_scheduled_observed_effect_bounds']==[34/36,1]
    assert after['exploratory_one_sided_e_value_derived_p']>=before['exploratory_one_sided_e_value_derived_p']


def test_all_unfinished_cohort_stays_in_denominator_and_has_no_complete_case():
    v=paired_report(cohort('UNRESOLVED','UNRESOLVED'))
    assert v['scheduled_n']==36 and v['complete_paired_n']==0
    assert v['full_scheduled_observed_effect_bounds']==[-1,1]
    assert v['complete_case_risk_difference'] is None
    assert v['complete_case_stratified_bootstrap_95_interval'] is None
    assert v['exploratory_one_sided_e_value_derived_p']==1


def test_family_bootstrap_reproducible_and_adverse_results_preserved():
    rows=cohort('FAIL','PASS');v=paired_report(rows)
    assert v['complete_case_risk_difference']==-1
    assert v['complete_case_stratified_bootstrap_95_interval']==[-1,-1]
    assert v==paired_report(rows)
    assert all(r['net_wins']==-6 for r in v['family_sensitivity'].values())
