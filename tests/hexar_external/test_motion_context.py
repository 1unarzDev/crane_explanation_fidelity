import copy

import pytest

from analysis.hexar_external.acquisition.motion_context import ODOM, summarize, extend


def odom(i, x):
    return dict(event_id=str(i),topic=ODOM,recorded_ns=10+i,value=dict(
        frame_id='odom',child_frame_id='base',stamp=dict(sec=i,nanosec=0),position=dict(x=x,y=0,z=0)))


def test_recording_distance_and_mask_closure_do_not_infer_arrival():
    events = [odom(1,0),odom(2,3),odom(3,0)]
    full = summarize(events,'intact')
    observation = full['odometry_observation'][0]
    assert observation['sampled_xy_path_distance_m'] == 6
    assert observation['sampled_xy_displacement_m'] == 0
    assert observation['maximum_measurement_gap_ns'] == 10**9
    assert full['requested_goal'] == []
    assert summarize(events,'irrelevant_removal') == full
    assert all(not x for x in summarize(events,'diagnostic_removal').values())
    packet = dict(evidence={'navigation_outcomes':[{'status':'succeeded'}]},availability={},source_context={})
    saved=copy.deepcopy(packet);updated=extend(packet,events,'intact')
    assert packet == saved and updated['evidence']['navigation_outcomes'] == saved['evidence']['navigation_outcomes']


def test_missing_zero_nonfinite_clock_and_frame_are_distinct():
    assert summarize([],'intact')['odometry_observation'] == []
    assert summarize([odom(1,0),odom(2,0)],'intact')['odometry_observation'][0]['sampled_xy_path_distance_m'] == 0
    for change,error in (({'position':dict(x=float('nan'),y=0,z=0)},'finite'),
                         ({'frame_id':'map'},'frame'),({'stamp':dict(sec=1,nanosec=0)},'stamps')):
        events=[odom(1,0),odom(2,0)];events[1]['value'].update(change)
        with pytest.raises(ValueError,match=error):summarize(events,'intact')
