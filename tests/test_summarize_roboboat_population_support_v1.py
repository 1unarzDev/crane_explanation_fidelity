import json
import pytest
import summarize_roboboat_population_support_v1 as release


def fixture(tmp_path):
    packet={'forms':[{'packet_id':'blind'}], 'response_text':'Synthetic answer.'}
    packet_path=tmp_path/'packet.json'; packet_path.write_text(json.dumps(packet))
    annotations=tmp_path/'annotations'; annotations.mkdir()
    final={'packet_id':'blind','packet_set_sha256':release.canonical_sha256(packet),
           'final_decisions':{'unit:synthetic':True,'highest_asserted_abstraction_level':'observation'}}
    for name,value in [('annotation-A.json',{}),('annotation-B.json',{}),('agreement.json',{}),('final.json',final)]:
        (annotations/name).write_text(json.dumps(value))
    review={'schema':'roboboat-population-citation-review/v1','packet_id':'blind','status':'PASS',
            'complete_source_review':True,'project_agent_review_not_human_validation':True,
            'issues':[],'unresolved_decision_keys':[], 'packet':release.binding(packet_path),
            'inputs':[release.binding(p) for p in annotations.glob('*.json')]}
    path=tmp_path/'review.json';path.write_text(json.dumps(review))
    return packet_path,annotations,path,review


@pytest.mark.parametrize('key,value',[('status','ISSUES_REQUIRE_RESOLUTION'),
    ('complete_source_review',False),('issues',['scope mismatch']),('unresolved_decision_keys',['unit:synthetic'])])
def test_source_review_gate_cannot_be_bypassed(tmp_path,key,value):
    packet,folder,path,review=fixture(tmp_path);review[key]=value;path.write_text(json.dumps(review))
    with pytest.raises(ValueError,match='citation review required'):
        release.reviewed_score(packet,folder,path)


def test_changed_annotation_invalidates_review(tmp_path):
    packet,folder,path,_=fixture(tmp_path)
    (folder/'annotation-A.json').write_text('{"different":true}')
    with pytest.raises(ValueError,match='bound input changed'):
        release.reviewed_score(packet,folder,path)


def test_both_raw_passes_must_be_reviewed(tmp_path):
    packet,folder,path,review=fixture(tmp_path);review['inputs']=review['inputs'][1:]
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError,match='bind both passes'):
        release.reviewed_score(packet,folder,path)


def test_only_endpoint_decisions_reach_scoring(tmp_path,monkeypatch):
    packet,folder,path,_=fixture(tmp_path)
    monkeypatch.setattr(release,'validate',lambda *a:None)
    monkeypatch.setattr(release,'score',lambda p,values:values)
    assert release.reviewed_score(packet,folder,path)=={'unit:synthetic':True}


def test_secondary_abstraction_issue_cannot_hide_missing_primary_decision(tmp_path,monkeypatch):
    packet,folder,path,review=fixture(tmp_path)
    review.update(status='PASS_PRIMARY_WITH_SECONDARY_ISSUES',
        supporting_metric_issues=['Abstraction taxonomy differs.'],
        unresolved_decision_keys=['highest_asserted_abstraction_level','unit:synthetic'])
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError,match='citation review required'):
        release.reviewed_score(packet,folder,path)


def test_narrow_secondary_only_exception_preserves_primary_score(tmp_path,monkeypatch):
    packet,folder,path,review=fixture(tmp_path)
    review.update(status='PASS_PRIMARY_WITH_SECONDARY_ISSUES',
        supporting_metric_issues=['Abstraction taxonomy differs.'],
        unresolved_decision_keys=['highest_asserted_abstraction_level'])
    path.write_text(json.dumps(review))
    monkeypatch.setattr(release,'validate',lambda *a:None)
    monkeypatch.setattr(release,'score',lambda p,values:values)
    assert release.reviewed_score(packet,folder,path)=={'unit:synthetic':True}
