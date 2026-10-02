"""Pure technical review of observed controller snapshots; no semantic labels."""
from .motion_context import timestamp

OUTPUT = '/mobile_base_controller/cmd_vel_unstamped'
INPUTS = {'navigation': ('cmd_vel', 10), 'keyboard': ('key_vel', 90),
          'joystick': ('joy_vel', 100), 'rviz': ('rviz_joy_vel', 100),
          'webgui_joystick': ('tab_vel', 100), 'assisted_teleop': ('assisted_vel', 200),
          'docking': ('docking_vel', 210)}
LOCKS = {'joystick': ('joy_priority', 100),
         'assisted_teleop': ('assisted_teleop_priority', 200),
         'charging': ('power/is_charging', 210)}


def validate(snapshot):
    """Require full expected public mux parameters and actual base receiver.

    This is a candidate integrity predicate, not continuous-wiring attestation.
    The complete actual snapshot remains evidence, including other receivers.
    """
    if snapshot.get('schema') != 'hexar-observed-controller-context/v1' or snapshot.get('node') != '/twist_mux':
        raise ValueError('known observed controller snapshot required')
    if timestamp(snapshot['stamp']) <= 0:
        raise ValueError('positive native simulated timestamp required')
    expected = {'use_sim_time': True}
    for group, rows, timeout in [('topics', INPUTS, .5), ('locks', LOCKS, 0.)]:
        for name, (topic, priority) in rows.items():
            expected.update({f'{group}.{name}.topic': topic,
                             f'{group}.{name}.priority': priority,
                             f'{group}.{name}.timeout': timeout})
    observed = snapshot['parameters']
    if set(observed) != set(expected) or any(type(observed[k]) is not type(v) or observed[k] != v for k, v in expected.items()):
        raise ValueError('complete typed public mux parameters required')
    for rows, msg in [(INPUTS, 'geometry_msgs/msg/Twist'), (LOCKS, 'std_msgs/msg/Bool')]:
        for topic, _ in rows.values():
            if msg not in snapshot['subscribers'].get('/' + topic, []):
                raise ValueError('expected observed mux subscription required')
    if 'geometry_msgs/msg/Twist' not in snapshot['publishers'].get(OUTPUT, []):
        raise ValueError('observed mux output publisher required')
    if not any(r.get('node_name') == 'mobile_base_controller' and r.get('node_namespace') == '/'
               and r.get('topic_type') == 'geometry_msgs/msg/Twist' for r in snapshot['output_receivers']):
        raise ValueError('actual mobile base controller receiver required')
    return snapshot


def extend(packet, snapshots, condition):
    """Equal-evidence boundary snapshots; mask before projecting observations.

    Input is public observed snapshots only, never the probe's technical review.
    No assertion about continuous configuration or causation is added.
    """
    import copy
    if condition not in ('intact', 'irrelevant_removal', 'diagnostic_removal'):
        raise ValueError('unknown evidence condition')
    if type(snapshots) is not list or len(snapshots) != 2:
        raise ValueError('start and end controller snapshots required')
    for snapshot in snapshots:
        validate(snapshot)
        if set(snapshot) != {'schema', 'stamp', 'node', 'parameters', 'subscribers',
                             'publishers', 'output_receivers', 'scope'}:
            raise ValueError('closed public controller snapshot required')
    if timestamp(snapshots[0]['stamp']) >= timestamp(snapshots[1]['stamp']):
        raise ValueError('ordered controller boundary stamps required')
    result = copy.deepcopy(packet)
    source = result['source_context']
    source['controller_runtime_observations'] = ([] if condition == 'diagnostic_removal'
                                                  else copy.deepcopy(snapshots))
    source['controller_source_scope'] = (
        'Static public configuration licenses source-qualified priority rules. '
        'Any supplied runtime snapshots are observed parameter-service and ROS-graph '
        'evidence only at their explicit native simulated-clock stamps. '
        'Absent or masked snapshots remain unknown. Two matching boundary snapshots '
        'do not prove continuous wiring or absence of intervening changes. '
        'Neither configuration nor graph alone proves message delivery, applied '
        'torque, physical arrival, or a unique physical cause.')
    return result
