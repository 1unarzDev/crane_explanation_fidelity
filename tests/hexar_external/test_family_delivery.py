import copy
import json
from pathlib import Path
from analysis.hexar_external.acquisition.family_delivery import checks

BASE=Path(__file__).resolve().parents[2]/'manifests/hexar_external/acquisition'


def fixture(family):
    return json.loads((BASE/f'hexar-tiago-dev-{family}-0015/episode.json').read_text())


def test_actual_six_family_setup_checks_ignore_navigation_result():
    for family in ('charging','dynamic_env','localization','manual_joystick','obstacle','success'):
        value=fixture(family)
        assert all(checks(value,family).values())
        value.update(terminal_action_status=None,timeout=True,accepted=False)
        # Goal acceptance is another technical check; result success never is.
        assert all(checks(value,family).values())


def test_wrong_reset_heading_and_missing_actual_consumer_cannot_qualify():
    value=fixture('charging')
    for row in value['reset_measurements_hidden']:row['quaternion_xyzw']=[0.,0.,0.,1.]
    assert not checks(value,'charging')['measured_position_and_heading_reset']
    value=fixture('charging');value['indicator_consumers_hidden']={}
    assert not checks(value,'charging')['actual_indicator_consumer_observed']


def test_missing_dynamic_observation_or_changed_seed_profile_fails():
    value=fixture('dynamic_env');value['intervention_observations_hidden'].pop()
    assert not checks(value,'dynamic_env')['three_measured_pre_goal_positions']
    value=fixture('dynamic_env');value['dynamic_trajectory_hidden']['phase_rad']+=.1
    assert not checks(value,'dynamic_env')['independently_seeded_native_time_trajectory']


def test_localization_ack_is_not_a_substitute_for_actual_readback():
    value=fixture('localization');value['localization_parameters_observed_hidden'][0]['integer_value']=99
    assert checks(value,'localization')['five_localization_parameter_acks']
    assert not checks(value,'localization')['five_matching_parameter_readbacks']
