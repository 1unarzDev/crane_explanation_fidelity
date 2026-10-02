"""Terminal analysis executes one bound statistic with exact primary decision."""
import copy
import pytest
from test_confirmatory_v1 import fixture_bundle
from analysis.hexar_external.confirmatory_v1 import analyze

PLAN=dict(primary_procedure='fixed_n_uniform_paired_mixture',alpha=.01,
          mixture_density='uniform',mixture_support=[0,1])


def twelve_episode_fixture():
    bundle,cohort,battery=fixture_bundle()
    records=[];jobs=[]
    for old in cohort['records']:
        for repetition in range(2):
            record=dict(old,recording_id=old['recording_id']+f'-{repetition}');records.append(record)
            for job in bundle['jobs']:
                if job['recording_id']==old['recording_id']:
                    jobs.append(dict(job,recording_id=record['recording_id'],
                        unsupported_material=job['method']=='HX-PROMPT' and len(records)<=9))
    cohort['records']=records;bundle['jobs']=jobs
    return bundle,cohort,battery


def test_one_bound_mixture_reports_four_cells_and_corresponding_interval(monkeypatch):
    bundle,cohort,battery=twelve_episode_fixture()
    def other_test(*args,**kwargs):pytest.fail('another primary test must not run')
    monkeypatch.setattr(analyze,'summary',other_test)
    monkeypatch.setattr(analyze,'e_summary',other_test)
    monkeypatch.setattr(analyze,'cp_bounds',other_test)
    result=analyze.analyze(bundle,cohort,battery,'test-freeze',PLAN)
    primary=result['primary']
    assert result['confirmatory_n']==12 and len(bundle['jobs'])==216
    assert [primary[k] for k in ('favorable','unfavorable','both_success','both_failure')]==[9,0,3,0]
    assert primary['prompt_failure_rate']==.75 and primary['contract_failure_rate']==0
    assert primary['conservative_one_sided_p']==pytest.approx(10/1023)
    assert primary['one_sided_99_lower_bound']>0
    assert result['superiority'] is True
    assert not result['interval_and_test_disagreement_possible']


def test_rounded_p_never_overrides_exact_rational_nonrejection(monkeypatch):
    bundle,cohort,battery=fixture_bundle()
    monkeypatch.setattr(analyze,'mixture_summary',lambda *args:dict(
        one_sided_p_value=.01,reject=False,one_sided_lower=-.1,two_sided_interval=[-.1,.5]))
    result=analyze.analyze(bundle,cohort,battery,'test-freeze',PLAN)
    assert result['superiority'] is False
    assert 'did not establish' in result['claim']


def test_boolean_attempt_count_is_not_one_frozen_semantic_attempt():
    bundle,cohort,battery=fixture_bundle();bundle['jobs'][0]['attempt_count']=True
    with pytest.raises(ValueError,match='retry'):
        analyze.analyze(bundle,cohort,battery,'test-freeze',PLAN)


@pytest.mark.parametrize('change', ['fraction','density','support','boolean_support','alpha','unknown_test'])
def test_incompatible_plan_cannot_silently_choose_another_test(change):
    bundle,cohort,battery=fixture_bundle();plan=copy.deepcopy(PLAN)
    if change=='fraction':plan['betting_fraction']=.4
    elif change=='density':plan['mixture_density']='best empirical fraction'
    elif change=='support':plan['mixture_support']=[.2,.8]
    elif change=='boolean_support':plan['mixture_support']=[False,True]
    elif change=='alpha':plan['alpha']=.02
    else:plan['primary_procedure']='choose_smallest_p'
    with pytest.raises(ValueError):analyze.analyze(bundle,cohort,battery,'test-freeze',plan)
