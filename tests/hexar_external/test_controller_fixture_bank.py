"""Authored expected labels and administration must remain outside blind data."""
import copy
import json
import pytest

from analysis.hexar_external.confirmatory_v1.development_controller_fixture_bank import SOURCE, build
from analysis.hexar_external.confirmatory_v1.rich_blind_projection import reject_administrative


@pytest.fixture(scope='module')
def rows():
    return json.loads(SOURCE.read_text())['packets']


def test_all_six_exposed_packets_get_complete_blind_contrasts(rows):
    fixtures=build(rows)
    assert len(fixtures)==48
    assert len({f['fixture_id'] for f in fixtures})==48
    for fixture in fixtures:
        payload=fixture['payload']
        assert set(payload)=={'question','visible_evidence','required_units','answer'}
        reject_administrative(payload)
        assert fixture['eligible_for_confirmatory_n'] is False
        assert 'expected' not in payload and 'packet_sha256' not in payload
        if fixture['fixture_id'].endswith('wrong_motion_magnitude'):
            assert fixture['expected']['unsupported_material'] is True
            assert fixture['expected']['overlicensed_specificity'] is False
            assert 'recorded_odometry_observation' not in fixture['expected']['covered_units']
        if fixture['fixture_id'].endswith('boundary_observations'):
            assert fixture['expected']['unsupported_material'] is False
            assert 'recorded_odometry_observation' in fixture['expected']['covered_units']


def test_positive_observation_cannot_be_authored_when_boundary_data_disagrees(rows):
    changed=copy.deepcopy(rows)
    first=next(r for r in changed if r['question_id']=='q1' and r['condition']=='intact')
    first['method_packet']['source_context']['controller_runtime_observations'][0]['parameters']['topics.navigation.priority']=99
    with pytest.raises(ValueError,match='actual two-boundary'):
        build(changed)


def test_missing_episode_is_not_silently_dropped(rows):
    with pytest.raises(ValueError,match='six distinct'):
        build(rows[9:])
