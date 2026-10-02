"""Deterministic development intervention measurements from native robot streams."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message

ap = argparse.ArgumentParser()
ap.add_argument('--bag', type=Path, required=True)
ap.add_argument('--output', type=Path, required=True)
args = ap.parse_args()
reader = rosbag2_py.SequentialReader()
reader.open(rosbag2_py.StorageOptions(uri=str(args.bag), storage_id='sqlite3'), rosbag2_py.ConverterOptions('', ''))
types = {t.name: get_message(t.type) for t in reader.get_all_topics_and_types()}
pos = []
commands = {'/cmd_vel': [], '/mobile_base_controller/cmd_vel_out': []}
indicators = {'/joy_priority': [], '/power/is_charging': []}
high_covariance = 0
clock_samples = []
while reader.has_next():
    topic, blob, timestamp = reader.read_next()
    if topic not in ('/clock', '/mobile_base_controller/odom', '/amcl_pose', *commands, *indicators):
        continue
    msg = deserialize_message(blob, types[topic])
    if topic == '/clock':
        clock_samples.append(msg.clock.sec + msg.clock.nanosec / 1e9)
    elif topic == '/mobile_base_controller/odom':
        pos.append((msg.pose.pose.position.x, msg.pose.pose.position.y))
    elif topic == '/amcl_pose':
        cov = msg.pose.covariance
        high_covariance += (cov[0] + cov[7])/2 > .2 or cov[35] > .2
    elif topic in indicators:
        indicators[topic].append(bool(msg.data))
    else:
        # PAL cmd_vel_out may be TwistStamped; record its actual declared shape.
        twist = msg.twist if hasattr(msg, 'twist') else msg
        commands[topic].append(math.hypot(twist.linear.x, twist.linear.y) + abs(twist.angular.z))
report = {'schema': 'hexar-native-development-motion-audit/v1', 'phase': 'development_only',
          'first_recorded_simulation_clock_s': clock_samples[0] if clock_samples else None,
          'last_recorded_simulation_clock_s': clock_samples[-1] if clock_samples else None,
          'simulation_clock_monotone': all(a<=b for a,b in zip(clock_samples,clock_samples[1:])),
          'odom_messages': len(pos), 'trajectory_distance_m': sum(math.hypot(b[0]-a[0], b[1]-a[1]) for a,b in zip(pos,pos[1:])),
          'displacement_m': math.hypot(pos[-1][0]-pos[0][0],pos[-1][1]-pos[0][1]) if pos else None,
          'command_messages': {k: len(v) for k,v in commands.items()},
          'command_nonzero_messages': {k: sum(x > .001 for x in v) for k,v in commands.items()},
          'indicator_true_messages': {k: sum(v) for k,v in indicators.items()},
          'high_amcl_covariance_messages': int(high_covariance), 'audit_code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'semantic_method_outputs_used': False,
          'full_family_qualification': False}
with args.output.open('x') as stream:
    json.dump(report,stream,indent=2);stream.write('\n')
