import copy
import hashlib
import pytest
from analysis.hexar_external.confirmatory_v1.development_unique_methods import prepare
from analysis.hexar_external.confirmatory_v1.unique_result_expansion import expand_outputs,expand_labels


def fixture():
    _,_,plan,_=prepare()
    rows=[dict(unique_request_id=r['unique_request_id'],episode_id=r['episode_id'],method=r['method'],request_sha256=r['request_sha256'],packet_sha256=r['packet_sha256'],status='VALID',answer='bounded answer',answer_sha256=hashlib.sha256(b'bounded answer').hexdigest(),model_calls=int(r['method']=='HX-PROMPT')) for r in plan['requests']]
    return plan,rows


def test_alias_expansion_preserves_bad_outputs_and_never_increases_call_counts():
    plan,rows=fixture();cells=expand_outputs(plan,rows)
    assert len(cells)==108 and sum(c['cell_generation_calls'] for c in cells)==36
    duplicate_id=next(r['source_unique_request_id'] for r in cells if r['is_generation_alias'])
    row=next(r for r in rows if r['unique_request_id']==duplicate_id)
    row.update(status='TECHNICAL_FAILURE',answer=None,answer_sha256=None,error='retained technical failure')
    copies=[c for c in expand_outputs(plan,rows) if c['source_unique_request_id']==duplicate_id]
    assert len(copies)==2 and all(c['status']=='TECHNICAL_FAILURE' for c in copies)
    labels={r['unique_request_id']:dict(status='UNRESOLVED',reason='fixture') for r in rows}
    assert len(expand_labels(plan,labels))==108


@pytest.mark.parametrize('mutation',['duplicate','missing','cross_episode','answer_hash','request_hash'])
def test_unbound_or_cross_cluster_outcomes_fail_closed(mutation):
    plan,rows=fixture();rows=copy.deepcopy(rows)
    if mutation=='duplicate':rows.append(rows[0])
    if mutation=='missing':rows.pop()
    if mutation=='cross_episode':rows[0]['episode_id']='another'
    if mutation=='answer_hash':rows[0]['answer']='changed'
    if mutation=='request_hash':rows[0]['request_sha256']='changed'
    with pytest.raises(ValueError):expand_outputs(plan,rows)
