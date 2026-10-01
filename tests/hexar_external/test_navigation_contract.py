import copy
import json
from pathlib import Path

import pytest

from analysis.hexar_external.acquisition.navigation_contract import contract, ontology
from analysis.hexar_external.acquisition.navigation_references import build

ROOT = Path(__file__).resolve().parents[2]


def packets():
    return json.loads((ROOT/'manifests/hexar_external/acquisition/navigation_packet_qualification_v1.json').read_text())['packets']


def test_unexpected_success_keeps_motion_and_source_bound_diagnostic():
    record = next(r for r in packets() if 'manual_joystick' in r['development_id'] and r['condition']=='intact')
    packet = record['method_packet'];saved=copy.deepcopy(packet)
    reference = build(packet)
    output = contract(packet,'dev-manual-regression',record['development_id'])
    assert packet == saved
    assert 'software reported success' in output['answer']
    assert 'manual-priority indicator' in output['answer']
    assert '4.63926838617e-06 m' in output['answer']
    assert 'sampled recording window' in output['answer']
    assert 'do not alone establish physical goal attainment' in output['answer']
    assert len(output['answer'].split())<=60
    assert len(output['realization']['final_clauses'])==3
    assert {u['unit_id'] for u in reference['required_units']} == {
        'reported_navigation_outcome','bounded_diagnostic_observation','recorded_odometry_observation'}
    assert reference['required_units'][-1]['no_motion_threshold'] is None
    assert not output['realization']['audit']['missing_required_claim_ids']
    assert not output['realization']['audit']['numeric_mismatches']


def test_diagnostic_mask_does_not_turn_unknown_motion_into_zero():
    record = next(r for r in packets() if r['condition']=='diagnostic_removal')
    reference = build(record['method_packet']);output=contract(record['method_packet'],'dev-masked',record['development_id'])
    assert {u['unit_id'] for u in reference['required_units']} == {'reported_navigation_outcome'}
    assert 'claim-motion' not in output['plan']['required_claim_ids']
    assert output['plan']['approved_numeric_values'] == []
    assert 'odometry estimates' not in output['answer']


def test_invalid_numeric_evidence_cannot_enter_reference_or_contract():
    record = next(r for r in packets() if r['condition']=='intact')
    for invalid in (float('nan'),-1,True):
        packet=copy.deepcopy(record['method_packet'])
        packet['evidence']['odometry_observation'][0]['sampled_xy_path_distance_m']=invalid
        with pytest.raises(ValueError):build(packet)
        with pytest.raises(ValueError):contract(packet,'dev-invalid',record['development_id'])


def test_realizer_repairs_unlicensed_or_altered_numeric_clauses():
    from realize_evidence_calibrated_explanation import realize
    from evidence_calibration_io import canonical_sha256
    record = next(r for r in packets() if r['condition']=='intact')
    output=contract(record['method_packet'],'dev-repair',record['development_id']);plan=output['plan']
    bad=dict(schema='crane-claim-realization-candidate/v1',response_id='dev-repair',plan_sha256=canonical_sha256(plan),clauses=[
        dict(clause_id='fabricated',kind='CLAIM',contract_id='claim-physical',numeric_values=[]),
        dict(clause_id='wrong-distance',kind='CLAIM',contract_id='claim-motion',numeric_values=[dict(slot_id='path_distance',value=999,unit='m')])])
    repaired=realize(ontology(),output['diagnostic_result'],plan,bad)
    assert repaired['audit']['status']=='REPAIRED'
    assert list(repaired['audit']['unapproved_claim_ids'])==['claim-physical']
    assert list(repaired['audit']['numeric_mismatches'])==['claim-motion:path_distance']
    assert {c['text'] for c in repaired['final_clauses']} == {c['text'] for c in output['realization']['final_clauses']}
