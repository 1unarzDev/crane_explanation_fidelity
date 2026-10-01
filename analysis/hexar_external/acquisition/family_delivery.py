"""Outcome-blind candidate checks on hidden acquisition setup observations.

No method answer, navigation result, judge label or semantic family outcome is
used. This validates setup delivery, not continuous motion or physical causation.
"""
import math
from .reset_geometry import review as reset_review
from .scenario_geometry import trajectory
from .plan import FAMILIES


def checks(episode,planned_family):
    if planned_family not in FAMILIES:
        raise ValueError('known frozen family required')
    sampling=episode.get('sampling_hidden',{})
    measurements=episode.get('reset_measurements_hidden',[])
    good_reset=False
    try:
        rebuilt=[reset_review((row['x'],row['y'],row['z']),row['quaternion_xyzw'],sampling['start_xy'],sampling['start_yaw']) for row in measurements]
        good_reset=len(rebuilt)>=3 and all(row['in_tolerance'] for row in rebuilt[-3:])
    except (KeyError,TypeError,ValueError):pass
    consumers=episode.get('indicator_consumers_hidden',{})
    configured=all(any(row.get('node_name')=='twist_mux' and row.get('topic_type')=='std_msgs/msg/Bool' for row in consumers.get(topic,[]))
        for topic in ('/power/is_charging','/joy_priority'))
    result=dict(measured_position_and_heading_reset=good_reset,
        actual_indicator_consumer_observed=configured,
        indicator_states_published_before_goal=type(episode.get('indicator_prelude_publications_per_topic')) is int
            and episode['indicator_prelude_publications_per_topic']==3,
        assigned_family_matches_driver=episode.get('family_hidden')==planned_family)
    observed=episode.get('intervention_observations_hidden',[])
    def valid_pose(row):
        try:
            requested,actual=row['requested_xyz'],row['observed_xyz']
            return (len(requested)==len(actual)==3 and all(type(v) in (int,float) and math.isfinite(v) for v in (*requested,*actual))
                and math.dist(requested,actual)<=.05 and type(row['observed_sim_stamp_ns']) is int and row['observed_sim_stamp_ns']>=0)
        except (KeyError,TypeError,ValueError):return False
    if planned_family in ('obstacle','dynamic_env'):
        spawn=[row for row in observed if row.get('stage')=='spawn']
        result['measured_spawn_pose_matches_request']=len(spawn)==1 and valid_pose(spawn[0])
    else:
        result['no_unassigned_obstruction']=observed==[] and episode.get('dynamic_trajectory_hidden') is None
    if planned_family=='dynamic_env':
        rows=[row for row in observed if row.get('stage')=='dynamic_prelude']
        try:
            profile=trajectory(episode['seed_hidden'],sampling['start_xy'],sampling['goal_xy'])
            bound=all(row['requested_xyz'][0]==profile['anchor_xy'][0] and abs(row['requested_xyz'][1]-profile['anchor_xy'][1])<=.8+1e-12
                      and row['requested_xyz'][2]==.6 for row in rows)
        except (KeyError,TypeError,ValueError):profile=None;bound=False
        result['independently_seeded_native_time_trajectory']=profile is not None and episode.get('dynamic_trajectory_hidden')==profile
        result['three_measured_pre_goal_positions']=len(rows)==3 and all(valid_pose(row) for row in rows) and bound
        result['prelude_observation_stamps_ordered']=len(rows)==3 and all(type(row.get('observed_sim_stamp_ns')) is int for row in rows) and all(a['observed_sim_stamp_ns']<b['observed_sim_stamp_ns'] for a,b in zip(rows,rows[1:]))
        result['actual_pre_goal_position_change_observed']=len(rows)==3 and all(valid_pose(row) for row in rows) and any(math.dist(a['observed_xyz'],b['observed_xyz'])>0 for a,b in zip(rows,rows[1:]))
    if planned_family=='localization':
        expected={'max_beams':(2,5),'z_hit':(3,.01),'z_rand':(3,.99),'update_min_d':(3,.01),'update_min_a':(3,.01)}
        values=episode.get('localization_parameters_observed_hidden',[])
        names=[row.get('name') for row in values]
        acks=episode.get('localization_parameters_accepted',[])
        result['five_localization_parameter_acks']=type(acks) is list and len(acks)==5 and all(v is True for v in acks)
        result['five_matching_parameter_readbacks']=len(values)==5 and set(names)==set(expected) and all(
            row.get('type')==expected[row['name']][0]
            and row.get('integer_value' if expected[row['name']][0]==2 else 'double_value')==expected[row['name']][1] for row in values)
    return result
