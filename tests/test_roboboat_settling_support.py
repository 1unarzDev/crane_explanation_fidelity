import pytest
from analyze_roboboat_settling_support import scores,summarize,PARTIAL_KEY


def decisions():
    return {'claim:one':'SUPPORTED_BY_VISIBLE_EVIDENCE',
        **{f'unit:{i}':True for i in range(4)},'limitation:one':True}


def test_partial_success_coverage_is_separate_from_inherited_correctness():
    value={**decisions(),PARTIAL_KEY:False};result=scores(value,'L2')
    assert result['inherited']['answer_success']
    assert not result['extended_answer_success']
    assert value[PARTIAL_KEY] is False
    value[PARTIAL_KEY]=True;assert scores(value,'L2')['extended_answer_success']
    with pytest.raises(ValueError,match='only at L2'):scores(value,'L1')
    with pytest.raises(ValueError,match='explicitly'):scores(decisions(),'L2')


def test_extra_coverage_does_not_excuse_unsupported_claim_or_unknown_limit():
    value={**decisions(),PARTIAL_KEY:True};value['claim:extra']='UNINTERPRETABLE'
    assert not scores(value,'L2')['extended_answer_success']
    value={**decisions(),PARTIAL_KEY:True};value['limitation:one']=False
    assert not scores(value,'L2')['extended_answer_success']


def test_complete_variant_population_adds_no_cluster_n_and_cannot_replace_original_pairs():
    rows=[]
    for batch in ('boat-terminal-settling-001','boat-terminal-settling-002'):
        for method in ('B2','B4'):
            for level in ('L0','L1','L2'):
                value={**decisions(),**({PARTIAL_KEY:method=='B2'} if level=='L2' else {})}
                row={'batch':batch,'method':method,'level':level}
                row.update({v:scores(value,level) for v in ('final','pass_A','pass_B')});rows.append(row)
    result=summarize(rows)
    assert result['new_independent_cluster_n']==0 and result['p_value'] is None
    assert result['methods']['B2']['final']['extended_successes']==6
    assert result['methods']['B4']['final']['extended_successes']==4
    assert result['methods']['B4']['final']['inherited_successes']==6
    with pytest.raises(ValueError,match='complete fixed'):summarize(rows[:-1])
    with pytest.raises(ValueError,match='complete fixed'):summarize(rows+rows[:1])
