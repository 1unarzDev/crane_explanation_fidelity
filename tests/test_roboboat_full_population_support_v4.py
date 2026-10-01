"""Construction-only availability/admission tests; no study calls or scoring."""
import json
from pathlib import Path
import pytest
import run_roboboat_full_population_support_v4 as support
from test_roboboat_full_population_support_v2 import reviewed_inventory


def partial_bank(tmp_path):
    response_path,response_root,source,bank=reviewed_inventory(tmp_path)
    joins=json.loads((bank/'evaluator-join.json').read_text())['entries']
    baseline=next(j['opaque_response_id'] for j in joins if j['method']=='B2')
    (bank/'project_reviews'/f'{baseline}.json').unlink()
    availability=tmp_path/'availability.json';snapshot=support.snapshot_availability(bank,availability)
    return response_path,response_root,source,bank,availability,snapshot,baseline


def prepare_partial(tmp_path):
    path,root,d,bank,availability,snapshot,key=partial_bank(tmp_path)
    out=tmp_path/'support';decl=tmp_path/'support.json'
    result=support.prepare(bank,path,root,out,decl,availability=availability)
    return decl,out,result,availability,key


def test_mechanical_review_availability_preserves_all_original_joins_and_reused_text_contexts(tmp_path):
    decl,out,d,availability,key=prepare_partial(tmp_path)
    assert d['schema'].endswith('/v4') and d['timeout_s']==600
    assert d['original_answers']==6 and d['reviewed_available_answers']==3
    joins=json.loads((out/'evaluator-join.json').read_text())['entries']
    pending=[j for j in joins if j['opaque_response_id']==key]
    assert len(pending)==3 and all(j['support_packet_id'] is None for j in pending)
    assert all(j['availability']['status']=='UNREVIEWED_SOURCE_EXISTS' for j in pending)
    assert all(j['primary_bounds_if_unavailable']==[0,1] for j in pending)
    assert len(d['snapshot_entries'])==3 and d['confirmation_n']==0
    assert support.verify_availability(availability)['bank']
    assert any(b['path'].endswith('run_roboboat_full_population_support_v4.py') for b in d['dependencies'])
    assert any(b['path'].endswith('roboboat_annotation_deadline_v2.py') for b in d['dependencies'])


def test_pending_return_vs_failed_attempt_receipt_distinguished(tmp_path):
    path,root,d,bank,availability,snapshot,key=partial_bank(tmp_path)
    # New snapshot after construction changes: no frozen snapshot is revised.
    (bank/'returns'/f'{key}-A.json').unlink()
    inventory_path=support.checked(json.loads((bank/'inventory-binding.json').read_text())['declaration'])
    attempt=bank/'extraction-attempts'/f'{key}-A.json';attempt.parent.mkdir()
    attempt.write_text(json.dumps({'opaque_response_id':key,'slot':'A',
        'source_identity':{'declaration_sha256':support.digest(inventory_path),'output_root':str(bank)},
        'status':'TECHNICAL_OR_STRUCTURAL_EXTRACTION_FAILURE'}))
    newer=support.snapshot_availability(bank,tmp_path/'availability-new.json')
    item=next(a for a in newer['answers'] if a['opaque_response_id']==key)
    assert item['status']=='EXTRACTION_RETURN_UNAVAILABLE'
    assert 'TECHNICAL_OR_STRUCTURAL_EXTRACTION_FAILURE' in item['reason']
    assert item['returns']['A']['observed_missing']


@pytest.mark.parametrize('attack',['return','review','missing-path','omitted-existing-review'])
def test_exact_snapshot_bindings_and_missing_path_existence_cannot_be_bypassed(tmp_path,attack):
    path,root,d,bank,availability,snapshot,key=partial_bank(tmp_path)
    if attack=='return': (bank/'returns'/f'{key}-A.json').write_text('{}')
    elif attack=='review':next((bank/'project_reviews').glob('*.json')).write_text('{}')
    elif attack=='missing-path':(bank/'project_reviews'/f'{key}.json').write_text('{}')
    else:
        eligible=next(a for a in snapshot['answers'] if a['status']=='REVIEWED_EXTRACTION_AVAILABLE')
        eligible['status']='UNREVIEWED_SOURCE_EXISTS';snapshot['dependencies']=[b for b in snapshot['dependencies'] if b['path']!=eligible['review']['path']]
        eligible['review']={'path':eligible['review']['path'],'observed_missing':True}
        availability.write_text(json.dumps(snapshot))
    with pytest.raises(ValueError):support.verify_availability(availability)


def test_false_complete_review_cannot_hide_missing_extraction_pass(tmp_path):
    path,root,d,bank=reviewed_inventory(tmp_path)
    raw=next((bank/'returns').glob('*-A.json'));raw.unlink()
    with pytest.raises(ValueError,match='cannot hide unavailable'):
        support.snapshot_availability(bank,tmp_path/'availability.json')


def test_raw_provider_receipt_still_checked_for_all_original_answers(tmp_path):
    path,root,d,bank,availability,snapshot,key=partial_bank(tmp_path)
    receipt=next((root/'calls').glob('*.json'));receipt.write_text('{}')
    with pytest.raises((ValueError,KeyError)):
        support.prepare(bank,path,root,tmp_path/'support',tmp_path/'support.json',availability=availability)


def test_existing_source_review_reasons_retained_without_support_labels(tmp_path):
    path,root,d,bank=reviewed_inventory(tmp_path)
    review=next((bank/'project_reviews').glob('*.json'));v=json.loads(review.read_text());v['status']='ISSUES_REQUIRE_RESOLUTION';review.write_text(json.dumps(v))
    snapshot=support.snapshot_availability(bank,tmp_path/'availability.json')
    item=next(a for a in snapshot['answers'] if a['review'].get('path')==str(review.resolve()))
    assert item['status']=='UNREVIEWED_SOURCE_EXISTS' and 'ISSUES_REQUIRE_RESOLUTION' in item['reason']
    assert 'primary_success' not in snapshot


def test_genuine_v3_inventory_accepted_without_schema_fabrication(monkeypatch,tmp_path):
    import test_roboboat_full_population_support_v2 as fixture
    import run_roboboat_full_population_inventory_v3 as inventory
    monkeypatch.setattr(fixture,'inventory',inventory)
    path,root,d,bank=fixture.reviewed_inventory(tmp_path)
    availability=tmp_path/'availability.json';support.snapshot_availability(bank,availability)
    result=support.prepare(bank,path,root,tmp_path/'support',tmp_path/'support.json',availability=availability)
    assert result['reviewed_available_answers']==6
    assert result['timeout_s']==600


def test_support_execution_uses_qualified600s_and_no_reissue(monkeypatch,tmp_path):
    decl,out,d,availability,key=prepare_partial(tmp_path);calls=[]
    def annotator(packet,target,caller):
        assert caller.timeout_s==600
        calls.append(packet);return {'construction_only':True}
    support.run(decl,out,annotator=annotator);support.run(decl,out,annotator=annotator)
    assert len(calls)==d['unique_support_packets']
    assert all(json.loads(p.read_text())['status']=='SUPPORT_COMPLETE_CITATION_REVIEW_PENDING' for p in (out/'terminals').glob('*.json'))


def test_later_return_review_and_attempt_arrivals_do_not_promote_frozen_selection(tmp_path):
    path,root,d,bank=reviewed_inventory(tmp_path)
    joins=json.loads((bank/'evaluator-join.json').read_text())['entries']
    key=next(j['opaque_response_id'] for j in joins if j['method']=='B2')
    review=bank/'project_reviews'/f'{key}.json';review_bytes=review.read_bytes();review.unlink()
    raw=bank/'returns'/f'{key}-A.json';raw_bytes=raw.read_bytes();raw.unlink()
    availability=tmp_path/'availability.json';before=support.snapshot_availability(bank,availability)
    out=tmp_path/'support';decl=tmp_path/'support.json'
    prepared=support.prepare(bank,path,root,out,decl,availability=availability)
    raw.write_bytes(raw_bytes);review.write_bytes(review_bytes)
    attempts=bank/'extraction-attempts';attempts.mkdir(exist_ok=True)
    (attempts/f'{key}-A.json').write_text('{}')
    assert support.verify_availability(availability,require_current=False)==before
    assert prepared['reviewed_available_answers']==3
    with pytest.raises(ValueError,match='missing path now exists'):
        support.verify_availability(availability)
    calls=[]
    support.run(decl,out,annotator=lambda *args,**kwargs: calls.append(args) or {'construction_only':True})
    assert len(calls)==prepared['unique_support_packets']
    joins=json.loads((out/'evaluator-join.json').read_text())['entries']
    assert all(j['support_packet_id'] is None for j in joins if j['opaque_response_id']==key)


def test_snapshot_forgery_after_preparation_rejected_even_for_unavailable_slots(tmp_path):
    decl,out,d,availability,key=prepare_partial(tmp_path)
    value=json.loads(availability.read_text());value['answers'][0]['reason']='forged'
    availability.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        support.run(decl,out,annotator=lambda *args: pytest.fail('unexpected call'))


def test_frozen_available_review_bytes_remain_immutable_after_late_arrivals(tmp_path):
    decl,out,d,availability,key=prepare_partial(tmp_path)
    snapshot=json.loads(availability.read_text())
    retained=next(a['review']['path'] for a in snapshot['answers'] if a['status']=='REVIEWED_EXTRACTION_AVAILABLE')
    Path(retained).write_text('{}')
    with pytest.raises(ValueError):
        support.verify_availability(availability,require_current=False)
