import copy
import json
from pathlib import Path
import pytest
from run_evidence_calibration_agent_qualification import _packet
from roboboat_material_qualification_validation_v3 import validate
from evidence_calibration_io import canonical_sha256

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    suite=json.loads((ROOT/'docs/roboboat_terminal_evidence/material_qualification_suite_v2.json').read_text())
    case=suite['cases'][0];packet=_packet(case,'A',canonical_sha256(suite))
    call=next((ROOT/'artifacts/roboboat-material-qualification-v2/pass-A/calls').glob('*.json'))
    returned=json.loads(call.read_text())['parsed_final']
    return packet,returned,case['form']['response_text']


def test_actual_retained_return_uses_bound_two_argument_validator_and_source_checks():
    p,r,t=inputs();assert validate(p,r,t)==r


def test_cached_packet_identity_cannot_be_changed_to_fix_source_validation():
    p,r,t=inputs();p=copy.deepcopy(p);p['response_text']=t
    with pytest.raises(ValueError,match='hash mismatch'):validate(p,r,t)


@pytest.mark.parametrize('category,field',[('required_unit_coverage','communicated'),('limitation_preservation','preserved')])
def test_source_citation_checked_without_mutating_frozen_packet_hash(category,field):
    p,r,t=inputs();r=copy.deepcopy(r);r[category][0]['response_span']='absent fabricated source';r[category][0][field]=True
    with pytest.raises(ValueError,match='verbatim source'):validate(p,r,t)
