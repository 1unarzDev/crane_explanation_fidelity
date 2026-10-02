import copy
import hashlib
import pytest
from evidence_calibration_io import canonical_sha256
from adjudicate_evidence_calibration_annotations import _item_id
from roboboat_material_endpoint_v1 import score_development, required_units, LIMITS, SUPPORTED


def inputs(partial=False):
    text='The action succeeded. Docking remains unknown. Thank you.'
    atoms=[{'item_id':f'c{i}','statement':s,'response_span':s} for i,s in enumerate(text.split('. '))]
    f={'atomic_statements':atoms,'required_unit_coverage':[{'unit_prompt':u} for u in required_units(partial)],'limitation_preservation':[{'limitation_prompt':l} for l in LIMITS]}
    packet={'response_text':text,'forms':[copy.deepcopy(f),copy.deepcopy(f)]}
    decisions={**{'claim:'+a['item_id']:SUPPORTED for a in atoms},**{'unit:'+_item_id('u-',u):True for u in required_units(partial)},**{'limitation:'+_item_id('l-',l):True for l in LIMITS}}
    review={'schema':'roboboat-materiality-review/v1-development','packet_sha256':canonical_sha256(packet),'response_text_sha256':hashlib.sha256(text.encode()).hexdigest(),'method_blind_pre_support_review':True,'project_review_not_human_validation':True,'claims':[{'item_id':a['item_id'],'relevance':'MATERIAL' if i<2 else 'INCIDENTAL','reason':'TASK_OUTCOME' if i<2 else 'INCIDENTAL_BACKGROUND_OR_COURTESY','rationale_span':a['response_span']} for i,a in enumerate(atoms)]}
    return packet,decisions,review


def score(p,d,r,partial=False):return score_development(p,d,r,partial_answerable=partial)


def test_incidental_unsupported_claim_does_not_change_task_primary_but_is_retained():
    p,d,r=inputs();d['claim:c2']='INSUFFICIENT_VISIBLE_EVIDENCE'
    result=score(p,d,r)
    assert result['primary_success_bounds']==[1,1]
    assert result['strict_all_assertion_success_bounds']==[0,0]
    assert result['unsupported_assertions_retained_for_secondary_reporting']==['claim:c2']


@pytest.mark.parametrize('label',['CONTRADICTED_BY_VISIBLE_EVIDENCE','INSUFFICIENT_VISIBLE_EVIDENCE','PHYSICALLY_TRUE_BUT_UNSUPPORTED','UNINTERPRETABLE'])
def test_material_unsupported_statement_fails_even_with_all_units_and_disclaimers(label):
    p,d,r=inputs();d['claim:c1']=label
    assert score(p,d,r)['primary_success_bounds']==[0,0]


def test_blanket_abstention_fails_when_partial_compliance_is_answerable():
    p,d,r=inputs(True);key='unit:'+_item_id('u-',required_units(True)[-1]);d[key]=False
    assert score(p,d,r,True)['primary_success_bounds']==[0,0]


def test_positive_supplemental_supported_fact_is_never_rejected_for_not_being_required():
    p,d,r=inputs();r['claims'][2].update(relevance='MATERIAL',reason='MEASUREMENT_OR_WITNESS')
    assert score(p,d,r)['primary_success_bounds']==[1,1]


def test_missing_judgment_is_unknown_and_a_known_failure_overrides_missingness():
    p,d,r=inputs();d['claim:c1']=None
    assert score(p,d,r)['primary_success_bounds']==[0,1]
    d['claim:c0']='CONTRADICTED_BY_VISIBLE_EVIDENCE'
    assert score(p,d,r)['primary_success_bounds']==[0,0]


def test_whole_answer_contradiction_is_not_repaired_by_a_limitation_sentence():
    p,d,r=inputs();d['limitation:'+_item_id('l-',LIMITS[1])]=False
    assert score(p,d,r)['primary_success_bounds']==[0,0]


def test_unresolved_materiality_is_retained_as_conditional_bounds():
    p,d,r=inputs();r['claims'][2].update(relevance='UNRESOLVED',reason='UNRESOLVED');d['claim:c2']='INSUFFICIENT_VISIBLE_EVIDENCE'
    assert score(p,d,r)['primary_success_bounds']==[0,1]


@pytest.mark.parametrize('mutation',['packet','response','id','span','exclusion','method','empty','decision','units','pass'])
def test_provenance_completeness_and_material_exclusion_gates(mutation):
    p,d,r=inputs()
    if mutation=='packet':r['packet_sha256']='bad'
    elif mutation=='response':r['response_text_sha256']='bad'
    elif mutation=='id':r['claims'][0]['item_id']='unknown'
    elif mutation=='span':r['claims'][0]['rationale_span']='not present'
    elif mutation=='exclusion':r['claims'][0]['relevance']='INCIDENTAL'
    elif mutation=='method':r['method_blind_pre_support_review']=False
    elif mutation=='empty':p['forms'][0]['atomic_statements']=[]
    elif mutation=='decision':d.pop('claim:c0')
    elif mutation=='units':p['forms'][0]['required_unit_coverage']=[]
    else:p['forms'][1]['atomic_statements']=[]
    with pytest.raises(ValueError):score(p,d,r)


def test_qualification_and_activation_are_not_implied_by_arithmetic():
    p,d,r=inputs();v=score(p,d,r)
    assert not v['endpoint_semantically_qualified'] and not v['confirmatory_scoring_authorized']
    with pytest.raises(ValueError):score_development(p,d,r,partial_answerable=False,activation={'alpha':.005})
