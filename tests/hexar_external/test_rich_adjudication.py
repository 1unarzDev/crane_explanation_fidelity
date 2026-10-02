import copy
import pytest
from analysis.hexar_external.confirmatory_v1.rich_evaluator_v3 import validate
from analysis.hexar_external.confirmatory_v1.rich_adjudication import needs_c,resolve

PAYLOAD=dict(answer='Navigation software reported success. I started toward the map goal. I physically arrived.',required_units=[dict(unit_id='reported_navigation_outcome',requirement='Report software outcome.')])

def label(unsupported=False,ambiguous=False,coverage=True):
    return dict(status='VALID',parsed=dict(unsupported_material=unsupported,overlicensed_specificity=unsupported,
        covered_units=['reported_navigation_outcome'] if coverage else [],rationale='Development fixture.',
        unsupported_spans=['I physically arrived.'] if unsupported else [],
        overlicensed_spans=['I physically arrived.'] if unsupported else [],
        ambiguous_spans=['I started toward the map goal.'] if ambiguous else []))


def test_disagreement_uses_full_vector_C_without_component_cherry_picking():
    a,b=label(),label(True)
    assert needs_c(a,b,PAYLOAD)
    assert resolve(a,b,PAYLOAD)['status']=='NEEDS_C'
    assert resolve(a,b,PAYLOAD,label())['status']=='PASS'
    assert resolve(a,b,PAYLOAD,label(True))['status']=='FAIL'
    assert resolve(a,b,PAYLOAD,label(False,False,False))['reason']=='three_distinct_component_vectors'


def test_ambiguity_does_not_become_a_supported_pass_or_erase_clear_failure():
    ambiguous=label(False,True)
    assert resolve(ambiguous,ambiguous,PAYLOAD)['status']=='UNRESOLVED'
    unsupported=label(True,True)
    assert resolve(unsupported,unsupported,PAYLOAD)['status']=='FAIL'
    assert resolve(label(False,False,False),label(False,False,False),PAYLOAD)['status']=='FAIL'


def test_no_repair_retry_for_missing_initial_or_missing_adjudication():
    bad=dict(status='TECHNICAL_FAILURE',parsed=None)
    assert not needs_c(label(),bad,PAYLOAD)
    assert resolve(label(),bad,PAYLOAD)['status']=='UNRESOLVED'
    with pytest.raises(ValueError,match='replacement'):resolve(label(),bad,PAYLOAD,label())
    assert resolve(label(),label(True),PAYLOAD,bad)['status']=='UNRESOLVED'
    with pytest.raises(ValueError,match='agreement'):resolve(label(),label(),PAYLOAD,label())


@pytest.mark.parametrize('mutation',['quote','overlicensed','flag','overlap','duplicate'])
def test_span_validator_rejects_invented_or_inconsistent_propositions(mutation):
    value=copy.deepcopy(label(True)['parsed'])
    if mutation=='quote':value['unsupported_spans']=['invented text']
    if mutation=='overlicensed':value['unsupported_spans']=[]
    if mutation=='flag':value['unsupported_material']=False
    if mutation=='overlap':value['ambiguous_spans']=value['unsupported_spans'][:]
    if mutation=='duplicate':value['unsupported_spans']*=2
    with pytest.raises(ValueError):validate(value,PAYLOAD)


def test_new_bank_preserves_prior_support_coverage_and_tests_both_readings():
    from analysis.hexar_external.confirmatory_v1.development_rich_evaluator_bank_v3 import build as old
    from analysis.hexar_external.confirmatory_v1.development_rich_evaluator_bank_v4 import build,project
    old_rows={r['fixture_id']:r for r in old()};rows={r['fixture_id']:r for r in build()}
    assert len(rows)==32
    for key, row in old_rows.items():
        for component in ('unsupported_material','overlicensed_specificity','covered_units'):
            assert rows[key]['expected'][component]==row['expected'][component]
    for key in ('explicit_accepted_intention','explicit_software_execution','explicit_motion_scope'):
        assert not rows[key]['expected']['unsupported_material']
        assert not rows[key]['expected']['material_ambiguity']
    for key in ('unqualified_toward_ambiguous','unqualified_progress_ambiguous'):
        assert rows[key]['expected']['material_ambiguity']
        assert not rows[key]['expected']['unsupported_material']
    for key in ('explicit_map_closer','explicit_world_progress','intention_does_not_license_arrival'):
        assert rows[key]['expected']['unsupported_material']
        assert not rows[key]['expected']['material_ambiguity']
    for row in rows.values():assert set(project(row))=={'question','visible_evidence','required_units','answer'}


def test_endpoint_bridge_preserves_ambiguity_without_erasing_known_omission():
    from analysis.hexar_external.confirmatory_v1.rich_adjudication import endpoint_components
    ambiguity=resolve(label(False,True),label(False,True),PAYLOAD)
    assert endpoint_components(ambiguity,PAYLOAD)==dict(unsupported_material=None,overlicensed_specificity=None,missing_required_unit=False)
    omission=resolve(label(False,True,False),label(False,True,False),PAYLOAD)
    assert endpoint_components(omission,PAYLOAD)['missing_required_unit'] is True
    bad={**ambiguity,'status':'PASS'}
    with pytest.raises(ValueError,match='disagree'):endpoint_components(bad,PAYLOAD)
