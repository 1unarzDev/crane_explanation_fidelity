"""Scientific admission, exact test, power, clustering and missingness checks."""
import copy
import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from analysis.hexar_external.confirmatory_v1 import statistics as stats
from analysis.hexar_external.confirmatory_v1 import audit, analyze


def test_exact_tail_and_direction():
    assert stats.paired_p(7,0) == pytest.approx(1/128)
    assert stats.paired_p(0,7) == 1
    assert stats.paired_p(0,0) == 1
    assert stats.paired_p(6,0) > .01
    assert stats.paired_p(7,0) <= .01
    with pytest.raises(ValueError):
        stats.paired_p(-1,2)


def test_conditional_type_one_control_at_every_discordant_n():
    for m in range(73):
        k = stats.rejection_threshold(m)
        assert stats.tail(m,k) <= .01 + 1e-12
        if k <= m and k > 0:
            assert stats.tail(m,k-1) > .01 - 1e-12


def test_exact_power_reproduces_planning_point_and_weaker_regime():
    assert stats.exact_power(72,.5,.8) == pytest.approx(.9031668982721305,abs=1e-9)
    assert stats.exact_power(72,.2,.8) < .4
    assert stats.exact_power(186,.2,.8) >= .9
    assert stats.exact_power(180,.2,.8) < .9
    assert stats.exact_power(72,.5,.5) <= .01


def test_power_matches_direct_multinomial_enumeration():
    n,d,q = 12,.4,.8
    brute = 0.
    for favorable in range(n+1):
        for unfavorable in range(n-favorable+1):
            ties=n-favorable-unfavorable
            if stats.paired_p(favorable,unfavorable) <= .01:
                brute += (math.factorial(n)/(math.factorial(favorable)*math.factorial(unfavorable)*math.factorial(ties))
                          *(d*q)**favorable*(d*(1-q))**unfavorable*(1-d)**ties)
    assert stats.exact_power(n,d,q) == pytest.approx(brute,abs=1e-12)


def test_exact_marginal_bounds_coverage_small_samples():
    # Both tails jointly cover >=.99 at .005 per tail; conservatism intended.
    for n in (1,6,12):
        bounds=[stats.cp_bounds(k,n,.005) for k in range(n+1)]
        for p in (.01,.1,.25,.5,.8,.99):
            coverage=sum(prob for prob,(lo,hi) in zip(stats.pmf(n,p),bounds) if lo<=p<=hi)
            assert coverage >= .99-1e-10
    result=stats.summary(7,0,5,0)
    assert result['prompt_minus_contract_failure_risk_difference']==pytest.approx(7/12)
    assert result['contract_failure_rate']==0
    assert result['one_sided_99_lower_bound'] < result['prompt_minus_contract_failure_risk_difference']


def fixture_bundle():
    families=['charging','dynamic_env','localization','manual_joystick','obstacle','success']
    cohort={'records':[{'recording_id':f'NEW-{i}','family':family} for i,family in enumerate(families)]}
    battery={'questions_by_family':{f:[{'question_id':q,'wording':q} for q in ('q1','q2','q3')] for f in families},
             'evidence_conditions':['intact','irrelevant_removal','diagnostic_removal']}
    jobs=[]
    for r in cohort['records']:
        for method in analyze.METHODS:
            for q in ('q1','q2','q3'):
                for c in battery['evidence_conditions']:
                    jobs.append(dict(recording_id=r['recording_id'],method=method,question_id=q,condition=c,
                                     attempt_count=1,blind_disposition_closed=True,
                                     unsupported_material=method=='HX-PROMPT',overlicensed_specificity=False,
                                     missing_required_unit=False,response_sha256='test-response',scoring_artifact_sha256='test-score'))
    bundle=dict(claim_id=audit.CLAIM,freeze_sha256='test-freeze',blind_scoring_complete=True,
                agent_assessed=True,semantic_generation_after_committed_freeze=True,jobs=jobs)
    return bundle,cohort,battery


def test_analysis_counts_recordings_not_answers():
    bundle,cohort,battery=fixture_bundle()
    result=analyze.analyze(bundle,cohort,battery,'test-freeze')
    assert len(bundle['jobs'])==108
    assert result['confirmatory_n']==6
    assert result['primary']['favorable']==6
    assert result['primary']['one_sided_exact_p']==pytest.approx(1/64)
    assert not result['superiority']
    assert len(result['family_descriptive'])==6


@pytest.mark.parametrize('change',['duplicate','retry','missing','old_claim','unblinded','wrong_type'])
def test_analysis_rejects_invalid_run(change):
    bundle,cohort,battery=fixture_bundle()
    if change=='duplicate':bundle['jobs'].append(copy.deepcopy(bundle['jobs'][0]))
    elif change=='retry':bundle['jobs'][0]['attempt_count']=2
    elif change=='missing':bundle['jobs'].pop()
    elif change=='old_claim':bundle['claim_id']='hexar-descriptive-v3'
    elif change=='unblinded':bundle['jobs'][0]['blind_disposition_closed']=False
    elif change=='wrong_type':bundle['jobs'][0]['unsupported_material']=1
    with pytest.raises(ValueError):
        analyze.analyze(bundle,cohort,battery,'test-freeze')


def test_missing_labels_cannot_help_contract_and_coverage_protected():
    bundle,cohort,battery=fixture_bundle()
    bundle['jobs'][0]['missing_required_unit']=None
    # Any unresolved CRANE job fails its physical recording, even though all
    # other job components are clear; answer-level averaging cannot dilute it.
    result=analyze.analyze(bundle,cohort,battery,'test-freeze')
    assert result['primary']['both_failure']==1
    assert result['primary']['favorable']==5
    # Missing HX-PROMPT label maps that recording to prompt success, unfavorable.
    for job in bundle['jobs']:
        if job['recording_id']=='NEW-0' and job['method']=='HX-PROMPT':
            job['unsupported_material']=False
    next(j for j in bundle['jobs'] if j['recording_id']=='NEW-0' and j['method']=='HX-PROMPT')['unsupported_material']=None
    result=analyze.analyze(bundle,cohort,battery,'test-freeze')
    assert result['primary']['unfavorable']==1
    assert result['primary']['both_failure']==0
    assert result['full_cohort_missingness_effect_bounds'][0] <= result['full_cohort_missingness_effect_bounds'][1]


def test_current_audit_blocks_without_using_replication():
    result=audit.audit()
    assert not result['passed'] and not result['confirmation_authorized']
    assert any('alpha' in error for error in result['errors'])
    assert any('model_version' in error for error in result['errors'])
    assert any('cohort' in error for error in result['errors'])
    assert result['consumed_by_audit']==result['semantic_outputs_generated']==0
    with pytest.raises(ValueError,match='no authorized'):
        analyze.verify_freeze()


def test_every_required_top_field_missing_fails(tmp_path):
    for name in audit.REQUIRED:
        (tmp_path/name).write_bytes((audit.BASE/name).read_bytes())
    name='endpoint.json'
    doc=json.loads((tmp_path/name).read_text())
    del doc['required_units']
    (tmp_path/name).write_text(json.dumps(doc))
    result=audit.audit(tmp_path)
    assert 'endpoint.json: missing required field required_units' in result['errors']


def test_all_original_recordings_permanently_development():
    data=json.loads((audit.BASE/'freshness_ledger.json').read_text())
    assert len(data['records'])==18
    assert data['untouched_original_navigation_recordings']==0
    assert all(r['semantic_outputs_inspected'] and r['status']=='DEVELOPMENT_PERMANENTLY_INELIGIBLE' for r in data['records'])
    assert json.loads((audit.BASE/'post_run_results.json').read_text())['status']=='NOT_RUN'
