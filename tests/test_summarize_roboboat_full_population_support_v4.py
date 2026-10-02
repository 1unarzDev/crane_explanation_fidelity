"""Synthetic labels exercise release bounds/gates, never empirical answer quality."""
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import pytest
import run_roboboat_full_population_support_v4 as support
import summarize_roboboat_full_population_support_v4 as release
import test_summarize_roboboat_full_population_support_v2 as old_fixture


def construction(monkeypatch,tmp_path, *, partial=False):
    def prepare(bank,path,root,out,decl):
        if partial:
            joins=json.loads((bank/'evaluator-join.json').read_text())['entries']
            baseline=next(j['opaque_response_id'] for j in joins if j['method']=='B2')
            (bank/'project_reviews'/f'{baseline}.json').unlink()
        availability=tmp_path/'availability.json';support.snapshot_availability(bank,availability)
        return support.prepare(bank,path,root,out,decl,availability=availability)
    monkeypatch.setattr(old_fixture,'support',SimpleNamespace(prepare=prepare,checked=support.checked,digest=support.digest))
    return old_fixture.prepared_support(tmp_path)


def test_full_snapshot_slots_retained_when_only_some_extraction_reviews_available(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path,partial=True)
    result=release.summarize(decl,out)
    assert len(result['rows'])==6
    assert result['method_totals']['B2']['snapshot_answer_slots']==3
    assert result['method_totals']['B2']['reviewed_answers']==0
    assert all(row['primary_bounds']==[0,1] for row in result['rows'] if row['method']=='B2')
    assert all(row['answer_status']=='UNREVIEWED_SOURCE_EXISTS' for row in result['rows'] if row['method']=='B2')
    assert result['confirmation_n']==result['replication_n']==result['independent_n_added']==0
    assert result['p_value'] is None and result['question_count_is_independent_n'] is False


@pytest.mark.parametrize('status',['missing','failed'])
def test_technical_annotation_unavailability_is_unknown_not_semantic_failure(monkeypatch,tmp_path,status):
    decl,out,d=construction(monkeypatch,tmp_path)
    key=Path(d['packets'][0]['path']).stem
    shutil.rmtree(out/'annotations'/key);(out/'citation_reviews'/f'{key}.json').unlink()
    terminal=out/'terminals'/f'{key}.json'
    if status=='missing':terminal.unlink()
    else:
        v=json.loads(terminal.read_text());v['status']='TECHNICAL_SUPPORT_FAILURE';terminal.write_text(json.dumps(v))
    result=release.summarize(decl,out)
    unavailable=[row for row in result['rows'] if row.get('support_packet_id')==key]
    assert unavailable and all(row['primary_bounds']==[0,1] and row['score'] is None for row in unavailable)
    assert result['technical_or_judgment_unavailability_is_semantic_failure'] is False


def test_completed_annotation_always_requires_complete_citation_review(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path)
    key=Path(d['packets'][0]['path']).stem;(out/'citation_reviews'/f'{key}.json').unlink()
    with pytest.raises(ValueError,match='every completed'):release.summarize(decl,out)


def test_completed_final_cannot_be_hidden_behind_missing_terminal(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path)
    key=Path(d['packets'][0]['path']).stem;(out/'terminals'/f'{key}.json').unlink()
    with pytest.raises(ValueError,match='cannot masquerade'):release.summarize(decl,out)


def test_explicitly_reviewed_unavailable_primary_judgment_is_unknown(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path)
    key=Path(d['packets'][0]['path']).stem;folder=out/'annotations'/key
    final=folder/'final.json';v=json.loads(final.read_text())
    missing=next(k for k in v['final_decisions'] if k.startswith('unit:'))
    v['final_decisions'][missing]=None;final.write_text(json.dumps(v))
    review=out/'citation_reviews'/f'{key}.json';r=json.loads(review.read_text())
    r.update(status='PRIMARY_DECISIONS_UNAVAILABLE_RETAINED',unresolved_decision_keys=[missing],
             inputs=[release.binding(p) for p in folder.glob('*.json')]);review.write_text(json.dumps(r))
    result=release.summarize(decl,out)
    rows=[row for row in result['rows'] if row.get('support_packet_id')==key]
    assert rows and all(row['primary_bounds']==[0,1] for row in rows)
    assert all(row['answer_status']=='PRIMARY_JUDGMENTS_UNAVAILABLE_RETAINED' for row in rows)
    assert all(row['whole_answer_and_supporting_labels']['all_final_decisions'][missing] is None for row in rows)


def test_unavailable_primary_review_must_name_every_actual_missing_key(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path)
    key=Path(d['packets'][0]['path']).stem;review=out/'citation_reviews'/f'{key}.json'
    r=json.loads(review.read_text());r.update(status='PRIMARY_DECISIONS_UNAVAILABLE_RETAINED',unresolved_decision_keys=['unit:invented']);review.write_text(json.dumps(r))
    with pytest.raises(ValueError,match='must be exact'):release.summarize(decl,out)


def test_later_missing_source_review_cannot_silently_revise_frozen_support_selection(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path,partial=True)
    snapshot=json.loads(Path(d['availability_snapshot']['path']).read_text())
    missing=next(a['review']['path'] for a in snapshot['answers'] if a['status']=='UNREVIEWED_SOURCE_EXISTS')
    Path(missing).write_text('{}')
    support.run(decl,out,annotator=lambda *a,**k:pytest.fail('unexpected annotation'))
    result=release.summarize(decl,out)
    assert result['method_totals']['B2']['unresolved_answer_slots']==3
    assert all(row['primary_bounds']==[0,1] for row in result['rows'] if row['method']=='B2')


def test_missing_primary_key_explicit_review_is_unknown_instead_of_failure(monkeypatch,tmp_path):
    decl,out,d=construction(monkeypatch,tmp_path)
    key=Path(d['packets'][0]['path']).stem;folder=out/'annotations'/key
    final=folder/'final.json';v=json.loads(final.read_text())
    missing=next(k for k in v['final_decisions'] if k.startswith('limitation:'))
    del v['final_decisions'][missing];final.write_text(json.dumps(v))
    review=out/'citation_reviews'/f'{key}.json';r=json.loads(review.read_text())
    r.update(status='PRIMARY_DECISIONS_UNAVAILABLE_RETAINED',unresolved_decision_keys=[missing],
             inputs=[release.binding(p) for p in folder.glob('*.json')]);review.write_text(json.dumps(r))
    result=release.summarize(decl,out)
    assert all(row['primary_bounds']==[0,1] for row in result['rows'] if row.get('support_packet_id')==key)


def test_every_method_slot_in_large_declared_panel_is_retained():
    entries=[{'id':f'construction-condition-{i}'} for i in range(48)]
    rows=[{'response_id':e['id'],'method':m,'primary_bounds':[0,1],
           'answer_status':'MISSING_OR_PENDING_SUPPORT_TERMINAL'} for e in entries for m in ('B2','B4')]
    totals,pairs=release.describe_slots(entries,rows)
    assert len(rows)==96 and len(pairs)==48
    assert totals['B2']['snapshot_answer_slots']==48
    assert totals['B4']['success_total_favorable']==48
    assert all(p['difference_bounds']==[-1,1] for p in pairs)
    with pytest.raises(ValueError,match='every unique'):release.describe_slots(entries,rows[:-1])
