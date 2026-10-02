import copy
import json
import math
from pathlib import Path
import pytest
from roboboat_temporal_certificate import audit_ladder, certificate, measure, render, scoped_config, validate_packet
from reference_roboboat_temporal import calculate
ROOT=Path(__file__).resolve().parents[1]


def packet():
    task=json.loads((ROOT/'docs/roboboat_terminal_evidence/task_contract_v1.json').read_text())
    return {'schema':'roboboat-evidence-packet/v1','packet_id':'opaque-1','question':'dock?', 'task':task,
      'configuration':scoped_config((ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()),
      'action':{'status':'succeeded'},'limits':[],
      'post_result':[{'simSeconds':i/50,'frame':'odom',**task['goal'], 'velocity':{'vx':0.,'vy':0.,'yaw_rate':0.,'source':'odom'}} for i in range(401)]}


def test_missing_contact_prevents_full_success_but_keeps_pose_support():
    p=packet();c=certificate(p)
    assert c['sampled_task_support']=='unknown'
    assert c['component_support']['position']=='true'
    assert c['component_support']['contact']=='unknown'
    assert c['continuous_task_support']=='unknown'
    assert calculate(p)['sampled_task_support']=='unknown'


def test_fully_observed_sampled_success_is_not_blanket_refusal():
    p=packet();p['contacts']={'complete':True,'coverage':[0.,8.],'clock':'ros-header-stamp','samples':[]}
    c=certificate(p)
    assert c['sampled_task_support']==calculate(p)['sampled_task_support']=='true'
    assert 'All required conditions held' in render(p,c)
    assert c['continuous_task_support']=='unknown'


@pytest.mark.parametrize('component,field,value',[('position','x',1.),('heading','yaw',2.),('speed','vx',.1),('yaw_rate','yaw_rate',.1)])
def test_single_supported_violation_suffices_with_contact_missing(component,field,value):
    p=packet();r=p['post_result'][100]
    if field in ['vx','yaw_rate']:r['velocity'][field]=value
    else:r[field]+=value
    c=certificate(p)
    assert c['sampled_task_support']==calculate(p)['sampled_task_support']=='false'
    assert c['component_support'][component]=='false'
    assert c['witnesses'][component]['time_s']==2.
    assert c['continuous_task_support']=='false'


def test_fixed_window_does_not_include_late_violations_or_select_favorable_start():
    p=packet();p['post_result'][350]['x']+=2
    c=certificate(p)
    assert c['component_support']['position']=='true'
    assert c['interval_s']==[0.,5.]
    assert c['sampled_task_support']==calculate(p)['sampled_task_support']=='unknown'


@pytest.mark.parametrize('mode',['gap','short','missing-velocity'])
def test_incomplete_evidence_yields_unknown(mode):
    p=packet()
    if mode=='gap':del p['post_result'][2:50]
    elif mode=='short':p['post_result']=p['post_result'][:200]
    else:
        for r in p['post_result']:r.pop('velocity')
    c=certificate(p);assert c['sampled_task_support']==calculate(p)['sampled_task_support']=='unknown'
    assert c['component_support']['speed' if mode=='missing-velocity' else 'position']=='unknown'


def test_wrapped_heading_and_world_motion():
    p=packet();t=p['task'];t['goal']['yaw']=-math.pi+.01
    r=p['post_result'][0];r['yaw']=math.pi-.01
    assert measure(r,t)['heading_error_rad']==pytest.approx(.02)


def test_uncertain_boundary_is_unknown_and_far_violation_false():
    p=packet();p['task']['position_uncertainty_m']=.02
    for r in p['post_result']:r['x']+=.41
    assert certificate(p)['component_support']['position']=='unknown'
    assert calculate(p)['sampled_task_support']=='unknown'
    p['post_result'][100]['x']+=.02
    assert certificate(p)['component_support']['position']=='false'


def test_arclength_not_added_to_radial_error():
    p=packet();g=p['task']['goal']
    for i,r in enumerate(p['post_result']):
        r['x']=g['x']+.1*math.cos(i);r['y']=g['y']+.1*math.sin(i)
    assert certificate(p)['component_support']['position']=='true'


@pytest.mark.parametrize('mutation',['reverse-clock','frame','nan','label','metadata'])
def test_malformed_or_leaking_evidence_fails_closed(mutation):
    p=packet()
    if mutation=='reverse-clock':p['post_result'][1]['simSeconds']=-1
    elif mutation=='frame':p['post_result'][1]['frame']='map'
    elif mutation=='nan':p['post_result'][1]['x']=float('nan')
    elif mutation=='label':p['task']['gold']='true'
    else:p['post_result'][1]['final_pose']={'x':9}
    with pytest.raises(ValueError):certificate(p)


def test_node_plugin_selection_not_first_yaml_match():
    b=(ROOT/'docs/roboboat_terminal_evidence/configs/validated_boat_nav2.yaml').read_bytes()
    b=b'irrelevant:\n  xy_goal_tolerance: 9.0\n'+b
    assert scoped_config(b)['xy_goal_tolerance']==.2
    b=b.replace(b'goal_checker_plugins: [goal_checker]',b'goal_checker_plugins: [goal_checker, other]')
    with pytest.raises(ValueError):scoped_config(b)


def test_real_removal_ladder_and_answer_specificity():
    p=packet();p['return_observation']=copy.deepcopy(p['post_result'][0]);p['post_result'][100]['x']+=1
    l1=copy.deepcopy(p);l1.pop('post_result');l0=copy.deepcopy(l1);l0.pop('return_observation')
    assert audit_ladder([l0,l1,p])['status']=='PASS'
    assert 'unestablished' in render(l0,certificate(l0))
    assert 'result-adjacent observation' in render(l1,certificate(l1))
    assert 'dwell failed' in render(p,certificate(p))
    l0['final_pose']={}
    with pytest.raises(ValueError):validate_packet(l0)
