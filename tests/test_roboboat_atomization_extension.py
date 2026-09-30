import json
import pytest
import run_roboboat_atomization_extension_v3 as runner


def test_no_tool_runner_sends_response_inline_and_never_gold(tmp_path,monkeypatch):
    doc=tmp_path/'doc';doc.mkdir()
    (doc/'marine_atomization_freeze_v3.json').write_text('{}')
    monkeypatch.setattr(runner,'DOC',doc)
    text='Completion is unknown.'
    def fake_call(cache,role,work,prompt,model,effort,schema,allow_tools):
        assert text in prompt and 'Use no tools.' in prompt
        assert 'secret-gold' not in prompt
        assert allow_tools is False
        entry=json.loads((work/'response.json').read_text())
        assert set(entry)=={'opaque_response_id','response_text'}
        value={'schema':'crane-evidence-calibration-atomization-return/v1',
            'opaque_response_id':entry['opaque_response_id'],
            'claims':[{'response_span':text,'claim_text':text,'asserted_abstraction_level':'task_outcome'}],
            'unresolved_spans':[],'attestation':'METHOD_BLIND_EXHAUSTIVE_EXTRACTION_ATTEMPT'}
        return {'parsed_final':value,'cache_key':'test'}
    monkeypatch.setattr(runner,'call',fake_call)
    freeze={'prompt':{'path':'research/explanation_fidelity/prompts/evidence-calibration-atomizer-v1.md'},
        'output_schema':{'path':'research/explanation_fidelity/schemas/evidence-calibration-atomization-return-v1.schema.json'},
        'candidate':{'model':'frozen-model','reasoning_effort':'high'}}
    case={'case_id':'opaque','response_text':text,'expected':['secret-gold']}
    result=runner.execute(case,'A',freeze,tmp_path/'out')
    assert result['semantic_completeness_established'] is False
    assert result['endpoint_scoring_authorized'] is False


def test_retained_structural_failure_cannot_be_retried_or_promoted(tmp_path):
    (tmp_path/'returns').mkdir()
    (tmp_path/'returns/opaque-A.json').write_text(json.dumps({
        'validation':{'status':'REVIEW_REQUIRED_UNRESOLVED_ASSERTION'}}))
    with pytest.raises(RuntimeError,match='retained structural failure'):
        runner.execute({'case_id':'opaque','response_text':'x'},'A',{},tmp_path)
