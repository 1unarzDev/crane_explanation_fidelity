import pytest
from roboboat_qualification_span_audit_v1 import audit_fields


def inputs():
    return ({'form':{'response_text':'Contact is missing. Full completion is unestablished.'},'expected':{'required_unit_coverage':[{'unit_prompt':'state evidence limitation','communicated':True,'response_span':'Full completion is unestablished.'}],'limitation_preservation':[]}},
            {'required_unit_coverage':[{'unit_prompt':'state evidence limitation','communicated':True,'response_span':'Contact is missing.'}],'limitation_preservation':[]})


def test_alternate_verbatim_span_does_not_imply_semantic_error_or_pass():
    c,r=inputs();v=audit_fields(c,r)
    assert v['all_boolean_and_source_span_checks_pass']
    assert not v['fields'][0]['reference_example_span_match']
    assert not v['qualification_promoted'] and not v['frozen_score_replaced']
    assert not v['fields'][0]['semantic_citation_validity_established_by_arithmetic']


def test_fabricated_citation_fails_source_containment():
    c,r=inputs();r['required_unit_coverage'][0]['response_span']='Unobserved imaginary text'
    assert not audit_fields(c,r)['all_boolean_and_source_span_checks_pass']


def test_wrong_boolean_is_retained_not_repaired_by_matching_words():
    c,r=inputs();r['required_unit_coverage'][0]['communicated']=False
    assert not audit_fields(c,r)['all_boolean_and_source_span_checks_pass']


def test_duplicate_or_missing_units_fail_closed():
    c,r=inputs();r['required_unit_coverage']*=2
    with pytest.raises(ValueError):audit_fields(c,r)
