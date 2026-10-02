"""Synthetic scheduling fixtures only; no development outcomes enter inference."""
import copy
import pytest
from analysis.hexar_external.confirmatory_v1.blind_bank import PACKET_KEYS
from analysis.hexar_external.confirmatory_v1.unique_request_plan import build
from analysis.hexar_external.confirmatory_v1.unique_analysis_binding import verify
from analysis.hexar_external.confirmatory_v1.journal import fingerprint


def fixture():
    entries=[];jobs=[];expected=set()
    for episode in ('SYNTHETIC-A','SYNTHETIC-B'):
        for method in ('HX-CONTRACT','HX-PROMPT'):
            for question in ('q1','q2','q3'):
                for condition in ('intact','irrelevant_removal','diagnostic_removal'):
                    packet={key:{} for key in PACKET_KEYS}
                    packet.update(question=question,evidence={'removed':condition=='diagnostic_removal'})
                    entries.append(dict(episode_id=episode,method=method,job_id=question+'-'+condition,
                        packet=packet,implementation_binding={'fixture':'NO_PROVIDER_OR_PHYSICAL_EPISODE'}))
                    expected.add((episode,method,question,condition))
    plan=build(entries);plan.update(status='SEALED_FOR_CONFIRMATORY_GENERATION',
        implementation_binding_qualified=True,binding_freeze_sha256='SYNTHETIC-FREEZE')
    for row in plan['aliases']:
        question,condition=row['job_id'].split('-',1);uid=row['unique_request_id']
        jobs.append(dict(recording_id=row['episode_id'],method=row['method'],question_id=question,condition=condition,
            source_unique_request_id=uid,response_sha256='synthetic-output-'+uid,scoring_artifact_sha256='synthetic-score-'+uid,
            unsupported_material=None,overlicensed_specificity=None,missing_required_unit=None))
    return dict(unique_request_plan=plan,unique_request_plan_sha256=fingerprint(plan),jobs=jobs),expected


def test_closed_identical_missingness_aliases_pass_without_more_observations():
    bundle,expected=fixture()
    verify(bundle,expected,'SYNTHETIC-FREEZE')
    assert len(bundle['jobs'])==36 and bundle['unique_request_plan']['unique_requests']==24


@pytest.mark.parametrize('field',['response_sha256','scoring_artifact_sha256','unsupported_material','overlicensed_specificity','missing_required_unit'])
def test_alias_output_or_label_mutation_fails_before_primary_analysis(field):
    bundle,expected=fixture();job=next(j for j in bundle['jobs'] if j['condition']=='intact')
    other=next(j for j in bundle['jobs'] if j is not job and j['source_unique_request_id']==job['source_unique_request_id'])
    other[field]='changed' if 'sha256' in field else True
    with pytest.raises(ValueError,match='different raw output'):
        verify(bundle,expected,'SYNTHETIC-FREEZE')


@pytest.mark.parametrize('mutation',['wrong_freeze','not_sealed','unqualified','wrong_uid','missing_component','missing_alias','stale_hash'])
def test_incomplete_or_wrong_unique_schedule_fails_closed(mutation):
    bundle,expected=fixture();plan=bundle['unique_request_plan']
    if mutation=='wrong_freeze':plan['binding_freeze_sha256']='other'
    elif mutation=='not_sealed':plan['status']='PURE_PLAN_NOT_ADMITTED'
    elif mutation=='unqualified':plan['implementation_binding_qualified']=False
    elif mutation=='wrong_uid':bundle['jobs'][0]['source_unique_request_id']='other'
    elif mutation=='missing_component':del bundle['jobs'][0]['unsupported_material']
    elif mutation=='missing_alias':bundle['jobs'].pop()
    else:plan['semantic_calls']=1
    if mutation!='stale_hash':bundle['unique_request_plan_sha256']=fingerprint(plan)
    with pytest.raises(ValueError):verify(bundle,expected,'SYNTHETIC-FREEZE')
