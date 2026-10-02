import pytest
from build_roboboat_settling_batch import checked_configuration
from pathlib import Path


def test_effective_stopping_thresholds_must_match_actual_selected_node_plugin():
    base=Path('docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    row={'internal_xy_tolerance_m':.2,'internal_trans_stopped_velocity_mps':.02,'internal_rot_stopped_velocity_radps':.02}
    params={'goal_checker_plugins':['selected'],'selected.plugin':'nav2_controller::StoppedGoalChecker',
        'selected.xy_goal_tolerance':.2,'selected.yaw_goal_tolerance':.35,
        'selected.trans_stopped_velocity':.02,'selected.rot_stopped_velocity':.02,
        'unused.trans_stopped_velocity':.05}
    readback={'schema':'crane-nav2-runtime-parameters/v1','nodes':{'/controller_server':params}}
    assert b'trans_stopped_velocity: 0.02' in checked_configuration(base,readback,row)
    params['selected.trans_stopped_velocity']=.05
    with pytest.raises(ValueError,match='stopping override'):checked_configuration(base,readback,row)
    params['selected.trans_stopped_velocity']=.02;params['selected.plugin']='other'
    with pytest.raises(ValueError,match='identity'):checked_configuration(base,readback,row)
