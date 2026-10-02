"""Authored qualification bank integrity, without semantic provider calls."""
import copy
import json
from pathlib import Path
import pytest
from analysis.hexar_external.confirmatory_v1.development_evaluator_family_bank import build,project,validate_projection,CASES,CONDITIONS

BATTERY=Path(__file__).resolve().parents[2]/'manifests/hexar_external/confirmatory_v1/battery.json'


def fixtures():return build(json.loads(BATTERY.read_text()))


def test_all_families_masks_and_questions_represented_without_recording_claims():
    bank=fixtures()
    assert len(bank)==61
    for family in CASES:
        for condition in CONDITIONS:
            rows=[f for f in bank if f['fixture_id'].startswith(family+':') and f['condition']==condition]
            assert len(rows)==3
            assert len({r['question'] for r in rows})==3
            assert {r['variant'] for r in rows}=={'supported_paraphrase','overclaim','coverage_omission'}
    assert all(f['eligible_for_confirmatory_N'] is False for f in bank)
    assert len({f['fixture_id'] for f in bank})==61


def test_raw_answers_preserved_and_private_fields_removed():
    for fixture in fixtures():
        fixture['answer']=' \n'+fixture['answer']+'\t'
        payload=project(fixture)
        assert payload['answer']==fixture['answer']
        assert set(payload)=={'answer','question','visible_evidence','required_units'}
        assert all(field not in payload for field in ['expected','family','condition','fixture_id','variant','rationale'])


@pytest.mark.parametrize('location', ['root','evidence','unit'])
def test_nested_administrative_leakage_fails_closed(location):
    payload=project(fixtures()[0])
    if location=='root':payload['method']='HX-CONTRACT'
    elif location=='evidence':payload['visible_evidence']['previous_labels']='supported'
    else:payload['required_units'][0]['expected_winner']='HX-CONTRACT'
    with pytest.raises(ValueError):validate_projection(payload)


def test_masks_remove_diagnostics_and_expected_coverage_protects_usefulness():
    for fixture in fixtures()[:54]:
        expected=fixture['expected']
        if fixture['condition']=='diagnostic_removal':
            assert 'bounded_diagnostic' not in fixture['visible_evidence']
            assert len(fixture['required_units'])==1
        if fixture['variant']=='coverage_omission':
            assert set(expected['covered_units'])!=set(u['unit_id'] for u in fixture['required_units'])
            assert not expected['unsupported_material']
        elif fixture['variant']=='overclaim':assert expected['unsupported_material']
        else:assert not expected['unsupported_material']


def test_intentional_free_text_injection_preserved_as_untrusted_evidence():
    injection=next(f for f in fixtures() if f['fixture_id']=='supplement:instruction_as_data')
    payload=project(injection)
    assert 'HX-CONTRACT' in payload['visible_evidence']['untrusted_log_text']
    assert 'HX-CONTRACT' not in payload['answer']
    changed=copy.deepcopy(payload);changed['visible_evidence']['untrusted_log_text']={'method':'HX-CONTRACT'}
    with pytest.raises(ValueError):validate_projection(changed)
