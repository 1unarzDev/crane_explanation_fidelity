import hashlib
import json
import pytest
from roboboat_reviewed_annotation_packet import build_reviewed_packet,validate_review_provenance


def review(answer):
    return {'status':'COMPLETE_FAITHFUL_PROJECT_REVIEW',
        'opaque_response_id':hashlib.sha256(answer.encode()).hexdigest(),
        'claims':[{'response_span':answer,'claim_text':answer}]}


def test_review_gate_and_exact_answer_binding_fail_closed():
    answer='Completion is unknown.'
    r=review(answer);r['status']='STRUCTURAL_ONLY'
    with pytest.raises(ValueError,match='review gate'):build_reviewed_packet({},answer,{},r)
    r=review('Other answer.')
    with pytest.raises(ValueError,match='different answer'):build_reviewed_packet({},answer,{},r)


def test_unqualified_tags_and_nonverbatim_spans_cannot_enter_claim_inventory():
    answer='Completion is unknown.';r=review(answer)
    r['claims'][0]['asserted_abstraction_level']='specific_physical_cause'
    with pytest.raises(ValueError,match='invalid reviewed'):build_reviewed_packet({},answer,{},r)
    r=review(answer);r['claims'][0]['response_span']='Completion succeeded.'
    with pytest.raises(ValueError,match='non-verbatim'):build_reviewed_packet({},answer,{},r)


def test_review_provenance_rejects_changed_artifacts_and_incomplete_passes():
    answer='Completion is unknown.';r=review(answer)
    r.update(source_text_sha256=r['opaque_response_id'],project_review_not_human_validation=True,
             abstraction_tags_discarded=True,source_assertion_completeness_reviewed=True)
    returns={slot:json.dumps({'case_id':r['opaque_response_id'],'slot':slot,
        'entry':{'response_text':answer},'validation':{'status':'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}}).encode()
        for slot in ('A','B')}
    r['extractor_returns_sha256']={s:hashlib.sha256(raw).hexdigest() for s,raw in returns.items()}
    validate_review_provenance(answer,r,returns)
    with pytest.raises(ValueError,match='both extraction'):validate_review_provenance(answer,r,{'A':returns['A']})
    with pytest.raises(ValueError,match='bytes changed'):validate_review_provenance(answer,r,{**returns,'B':returns['B']+b' '})
    r['source_assertion_completeness_reviewed']=False
    with pytest.raises(ValueError,match='explicit project'):validate_review_provenance(answer,r,returns)
