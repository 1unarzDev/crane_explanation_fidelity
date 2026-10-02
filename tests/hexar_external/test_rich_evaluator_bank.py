import copy

import pytest

from analysis.hexar_external.confirmatory_v1.development_rich_evaluator_bank import UNITS, build, project


def test_positive_source_and_motion_fixtures_and_conflict_omissions_are_distinct():
    fixtures={f['fixture_id']:f for f in build()}
    for key in ('source_rule_positive','conditional_rule_positive','higher_priority_positive','observed_command_positive'):
        assert fixtures[key]['expected']==dict(unsupported_material=False,overlicensed_specificity=False,covered_units=list(UNITS))
    for key in ('omit_motion','omit_diagnostic','blanket_refusal'):
        assert not fixtures[key]['expected']['unsupported_material']
        assert len(fixtures[key]['expected']['covered_units']) < len(UNITS)
    # Unsupported extra detail does not erase separately correct units.
    assert fixtures['physical_arrival_overclaim']['expected']['covered_units']==list(UNITS)
    assert fixtures['physical_arrival_overclaim']['expected']['unsupported_material']
    assert fixtures['literal_zero_error']['expected']['covered_units']==list(UNITS[:2])


def test_nested_judge_projection_excludes_labels_and_administrative_metadata():
    fixture=build()[0];fixture['method']='HX-CONTRACT';fixture['family']='manual';fixture['prior_result']='100%'
    payload=project(fixture)
    assert set(payload)=={'question','visible_evidence','required_units','answer'}
    assert 'expected' not in payload
    hidden=copy.deepcopy(fixture);hidden['visible_evidence']['expected_winner']='CRANE'
    with pytest.raises(ValueError,match='closed authored evidence'):project(hidden)
    hidden=copy.deepcopy(fixture);hidden['required_units'][0]['prior_label']=True
    with pytest.raises(ValueError,match='nested label leakage'):project(hidden)


def test_annotation_candidate_does_not_admit_provider_or_missing_masked_units():
    from analysis.hexar_external.confirmatory_v1.rich_evaluator_candidate import request,validate
    fixture=next(f for f in build() if f['fixture_id']=='masked_bounded')
    declaration=request(fixture)
    assert not declaration['provider_admitted'] and not declaration['execution_schedule_declared']
    correct=dict(unsupported_material=False,overlicensed_specificity=False,covered_units=[UNITS[0]],rationale='Reported software outcome only.')
    assert validate(correct,declaration['payload'])==correct
    for units in ([UNITS[1]],[UNITS[0],UNITS[0]]):
        wrong={**correct,'covered_units':units}
        with pytest.raises(ValueError,match='submitted required IDs'):validate(wrong,declaration['payload'])
    with pytest.raises(ValueError,match='scalar types'):
        validate({**correct,'unsupported_material':0},declaration['payload'])


def test_v3_taxonomy_preserves_primary_support_labels_and_blinding():
    from analysis.hexar_external.confirmatory_v1.development_rich_evaluator_bank_v3 import build as revised
    old={f['fixture_id']:f for f in build()}
    new={f['fixture_id']:f for f in revised()}
    assert len(new)==24
    for key,fixture in old.items():
        assert new[key]['expected']['unsupported_material']==fixture['expected']['unsupported_material']
        assert new[key]['expected']['covered_units']==fixture['expected']['covered_units']
        if key!='masked_invented_motion':
            assert new[key]['expected']==fixture['expected']
    assert new['masked_invented_motion']['expected']['unsupported_material']
    assert not new['masked_invented_motion']['expected']['overlicensed_specificity']
    for fixture in new.values():
        assert not fixture['expected']['overlicensed_specificity'] or fixture['expected']['unsupported_material']
        assert set(project(fixture))=={'question','visible_evidence','required_units','answer'}


def test_v2_rejects_specificity_without_unsupported_material():
    from analysis.hexar_external.confirmatory_v1.rich_evaluator_v2 import validate
    payload=project(build()[0])
    wrong=dict(unsupported_material=False,overlicensed_specificity=True,covered_units=[],rationale='Inconsistent flags.')
    with pytest.raises(ValueError,match='must also be unsupported'):validate(wrong,payload)
