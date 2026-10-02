"""Exercise the real result callback without importing the ROS runtime."""
import ast
import math
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]

def test_result_callback_captures_actual_receipt_and_separate_odom_stamp():
    path=ROOT/'packages/crane_ml/Tools/Performance/nav2_follow_path_fixture.py'
    tree=ast.parse(path.read_text())
    method=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='on_result')
    module=ast.Module(body=[method],type_ignores=[])
    env={'time':SimpleNamespace(monotonic=lambda:110.25),'ACTION_STATUS':{4:'succeeded'},
         'pose_dict':lambda _: {'x':1.,'y':2.,'yaw':0.}}
    exec(compile(module,str(path),'exec'),env)
    events=[]
    obj=SimpleNamespace(started_wall=100.,latest_odom=object(),args=SimpleNamespace(odom_topic='/crane/odom'),
       action_name='/follow_path',goal_handle=SimpleNamespace(goal_id=SimpleNamespace(uuid=[1,2,3])),
       trajectory_sample=lambda _: {'simSeconds':8.0,'phase':'post_result'},publish_event=events.append)
    env['on_result'](obj,SimpleNamespace(result=lambda:SimpleNamespace(status=4,result=SimpleNamespace())))
    assert obj.terminal_event_v2['receipt_wall_seconds']==10.25
    assert obj.terminal_event_v2['measurement']['simSeconds']==8.
    assert obj.terminal_event_v2['goal_id']==events[0]['goal_id']=='010203'
    assert obj.result_received_wall==110.25
    assert obj.action_result_pose['x']==1.
