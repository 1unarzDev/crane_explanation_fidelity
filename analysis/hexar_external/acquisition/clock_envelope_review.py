"""Native technical clock diagnostics; no eligibility or semantic decisions."""
import argparse
import json
from pathlib import Path
import sqlite3


def native(folder):
    import yaml
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    metadata = yaml.safe_load((folder / 'raw/metadata.yaml').read_text())['rosbag2_bagfile_information']
    decoded = {'/clock': [], '/mobile_base_controller/odom': [], '/hexar_acquisition/navigation_event': []}
    for name in metadata['relative_file_paths']:
        path = folder / 'raw' / name
        path.resolve().relative_to((folder / 'raw').resolve())
        connection = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
        try:
            topics = {uid: (topic, get_message(kind)) for uid, topic, kind in
                      connection.execute('SELECT id,name,type FROM topics') if topic in decoded}
            for uid, receipt, blob in connection.execute('SELECT topic_id,timestamp,data FROM messages ORDER BY id'):
                if uid not in topics:
                    continue
                topic, kind = topics[uid]
                message = deserialize_message(blob, kind)
                if topic == '/hexar_acquisition/navigation_event':
                    value = json.loads(message.data)
                    stamp = value['stamp']['sec'] * 10**9 + value['stamp']['nanosec']
                    event = value['event']
                else:
                    value = message.clock if topic == '/clock' else message.header.stamp
                    stamp = value.sec * 10**9 + value.nanosec
                    event = None
                decoded[topic].append(dict(receipt_ns=receipt, stamp_ns=stamp, event=event))
        finally:
            connection.close()
    clocks = decoded['/clock']
    odom = decoded['/mobile_base_controller/odom']
    boundaries = decoded['/hexar_acquisition/navigation_event']
    accepted = [row for row in boundaries if row['event'] == 'accepted']
    terminal = [row for row in boundaries if row['event'] in ('terminal_result', 'terminal_result_unavailable')]
    if not clocks or not odom or len(accepted) != 1 or len(terminal) != 1:
        raise ValueError('observed clock/odometry/action pair required')
    lo, hi = min(r['stamp_ns'] for r in clocks), max(r['stamp_ns'] for r in clocks)
    begin, end = accepted[0]['stamp_ns'], terminal[0]['stamp_ns']
    outside = [r for r in odom if not lo <= r['stamp_ns'] <= hi]
    task = [r for r in odom if begin <= r['stamp_ns'] <= end]
    return dict(episode_id=folder.name, clock_stamp_range_ns=[lo, hi],
        odometry_stamp_range_ns=[min(r['stamp_ns'] for r in odom), max(r['stamp_ns'] for r in odom)],
        observed_action_stamp_range_ns=[begin, end], outside_full_envelope=outside,
        task_window_odometry_n=len(task),
        task_window_odometry_outside_envelope_n=sum(not lo <= r['stamp_ns'] <= hi for r in task),
        action_boundaries_within_clock_envelope=lo <= begin < end <= hi,
        full_clock_final_row=clocks[-1], full_odometry_final_row=odom[-1],
        disposition='DIAGNOSTIC_ONLY_NO_ELIGIBILITY_CHANGE', method_or_judge_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(native(args.folder)))
