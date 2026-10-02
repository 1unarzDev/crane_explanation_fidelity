import pytest

from analysis.hexar_external.acquisition.action_window import EVENT, ODOM, observed_window, odometry_summary


def fixture():
    def boundary(event,sec,receipt,status=None):
        return dict(event_id=event,topic=EVENT,recorded_ns=receipt,value=dict(event=event,stamp=dict(sec=sec,nanosec=0),goal_id_hex='a'*32,status=status))
    def odom(sec,x):
        return dict(event_id='odom-'+str(sec),topic=ODOM,recorded_ns=1000+sec,value=dict(stamp=dict(sec=sec,nanosec=0),frame_id='odom',child_frame_id='base',position=dict(x=x,y=0,z=0)))
    return [boundary('accepted',2,1002),odom(1,100),odom(3,0),odom(4,2),odom(5,100),boundary('terminal_result',4,1005,5)]


def test_measurement_clock_selects_window_without_receipt_conversion_or_success_exclusion():
    value=odometry_summary(fixture(),'intact');row=value['odometry_observation'][0]
    assert row['sampled_xy_path_distance_m']==2
    assert row['messages']==2
    assert value['observed_action_window']['terminal_result_status']==5
    assert row['start_boundary_sample_gap_ns']==10**9
    assert row['end_boundary_sample_gap_ns']==0
    assert not row['physical_goal_attainment_inferred']
    assert odometry_summary(fixture(),'irrelevant_removal')==value
    assert odometry_summary(fixture(),'diagnostic_removal')['availability']=='unavailable'


def test_unavailable_boundary_or_result_never_becomes_zero_or_success():
    assert odometry_summary([],'intact')['observed_action_window'] is None
    assert odometry_summary([],'intact')['odometry_observation']==[]
    events=fixture();events[-1]['value'].update(event='terminal_result_unavailable',status=None)
    window=observed_window(events)
    assert not window['terminal_result_available'] and window['terminal_result_status'] is None
    assert odometry_summary(events,'intact')['availability']=='present'


def test_wrong_goal_or_duplicate_boundary_fails_closed():
    events=fixture();events[-1]['value']['goal_id_hex']='b'*32
    with pytest.raises(ValueError,match='different action goals'):observed_window(events)
    events=fixture();events.append(events[0])
    with pytest.raises(ValueError,match='exactly one'):observed_window(events)
