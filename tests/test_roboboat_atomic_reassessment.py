import hashlib
import json
from pathlib import Path
import pytest
import run_roboboat_atomic_reassessment as runner


def test_complete_bank_gate_rejects_a_missing_review_and_changed_return(tmp_path):
    answer='Completion is unknown.';key=hashlib.sha256(answer.encode()).hexdigest()
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
    write(tmp_path/'blind-bank.json',{'entries':[{'opaque_response_id':key,'response_text':answer}]})
    write(tmp_path/'structural-result.json',{'status':'COMPLETE_BLIND_BANK_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING','unique_answer_texts':1})
    with pytest.raises(FileNotFoundError):runner.load_complete_reviews(tmp_path)
    returns={}
    for slot in ('A','B'):
        path=tmp_path/'returns'/f'{key}-{slot}.json'
        write(path,{'case_id':key,'slot':slot,'entry':{'response_text':answer},
            'validation':{'status':'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}})
        returns[slot]=runner.digest(path)
    write(tmp_path/'project_reviews'/f'{key}.json',{
        'status':'COMPLETE_FAITHFUL_PROJECT_REVIEW','source_text_sha256':key,
        'opaque_response_id':key,'extractor_returns_sha256':returns,
        'project_review_not_human_validation':True,'abstraction_tags_discarded':True,
        'source_assertion_completeness_reviewed':True,
        'claims':[{'response_span':answer,'claim_text':answer}]})
    entries,reviews=runner.load_complete_reviews(tmp_path)
    assert len(entries)==len(reviews)==1
    path=tmp_path/'returns'/f'{key}-B.json';path.write_text(path.read_text()+' ')
    with pytest.raises(ValueError,match='bytes changed'):runner.load_complete_reviews(tmp_path)


def test_unresolved_intent_never_resubmits_annotation(tmp_path,monkeypatch):
    monkeypatch.setattr(runner,'ROOT',tmp_path);monkeypatch.setattr(runner,'OUT',tmp_path/'out')
    monkeypatch.setattr(runner,'annotate',lambda *a,**kw:pytest.fail('resubmission forbidden'))
    path=tmp_path/'out'/'intents'/'opaque.json';path.parent.mkdir(parents=True);path.write_text('{}')
    with pytest.raises(FileExistsError):runner.run_one({'path':'opaque.json','sha256':'unused'}, {})
