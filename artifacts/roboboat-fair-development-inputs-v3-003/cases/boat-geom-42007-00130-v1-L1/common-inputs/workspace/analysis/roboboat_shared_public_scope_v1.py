"""Neutral common input/scope checks; no claim planning, realization or answers."""
import math
import yaml
from roboboat_temporal_certificate_v2 import validate_packet
from roboboat_temporal_certificate import scoped_config


def validate_public_inputs(packet, configuration_bytes):
    configuration=yaml.safe_load(configuration_bytes)
    forbidden={'gold','gold_labels','evaluator_truth','dockingSuccessObserved',
               'diagnostic_result','checked_answer','reference_answer','expectedNavigationStatus'}
    def public_only(value):
        if isinstance(value,dict):
            if set(value)&forbidden: raise ValueError('evaluator/answer metadata in supplied configuration')
            for child in value.values(): public_only(child)
        elif isinstance(value,list):
            for child in value: public_only(child)
    public_only(configuration)
    validate_packet(packet)
    task, action = packet['task'], packet['action']
    if task.get('clock') != 'ros-header-stamp':
        raise ValueError('unsupported sample clock')
    if task.get('measurement_scope') != 'sampled-delivered-simulator-odometry':
        raise ValueError('unsupported measurement scope')
    for row in [packet.get('return_observation'), *packet.get('post_result', [])]:
        if row is not None and 'velocity' in row and row['velocity'].get('source') != 'delivered-odometry-twist-body-to-odom':
            raise ValueError('unsupported delivered velocity source')
    reference = packet.get('return_observation')
    if reference is not None and reference.get('alignment') not in (
            'latest-delivered-at-client-receipt', 'last-pre-result-observation'):
        raise ValueError('unsupported reference alignment')
    if action['status'] not in ('succeeded', 'aborted', 'canceled', 'timeout'):
        raise ValueError('unsupported action status')
    if action['status'] == 'timeout' and (
            action.get('event_time_support') == 'recorded-client-receipt'
            or action.get('receipt_wall_seconds') is not None or action.get('receipt_clock') is not None
            or packet.get('post_result') or (reference is not None and
                reference.get('alignment') == 'latest-delivered-at-client-receipt')):
        raise ValueError('fixture timeout contradicts terminal result evidence')
    for key in ('xy_goal_tolerance', 'yaw_goal_tolerance', 'trans_stopped_velocity', 'rot_stopped_velocity'):
        value = packet['configuration'].get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('configured limit must be finite nonnegative number')
    if action.get('event_time_support') == 'recorded-client-receipt':
        value = action.get('receipt_wall_seconds')
        if action.get('receipt_clock') != 'fixture-monotonic':
            raise ValueError('unsupported receipt clock')
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError('invalid receipt time')
    if packet['configuration'] != scoped_config(configuration_bytes, packet['configuration'].get('plugin_id')):
        raise ValueError('visible configuration does not match exact supplied YAML')
    return {'status': 'PUBLIC_INPUT_SCOPE_VALID', 'answers_generated': 0,
            'interpretation': 'Input compatibility only; no physical outcome or claim selection.'}
