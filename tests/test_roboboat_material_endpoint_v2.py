import pytest
from adjudicate_evidence_calibration_annotations import _item_id
from roboboat_material_endpoint_v2 import score_development,MATERIAL_LIMIT,UNITS,PARTIAL_UNIT,LIMITS,SUPPORTED


def decisions(partial=False):return {'claim:c':SUPPORTED,**{'unit:'+_item_id('u-',u):True for u in UNITS+((PARTIAL_UNIT,) if partial else ())},**{'limitation:'+_item_id('l-',l):True for l in LIMITS+(MATERIAL_LIMIT,)}}


def test_minor_supplemental_error_can_differ_from_strict_score_without_being_erased():
    d=decisions();d['claim:c']='CONTRADICTED_BY_VISIBLE_EVIDENCE'
    s=score_development(d,partial_answerable=False)
    assert s['proposed_primary_success_bounds']==[1,1]
    assert s['strict_all_assertion_success_bounds']==[0,0]
    assert s['unsupported_atomic_decisions']=={'claim:c':'CONTRADICTED_BY_VISIBLE_EVIDENCE'}
    assert not s['endpoint_semantically_qualified']


def test_material_outcome_or_witness_error_fails_despite_small_magnitude():
    d=decisions();d['claim:c']='CONTRADICTED_BY_VISIBLE_EVIDENCE'
    d['limitation:'+_item_id('l-',MATERIAL_LIMIT)]=False
    assert score_development(d,partial_answerable=False)['proposed_primary_success_bounds']==[0,0]


def test_blanket_unknown_fails_when_positive_sampled_information_is_answerable():
    d=decisions(True);d['unit:'+_item_id('u-',PARTIAL_UNIT)]=False
    assert score_development(d,partial_answerable=True)['proposed_primary_success_bounds']==[0,0]


def test_missing_judgments_stay_unknown_instead_of_dropped():
    d=decisions();d['claim:c']=None
    assert score_development(d,partial_answerable=False)['proposed_primary_success_bounds']==[0,1]
    d['limitation:'+_item_id('l-',LIMITS[0])]=False
    assert score_development(d,partial_answerable=False)['proposed_primary_success_bounds']==[0,0]


@pytest.mark.parametrize('mode',['material','unit','empty','bad-bool','partial'])
def test_complete_prospective_inventory_required(mode):
    d=decisions()
    if mode=='material':d.pop('limitation:'+_item_id('l-',MATERIAL_LIMIT))
    elif mode=='unit':d.pop('unit:'+_item_id('u-',UNITS[0]))
    elif mode=='empty':d.pop('claim:c')
    elif mode=='bad-bool':d['limitation:'+_item_id('l-',MATERIAL_LIMIT)]=1
    else:d['unit:'+_item_id('u-',PARTIAL_UNIT)]=True
    with pytest.raises(ValueError):score_development(d,partial_answerable=False)


def test_qualified_annotation_source_does_not_authorize_this_new_mapping_or_activation():
    with pytest.raises(ValueError):score_development(decisions(),partial_answerable=False,activation={'alpha':.005})
