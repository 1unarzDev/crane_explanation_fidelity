import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('runtime_parameters', ROOT / 'packages/crane_ml/'
    'Tools/Performance/capture_nav2_runtime_parameters.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_scoped_runtime_plugin_selection_ignores_other_nodes_and_plugins():
    controller = {'goal_checker_plugins': ['dock'], 'controller_plugins': ['boat'],
        'dock.plugin': 'StoppedGoalChecker', 'dock.xy_goal_tolerance': .2,
        'boat.plugin': 'PurePursuit', 'unused.xy_goal_tolerance': 9.}
    result = MODULE.assemble({'/controller_server': controller,
                             '/other': {'dock.xy_goal_tolerance': 7.}})
    selected = result['selected_controller_plugins']
    assert selected['goal_checker_plugins']['dock']['xy_goal_tolerance'] == .2
    assert 'unused' not in selected['goal_checker_plugins']


@pytest.mark.parametrize('controller', [
    {}, {'goal_checker_plugins': ['dock'], 'dock.xy_goal_tolerance': .2},
    {'goal_checker_plugins': [], 'controller_plugins': ['boat']}])
def test_unavailable_runtime_identity_fails_closed(controller):
    with pytest.raises(ValueError):
        MODULE.assemble({'/controller_server': controller})


def test_batch_uses_measured_override_and_rejects_launch_mismatch():
    from build_roboboat_terminal_batch import runtime_config
    from roboboat_temporal_certificate import scoped_config
    base=(ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    readback={'schema':'crane-nav2-runtime-parameters/v1','nodes':{'/controller_server':{
        'goal_checker_plugins':['dock'], 'dock.plugin':'nav2_controller::StoppedGoalChecker',
        'dock.xy_goal_tolerance':.4,'dock.yaw_goal_tolerance':.35,
        'dock.trans_stopped_velocity':.05,'dock.rot_stopped_velocity':.05}}}
    actual=scoped_config(runtime_config(base,readback,.4))
    assert actual['plugin_id']=='dock' and actual['xy_goal_tolerance']==.4
    with pytest.raises(ValueError,match='registered launch'):
        runtime_config(base,readback,.2)
