import pytest
from roboboat_qualification_boolean_fields_v2 import score_case


def inputs():
    c={'case_id':'x','split':'heldout','threat_tags':[],
       'form':{'response_text':'Contact is missing. Completion is unknown.'},
       'expected':{'atomic_labels':[{'item_id':'c','label':'SUPPORTED_BY_VISIBLE_EVIDENCE'}],
         'required_unit_coverage':[{'unit_prompt':'state limit','communicated':True,'response_span':'Completion is unknown.'}],
         'limitation_preservation':[],'highest_asserted_abstraction_level':'task_outcome','false_premise_handling':'NOT_APPLICABLE'}}
    r={'atomic_labels':[{'item_id':'c','label':'SUPPORTED_BY_VISIBLE_EVIDENCE'}],
       'required_unit_coverage':[{'unit_prompt':'state limit','communicated':True,'response_span':'Contact is missing.'}],
       'limitation_preservation':[],'highest_asserted_abstraction_level':'task_outcome','false_premise_handling':'NOT_APPLICABLE'}
    return c,r


def test_valid_alternate_source_citation_not_rejected_for_example_wording():
    c,r=inputs();s=score_case(c,r)
    assert s['required_units'][0]['correct']
    assert not s['required_units'][0]['semantic_citation_validity_established']


def test_irrelevant_verbatim_citation_is_not_semantically_validated_by_arithmetic():
    c,r=inputs();r['required_unit_coverage'][0]['response_span']='Completion'
    s=score_case(c,r);assert s['required_units'][0]['source_citation_valid']
    assert not s['required_units'][0]['semantic_citation_validity_established']


@pytest.mark.parametrize('mode',['fabricated','missing','boolean'])
def test_wrong_or_uncited_positive_field_fails(mode):
    c,r=inputs();a=r['required_unit_coverage'][0]
    if mode=='fabricated':a['response_span']='not in answer'
    elif mode=='missing':a['response_span']=None
    else:a['communicated']=False
    assert not score_case(c,r)['required_units'][0]['correct']


def test_duplicate_fields_rejected():
    c,r=inputs();r['required_unit_coverage']*=2
    with pytest.raises(ValueError):score_case(c,r)
