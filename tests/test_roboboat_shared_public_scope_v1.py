import copy
import json
import pytest
from roboboat_shared_public_scope_v1 import validate_public_inputs
from roboboat_temporal_certificate import scoped_config
from roboboat_temporal_certificate_v2 import POLICY


def public_inputs():
    configuration=b'''controller_server:
  ros__parameters:
    goal_checker_plugins: [goal_checker]
    goal_checker:
      plugin: nav2_controller::StoppedGoalChecker
      xy_goal_tolerance: 0.2
      yaw_goal_tolerance: 0.35
      trans_stopped_velocity: 0.02
      rot_stopped_velocity: 0.02
'''
    pose={'x':0.,'y':0.,'yaw':0.}
    task={'schema':'roboboat-terminal-task/v2','id':'construction-task','frame':'odom',
        'clock':'ros-header-stamp','goal':pose,'berth_center':copy.deepcopy(pose),
        'position_tolerance_m':0.4,'heading_tolerance_rad':0.35,'speed_tolerance_mps':0.05,
        'yaw_rate_tolerance_radps':0.05,'hull_length_m':1.063,'hull_beam_m':0.895,
        'berth_depth_m':3.,'berth_width_m':2.,'dwell_s':5.,'capture_s':8.,
        'max_sample_gap_s':0.06,'position_uncertainty_m':0.,'heading_uncertainty_rad':0.,
        'speed_uncertainty_mps':0.,'yaw_rate_uncertainty_radps':0.,
        'interval_policy':'first-post-result-observation-fixed-dwell','contact_policy':copy.deepcopy(POLICY),
        'measurement_scope':'sampled-delivered-simulator-odometry','continuous_time_proof':False,
        'uncertainty_basis':'Numerical simulator measurements; no intersample bound.'}
    packet={'schema':'roboboat-evidence-packet/v2','packet_id':'construction-packet',
        'question':'Explain the navigation and docking evidence.','task':task,
        'configuration':scoped_config(configuration),
        'action':{'status':'succeeded','name':'/navigate_to_pose','identity':'construction-goal',
                  'event_time_support':'recorded-client-receipt','receipt_clock':'fixture-monotonic',
                  'receipt_wall_seconds':10.25},'limits':['Delivered observations do not prove consumption.']}
    return packet,configuration


def test_neutral_validation_preserves_exact_public_inputs_and_generates_no_answers():
    p,c=public_inputs();original=copy.deepcopy(p)
    result=validate_public_inputs(p,c)
    assert result['answers_generated']==0 and result['status']=='PUBLIC_INPUT_SCOPE_VALID'
    assert p==original and p['task']['position_tolerance_m']!=p['configuration']['xy_goal_tolerance']


@pytest.mark.parametrize('field,value',[('clock','fixture-monotonic'),('measurement_scope','hardware')])
def test_explicit_public_sample_scope_prerequisites(field,value):
    p,c=public_inputs();p['task'][field]=value
    with pytest.raises(ValueError):validate_public_inputs(p,c)


def test_body_twist_reference_alignment_and_receipt_clocks_are_explicit():
    p,c=public_inputs()
    row={'x':0.,'y':0.,'yaw':0.,'simSeconds':5.,'frame':'odom',
         'alignment':'last-pre-result-observation',
         'velocity':{'vx':0.,'vy':0.,'yaw_rate':0.,'source':'delivered-odometry-twist-body-to-odom'}}
    p['return_observation']=row;validate_public_inputs(p,c)
    row['alignment']='consumed-by-nav2'
    with pytest.raises(ValueError,match='alignment'):validate_public_inputs(p,c)
    row['alignment']='last-pre-result-observation';row['velocity']['source']='physical-truth'
    with pytest.raises(ValueError,match='velocity source'):validate_public_inputs(p,c)
    del row['velocity'];p['action']['receipt_clock']='ros-header-stamp'
    with pytest.raises(ValueError,match='receipt clock'):validate_public_inputs(p,c)


def test_fixture_timeout_is_not_cancellation_completion_or_result():
    p,c=public_inputs();p['action'].update(status='timeout',event_time_support='historical-event-time-unavailable',
        receipt_clock=None,receipt_wall_seconds=None)
    validate_public_inputs(p,c)
    p['action']['receipt_wall_seconds']=2
    with pytest.raises(ValueError,match='timeout contradicts'):validate_public_inputs(p,c)
    p['action']['receipt_wall_seconds']=None
    p['post_result']=[{'x':0.,'y':0.,'yaw':0.,'simSeconds':5.,'frame':'odom'}]
    with pytest.raises(ValueError,match='timeout contradicts'):validate_public_inputs(p,c)


@pytest.mark.parametrize('value',[True,-1,float('nan'),'0.2'])
def test_configured_observation_prerequisites_and_exact_yaml(value):
    p,c=public_inputs();p['configuration']['xy_goal_tolerance']=value
    with pytest.raises(ValueError,match='configured limit'):validate_public_inputs(p,c)


def test_configuration_yaml_mismatch_and_hidden_truth_rejected():
    p,c=public_inputs();p['configuration']['xy_goal_tolerance']=0.3
    with pytest.raises(ValueError,match='exact supplied YAML'):validate_public_inputs(p,c)
    p,c=public_inputs();p['gold']='hidden'
    with pytest.raises(ValueError):validate_public_inputs(p,c)


def test_even_source_hash_matched_yaml_cannot_stage_evaluator_answers():
    p,c=public_inputs();c+=b'gold: hidden-episode-answer\n';p['configuration']=scoped_config(c)
    with pytest.raises(ValueError,match='evaluator/answer metadata'):
        validate_public_inputs(p,c)
