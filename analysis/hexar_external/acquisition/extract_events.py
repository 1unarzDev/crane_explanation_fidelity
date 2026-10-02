"""Native, deterministic extraction of the historical HEXAR interface from new bags.

No family/intervention/seed metadata is read. No diagnostics are invented. It is
usable on development bags now; confirmation release requires the study gate.
"""
import argparse
import json
from pathlib import Path

VISIBLE_TOPICS = {'/rosout', '/amcl_pose', '/joy_priority', '/power/is_charging', '/task_info'}

def extract(bag: Path):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(bag), storage_id='sqlite3'), rosbag2_py.ConverterOptions('', ''))
    types = {topic.name: get_message(topic.type) for topic in reader.get_all_topics_and_types() if topic.name in VISIBLE_TOPICS}
    events = []
    while reader.has_next():
        topic, blob, timestamp = reader.read_next()
        if topic not in VISIBLE_TOPICS:
            continue
        msg = deserialize_message(blob, types[topic])
        if topic == '/rosout':
            value = {'name': msg.name, 'msg': msg.msg, 'level': msg.level, 'stamp': {'sec': msg.stamp.sec, 'nanosec': msg.stamp.nanosec}}
        elif topic == '/amcl_pose':
            value = {'covariance': list(msg.pose.covariance)}
        else:
            value = {'data': msg.data}
        events.append({'event_id': f'raw-{len(events):08d}', 'topic': topic, 'recorded_ns': timestamp, 'value': value})
    return events

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--bag', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--phase', choices=('development',), required=True)
    args = ap.parse_args()
    # The executable currently refuses any confirmatory release.
    events = extract(args.bag)
    with args.output.open('x') as stream:
        json.dump(events, stream, indent=2)
        stream.write('\n')
