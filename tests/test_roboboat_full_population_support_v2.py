import hashlib
import json
from pathlib import Path
import pytest
import run_roboboat_full_population_inventory_v2 as inventory
import run_roboboat_full_population_support_v2 as support
from test_roboboat_full_population_inventory_v2 import population


def reviewed_inventory(tmp_path, *, fail=False):
    path,root,d=population(tmp_path,fail=fail)
    bank=tmp_path/'bank'
    inventory.prepare(path,root,bank,tmp_path/'inventory.json')
    for e in json.loads((bank/'blind-bank.json').read_text())['entries']:
        key,answer=e['opaque_response_id'],e['response_text']
        raws={slot:json.dumps({'case_id':key,'slot':slot,'entry':{'response_text':answer},
            'validation':{'status':'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}}).encode() for slot in ('A','B')}
        returns=bank/'returns';returns.mkdir(exist_ok=True)
        for slot,raw in raws.items(): (returns/f'{key}-{slot}.json').write_bytes(raw)
        review={'status':'COMPLETE_FAITHFUL_PROJECT_REVIEW','opaque_response_id':key,
            'source_text_sha256':key,'project_review_not_human_validation':True,
            'abstraction_tags_discarded':True,'source_assertion_completeness_reviewed':True,
            'extractor_returns_sha256':{slot:hashlib.sha256(raw).hexdigest() for slot,raw in raws.items()},
            'claims':[{'response_span':answer,'claim_text':answer}]}
        reviews=bank/'project_reviews';reviews.mkdir(exist_ok=True)
        (reviews/f'{key}.json').write_text(json.dumps(review))
    return path,root,d,bank


def test_actual_full_support_prepare_and_no_method_metadata_staged_to_judges(tmp_path):
    path,root,d,bank=reviewed_inventory(tmp_path)
    out=tmp_path/'support';decl=tmp_path/'support.json'
    result=support.prepare(bank,path,root,out,decl)
    assert result['schema']=='roboboat-full-population-reviewed-support/v2'
    assert result['original_answers']==6
    assert result['snapshot_entries']==d['entries']
    assert result['judge']['passes']==2 and result['timeout_s']==300
    calls=[]
    def annotator(packet,target,caller):
        p=json.loads(Path(packet).read_text());calls.append(packet)
        assert 'method' not in p and 'generation_provenance' not in p
        assert caller.timeout_s==300
        return {'construction_only':True}
    support.run(decl,out,annotator=annotator);support.run(decl,out,annotator=annotator)
    assert len(calls)==result['unique_support_packets']


def test_full_support_keeps_b2_failure_slots_and_annotates_all_retained_b4(tmp_path):
    path,root,d,bank=reviewed_inventory(tmp_path,fail=True)
    result=support.prepare(bank,path,root,tmp_path/'support',tmp_path/'support.json')
    assert result['original_answers']==3
    ledger=json.loads(support.checked(result['response_accounting']).read_text())
    assert all(e['methods']['B2']=='MISSING_ANSWER' for e in ledger['entries'])
    assert len(result['snapshot_entries'])==3


@pytest.mark.parametrize('attack',['missing-review','unresolved-review','missing-pass'])
def test_extraction_completeness_review_gate_blocks_support_prepare(tmp_path,attack):
    path,root,d,bank=reviewed_inventory(tmp_path)
    review=next((bank/'project_reviews').glob('*.json'))
    if attack=='missing-review': review.unlink()
    elif attack=='unresolved-review':
        value=json.loads(review.read_text());value['status']='ISSUES_REQUIRE_RESOLUTION';review.write_text(json.dumps(value))
    else: next((bank/'returns').glob('*-A.json')).unlink()
    with pytest.raises((ValueError,FileNotFoundError)):
        support.prepare(bank,path,root,tmp_path/'support',tmp_path/'support.json')


def test_no_selective_join_after_inventory_source_freeze(tmp_path):
    path,root,d,bank=reviewed_inventory(tmp_path)
    join=bank/'evaluator-join.json';value=json.loads(join.read_text());value['entries'].pop();join.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='bound input'):
        support.prepare(bank,path,root,tmp_path/'support',tmp_path/'support.json')
