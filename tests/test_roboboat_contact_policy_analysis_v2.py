import copy
import pytest
from adjudicate_evidence_calibration_annotations import _item_id
from analyze_roboboat_contact_policy_support_v2 import score,summarize
from roboboat_material_endpoint_v1 import UNITS,PARTIAL_UNIT,LIMITS,SUPPORTED


def decisions(partial=False):
    return {'claim:c1':SUPPORTED,**{'unit:'+_item_id('u-',u):True for u in UNITS+((PARTIAL_UNIT,) if partial else ())},**{'limitation:'+_item_id('l-',l):True for l in LIMITS}}


def test_unsupported_claim_or_whole_answer_overclaim_fails_despite_units():
    d=decisions();d['claim:c1']='INSUFFICIENT_VISIBLE_EVIDENCE'
    assert not score(d,False)['strict_common_success']
    d=decisions();d['limitation:'+_item_id('l-',LIMITS[1])]=False
    assert not score(d,False)['strict_common_success']


def test_partial_compliance_omission_only_fails_extended_sensitivity():
    d=decisions(True);d['unit:'+_item_id('u-',PARTIAL_UNIT)]=False
    s=score(d,True)
    assert s['strict_common_success'] and not s['strict_extended_success']
    assert not s['material_primary_score_authorized']


@pytest.mark.parametrize('mode',['empty','missing','extra','unknown','bad-bool'])
def test_no_vacuous_partial_or_unknown_score_release(mode):
    d=decisions()
    if mode=='empty':d.pop('claim:c1')
    elif mode=='missing':d.pop('unit:'+_item_id('u-',UNITS[0]))
    elif mode=='extra':d['unit:extra']=True
    elif mode=='unknown':d['claim:c1']=None
    else:d['limitation:'+_item_id('l-',LIMITS[0])]=1
    with pytest.raises(ValueError):score(d,False)


def rows():
    out=[]
    for variant in ('opaque-existing-a','opaque-existing-b'):
        for level in ('L0','L1','L2'):
            for method in ('B2','B4'):
                scored=score(decisions(level=='L2'),level=='L2')
                out.append({'response_id':variant+'-'+level,'method':method,'partial_information_answerable':level=='L2',**{view:copy.deepcopy(scored) for view in ('pass_A','pass_B','final')}})
    return out


def test_complete_replay_uses_six_answers_per_method_and_no_new_independent_N():
    r=summarize(rows())
    assert r['new_independent_configuration_n']==0 and not r['paired_cluster_effect_estimated']
    assert r['p_value'] is None and r['confidence_interval'] is None
    for method in ('B2','B4'):
        assert r['methods'][method]['final']['answers']==6
        assert r['methods'][method]['final']['partial_compliance_communicated']==2


@pytest.mark.parametrize('mode',['missing','duplicate','wrong-level'])
def test_partial_or_duplicated_population_cannot_release(mode):
    r=rows()
    if mode=='missing':r.pop()
    elif mode=='duplicate':r[-1]=r[0]
    else:r[-1]['response_id']='opaque-existing-b-L3'
    with pytest.raises(ValueError):summarize(r)
