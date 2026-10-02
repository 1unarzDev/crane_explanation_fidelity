import pytest
from analyze_roboboat_atomic_failure_bounds import bound_aggregate


def rows(batch):
    return [{'batch':batch,'method':method,'level':level,'annotation_status':'FINALIZED_AGENT_ASSESSED',
        **{view:{'answer_success':True} for view in ('final','pass_A','pass_B')}}
        for method in ('B2','B4') for level in ('L0','L1','L2')]


def missing(row):
    row.update(annotation_status='RETAINED_TIMEOUT_SUPPORT_UNAVAILABLE',final=None,pass_A=None,pass_B=None)


def test_missing_paired_judgment_widens_score_without_dropping_configuration():
    values=rows('a')+rows('b');missing(values[0])
    result=bound_aggregate(values,{'a':'pair','b':'pair'})
    assert result['complete_paired_clusters']==1 and result['fresh_recordings']==2
    assert result['mean_cluster_difference_bounds']['final']==[0,pytest.approx(1/6)]
    assert result['identified_final_mean'] is None
    assert result['bounds_are_confidence_intervals'] is False
    assert values[0]['final'] is None


def test_missing_unpaired_judgment_remains_reported_but_cannot_change_declared_pairing():
    values=rows('a')+rows('b')+rows('c');missing(values[-1])
    result=bound_aggregate(values,{'a':'pair','b':'pair','c':'unpaired'})
    assert result['fresh_recordings']==3 and result['complete_paired_clusters']==1
    assert result['mean_cluster_difference_bounds']['final']==[0,0]
    assert result['identified_final_mean']==0
