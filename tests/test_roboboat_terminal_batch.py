import copy,json
from pathlib import Path
import pytest
from roboboat_temporal_certificate import build_ladder,certificate
from reference_roboboat_temporal import calculate
from run_roboboat_terminal_comparison import annotation_packet
ROOT=Path(__file__).resolve().parents[1]

def source():
    task=json.loads((ROOT/'docs/roboboat_terminal_evidence/task_contract_v1.json').read_text())
    g=task['goal'];rows=[]
    for i in range(401):
        rows.append({'phase':'post_result','frameId':'odom','childFrameId':'base_link','simSeconds':10+i*.02,
                     **g,'bodySurge':.02,'bodySway':.01,'bodyYawRate':.0})
    pre={**rows[0],'simSeconds':9.98,'phase':'action'}
    return task,{'status':'succeeded','actionName':'/follow_path','provenance':'latest-delivered-odometry-not-proven-internal-consumption',
    'plannedPath':[g],'trajectory':[pre,*rows], 'dockingSuccessObserved':True,'dockingEvaluations':[{'success':True}],
    'terminalEventV2':{'goal_id':'opaque-uuid','receipt_wall_seconds':11.23,'measurement':pre}}


def test_additive_event_identity_and_clock_never_replaced_by_first_post_sample():
    task,s=source();b=(ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    ladder=build_ladder(s,b,task,'opaque-test')
    assert ladder[2]['action']['receipt_wall_seconds']==11.23
    assert ladder[2]['return_observation']['simSeconds']==9.98
    assert ladder[2]['post_result'][0]['simSeconds']==10
    assert 'dockingSuccessObserved' not in json.dumps(ladder)
    assert 'post_result' not in ladder[0] and 'return_observation' not in ladder[0]
    assert 'post_result' not in ladder[1]
    assert ladder[2]['return_observation']['velocity']['vx']==pytest.approx(-.01)
    assert ladder[2]['return_observation']['velocity']['vy']==pytest.approx(.02)


def test_failed_action_supported_population_not_success_selected():
    task,s=source();s['status']='aborted';s.pop('terminalEventV2')
    b=(ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    ladder=build_ladder(s,b,task,'opaque-test')
    assert ladder[0]['action']['status']=='aborted'
    assert ladder[2]['action']['receipt_wall_seconds'] is None


def test_method_blind_inventory_keeps_negation_and_complete_packet():
    task,s=source();b=(ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    p=build_ladder(s,b,task,'opaque-test')[2]
    text='The evidence does not show waves caused drift. Completion is unknown.'
    judge=annotation_packet(p,text,calculate(p),'opaque-judgment')
    assert judge['response_text']==text
    assert 'B2' not in json.dumps(judge) and 'B4' not in json.dumps(judge)
    assert judge['forms'][0]['atomic_statements'][0]['statement']=='The evidence does not show waves caused drift.'
    assert judge['forms'][0]['robot_visible_evidence']==p


def test_independent_reference_randomized_pose_and_motion():
    import random
    task,s=source();b=(ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    p=build_ladder(s,b,task,'opaque-test')[2];rng=random.Random(431)
    for _ in range(60):
        q=copy.deepcopy(p)
        r=q['post_result'][rng.randrange(250)]
        r['x']+=rng.uniform(-1,1);r['y']+=rng.uniform(-1,1);r['yaw']+=rng.uniform(-4,4)
        r['velocity']['vx']=rng.uniform(-.15,.15)
        assert certificate(q)['sampled_task_support']==calculate(q)['sampled_task_support']
