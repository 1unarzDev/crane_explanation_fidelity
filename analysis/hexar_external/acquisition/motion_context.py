"""Development-only, recording-scoped motion summaries from visible messages.

No frame transforms, arrival decisions, causal labels or hidden plans are read.
Masking occurs before summaries. Receipt and measurement clocks stay separate.
"""
import copy
import math

ODOM = '/mobile_base_controller/odom'
COMMANDS = ('/cmd_vel', '/mobile_base_controller/cmd_vel_out')
GOALS = ('/goal_pose', '/hexar_acquisition/navigation_goal')
STATUS = '/navigate_to_pose/_action/status'
TOPICS = (ODOM, *COMMANDS, *GOALS, STATUS)


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError('finite numeric motion measurement required')
    return float(value)


def timestamp(value):
    sec, nano = value['sec'], value['nanosec']
    if type(sec) is not int or type(nano) is not int or not 0 <= nano < 10**9:
        raise ValueError('invalid measurement stamp')
    return sec * 10**9 + nano


def summarize(events, condition):
    if condition not in ('intact', 'irrelevant_removal', 'diagnostic_removal'):
        raise ValueError('unknown evidence condition')
    selected = [e for e in events if e['topic'] in TOPICS and
                not (condition == 'diagnostic_removal' and e['topic'] in (ODOM, *COMMANDS))]
    ids = [e['event_id'] for e in selected]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate raw motion evidence identity')
    result = {'odometry_observation': [], 'command_observation': [],
              'requested_goal': [], 'action_status_observation': []}
    for topic in TOPICS:
        rows = [e for e in selected if e['topic'] == topic]
        if not rows:
            continue
        receipts = [e['recorded_ns'] for e in rows]
        if any(type(t) is not int for t in receipts) or any(a > b for a, b in zip(receipts, receipts[1:])):
            raise ValueError('nonmonotone or invalid receipt clock')
        base = dict(evidence_id='motion-' + topic.strip('/').replace('/', '-'), topic=topic,
                    messages=len(rows), receipt_ns_first=receipts[0], receipt_ns_last=receipts[-1],
                    scope='all recorded samples of this channel; not an inferred accepted-task window')
        if topic == ODOM:
            frames = {(r['value']['frame_id'], r['value']['child_frame_id']) for r in rows}
            if len(frames) != 1 or not next(iter(frames))[0]:
                raise ValueError('one nonempty odometry frame required; no inferred transform')
            stamps = [timestamp(r['value']['stamp']) for r in rows]
            if any(a >= b for a, b in zip(stamps, stamps[1:])):
                raise ValueError('odometry measurement stamps must increase strictly')
            positions = [(finite(r['value']['position']['x']), finite(r['value']['position']['y'])) for r in rows]
            distance = math.fsum(math.dist(a, b) for a, b in zip(positions, positions[1:]))
            if not math.isfinite(distance):
                raise ValueError('nonfinite accumulated distance')
            base.update(frame_id=next(iter(frames))[0], child_frame_id=next(iter(frames))[1],
                        measurement_stamp_ns_first=stamps[0], measurement_stamp_ns_last=stamps[-1],
                        maximum_measurement_gap_ns=max((b-a for a,b in zip(stamps,stamps[1:])),default=None),
                        sampled_xy_path_distance_m=distance, sampled_xy_displacement_m=math.dist(positions[0],positions[-1]),
                        interpretation='controller odometry estimate; sampling gaps and rotation are not physical-goal measurements')
            result['odometry_observation'].append(base)
        elif topic in COMMANDS:
            linear = [math.hypot(*(finite(r['value']['linear'][axis]) for axis in ('x','y','z'))) for r in rows]
            angular = [math.hypot(*(finite(r['value']['angular'][axis]) for axis in ('x','y','z'))) for r in rows]
            if not all(math.isfinite(n) for n in (*linear,*angular)):
                raise ValueError('nonfinite command norm')
            base.update(exact_nonzero_samples=sum(l > 0 or a > 0 for l,a in zip(linear,angular)),
                        maximum_linear_norm_m_s=max(linear),maximum_angular_norm_rad_s=max(angular),
                        interpretation='recorded command vectors; not proof of applied torque or physical motion')
            result['command_observation'].append(base)
        else:
            # Explicit whitelist projection; ancillary private keys cannot pass.
            for row in rows:
                value = row['value']
                visible = ({'statuses': [{k:s[k] for k in ('goal_id_hex','goal_stamp','status')} for s in value['statuses']]}
                           if topic == STATUS else {k:value[k] for k in ('frame_id','stamp','position','orientation')})
                target = 'action_status_observation' if topic == STATUS else 'requested_goal'
                result[target].append(dict(evidence_id=row['event_id'],topic=topic,receipt_ns=row['recorded_ns'],value=copy.deepcopy(visible)))
    return result


def extend(packet, events, condition):
    result = copy.deepcopy(packet)
    measurements = summarize(events, condition)
    if any(key in result['evidence'] for key in measurements):
        raise ValueError('motion evidence already projected')
    result['evidence'].update(measurements)
    result['availability'].update({k:'present' if v else 'unavailable' for k,v in measurements.items()})
    result['source_context']['motion_window_scope'] = (
        'These summaries describe each channel over its recorded sample window. '
        'Receipt and measurement timestamps are separate clocks. No accepted-task '
        'window, clock conversion, TF transform or physical arrival is inferred. '
        'Command vectors are commands; odometry estimates motion. Missing channels '
        'and unobserved intervals remain unknown.')
    return result
