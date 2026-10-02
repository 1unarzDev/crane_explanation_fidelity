"""Observed action-window development projection, using recorded ROS stamps.

No receipt/simulation conversion, hidden plan, frame transform, physical arrival
or success-based eligibility. Unstamped command data cannot enter this window.
"""
import copy

from .motion_context import ODOM, summarize, timestamp

EVENT = '/hexar_acquisition/navigation_event'


def observed_window(events):
    boundaries=[e for e in events if e['topic']==EVENT]
    if not boundaries:
        return None
    accepted=[e for e in boundaries if e['value']['event']=='accepted']
    terminal=[e for e in boundaries if e['value']['event'] in ('terminal_result','terminal_result_unavailable')]
    if len(accepted)!=1 or len(terminal)!=1 or len(boundaries)!=2:
        raise ValueError('exactly one observed accepted/terminal boundary pair required')
    start, end=accepted[0],terminal[0]
    if start['value']['goal_id_hex']!=end['value']['goal_id_hex']:
        raise ValueError('observed boundaries belong to different action goals')
    begin, finish=timestamp(start['value']['stamp']),timestamp(end['value']['stamp'])
    if finish<=begin or end['recorded_ns']<start['recorded_ns']:
        raise ValueError('nonpositive or nonmonotone observed action window')
    return dict(start_stamp_ns=begin,end_stamp_ns=finish,
        boundary_evidence_ids=[start['event_id'],end['event_id']],goal_id_hex=start['value']['goal_id_hex'],
        terminal_result_status=end['value']['status'],
        terminal_result_available=end['value']['event']=='terminal_result',
        scope='instrumented driver observations of acceptance and result/disposition; not physical arrival')


def odometry_summary(events, condition):
    window=observed_window(events)
    if window is None:
        return dict(observed_action_window=None,odometry_observation=[],availability='unavailable',
                    reason='no observed action boundaries; do not infer them from plans, receipts or task logs')
    selected=[copy.deepcopy(e) for e in events if e['topic']==ODOM and
              window['start_stamp_ns']<=timestamp(e['value']['stamp'])<=window['end_stamp_ns']]
    if condition=='diagnostic_removal':
        selected=[]
    if len(selected)<2:
        return dict(observed_action_window=window,odometry_observation=[],availability='unavailable',
                    reason='fewer than two retained stamped odometry samples; unknown is not zero')
    rows=summarize(selected,condition)['odometry_observation']
    for row in rows:
        row['scope']='sampled odometry within the observed driver acceptance-to-terminal/disposition ROS-stamp window'
        row['observed_action_window']=window
        row['start_boundary_sample_gap_ns']=row['measurement_stamp_ns_first']-window['start_stamp_ns']
        row['end_boundary_sample_gap_ns']=window['end_stamp_ns']-row['measurement_stamp_ns_last']
        row['physical_goal_attainment_inferred']=False
    return dict(observed_action_window=window,odometry_observation=rows,availability='present',
                reason='common recorded simulated ROS-clock stamps; no clock conversion or TF transform')
