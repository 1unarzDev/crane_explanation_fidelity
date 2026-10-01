import copy
import json

from analysis.hexar_external.confirmatory_v1.development_motion_fixture_bank import SOURCE,build
from analysis.hexar_external.confirmatory_v1.motion_usefulness import PUBLIC_REQUIREMENT
from analysis.hexar_external.acquisition.navigation_usefulness_v2 import public_packet,reference
from analysis.hexar_external.confirmatory_v1.rich_blind_projection import reject_administrative


def rows():
    return json.loads(SOURCE.read_text())['packets']


def test_public_and_reference_requirements_are_identical_without_mutating_history():
    original=next(r['method_packet'] for r in rows() if r['condition']=='intact')
    preserved=copy.deepcopy(original);packet=public_packet(original)
    assert original==preserved
    assert packet['evidence']==original['evidence']
    assert packet['public_communication_requirements']['useful_motion']==PUBLIC_REQUIREMENT
    motion=next(u for u in reference(packet)['required_units'] if u['unit_id']=='recorded_odometry_observation')
    assert motion['requirement']==PUBLIC_REQUIREMENT
    assert motion['maximum_expressed_resolution_or_range_width_m']=='0.1'
    assert motion['no_motion_threshold'] is None


def test_absent_masked_motion_does_not_create_a_hidden_required_unit():
    packet=public_packet(next(r['method_packet'] for r in rows() if r['condition']=='diagnostic_removal'))
    assert not any(u['unit_id']=='recorded_odometry_observation' for u in reference(packet)['required_units'])


def test_authored_fixture_bank_preserves_blinding_and_predeclared_contrasts():
    fixtures=build(rows())
    assert len(fixtures)==48 and len({f['fixture_id'] for f in fixtures})==48
    for fixture in fixtures:
        reject_administrative(fixture['payload'])
        expected=fixture['expected']
        assert not fixture['eligible_for_confirmatory_n']
        has_motion='recorded_odometry_observation' in expected['covered_units']
        if fixture['fixture_id'].endswith(('fine_rounding','narrow_range','physical_immobility')):
            assert has_motion
        else: assert not has_motion
