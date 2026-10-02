import pytest
from analyze_roboboat_atomic_reassessment import score_decisions,aggregate


def decisions(label='SUPPORTED_BY_VISIBLE_EVIDENCE'):
    return {'claim:one':label,**{f'unit:{i}':True for i in range(4)},
        'limitation:one':True,'highest_asserted_abstraction_level':'specific_physical_cause'}


def test_unsupported_or_unknown_claim_is_adverse_and_unqualified_tag_does_not_score():
    d=decisions();assert score_decisions(d)['answer_success']
    d['claim:extra']='PHYSICALLY_TRUE_BUT_NOT_SUPPORTED'
    assert not score_decisions(d)['answer_success']
    assert not score_decisions(decisions('UNINTERPRETABLE'))['answer_success']
    d=decisions();d['unit:0']=False
    assert not score_decisions(d)['answer_success']
    d=decisions();d['limitation:one']=False
    assert not score_decisions(d)['answer_success']


def test_empty_claim_inventory_or_missing_unit_cannot_pass_vacuously():
    d=decisions();del d['claim:one']
    with pytest.raises(ValueError,match='incomplete'):score_decisions(d)
    d=decisions();del d['unit:0']
    with pytest.raises(ValueError,match='incomplete'):score_decisions(d)
    d=decisions();d['unit:0']=None
    with pytest.raises(ValueError,match='boolean'):score_decisions(d)


def rows(batch,b2=True,b4=True):
    return [{'batch':batch,'method':method,'level':level,
        **{view:{'answer_success':value} for view in ('final','pass_A','pass_B')}}
        for method,value in [('B2',b2),('B4',b4)] for level in ('L0','L1','L2')]


def test_pairs_not_ladders_or_passes_determine_n_and_unpaired_variant_is_reported():
    values=rows('a')+rows('b')+rows('c',False,True)+rows('d',False,True)+rows('e',False,True)
    result=aggregate(values,{'a':'pair1','b':'pair1','c':'pair2','d':'pair2','e':'incomplete'})
    assert result['fresh_recordings']==5 and result['complete_paired_clusters']==2
    assert result['observed_mean_cluster_difference']=={'final':.5,'pass_A':.5,'pass_B':.5}
    assert result['clusters'][0]['complete_pair'] is False
    assert result['clusters'][0]['scores'] is None
    assert result['p_value'] is None and result['confidence_interval'] is None
    assert result['sensitivity_is_confidence_interval'] is False


def test_judge_sensitivity_preserves_disagreement_instead_of_adding_n():
    values=rows('a')+rows('b')
    values[0]['pass_A']['answer_success']=False
    result=aggregate(values,{'a':'pair','b':'pair'})
    assert result['complete_paired_clusters']==1
    assert result['observed_mean_cluster_difference']['pass_A']==pytest.approx(1/6)
    assert result['observed_mean_cluster_difference']['final']==0
    assert result['judge_pass_sensitivity_range']==[0,pytest.approx(1/6)]


def test_duplicates_incomplete_ladders_and_unregistered_configurations_fail_closed():
    values=rows('a');mapping={'a':'pair'}
    with pytest.raises(ValueError,match='duplicate'):aggregate(values+values,mapping)
    with pytest.raises(ValueError,match='incomplete'):aggregate(values[:-1],mapping)
    with pytest.raises(ValueError,match='unregistered physical'):aggregate(values,{})
