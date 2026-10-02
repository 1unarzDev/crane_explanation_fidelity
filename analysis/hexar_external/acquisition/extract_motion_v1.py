"""Pure native extraction of recorded motion/action channels; no private metadata.

Receipt timestamps remain receipt timestamps. Stamped ROS measurement timestamps
are retained separately; missing goals/status remain missing, never inferred.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

TOPICS = {
    '/mobile_base_controller/odom': 'nav_msgs/msg/Odometry',
    '/cmd_vel': 'geometry_msgs/msg/Twist',
    '/mobile_base_controller/cmd_vel_out': 'geometry_msgs/msg/TwistStamped',
    '/navigate_to_pose/_action/status': 'action_msgs/msg/GoalStatusArray',
    '/goal_pose': 'geometry_msgs/msg/PoseStamped',
    '/hexar_acquisition/navigation_goal': 'geometry_msgs/msg/PoseStamped',
}

def file_sha(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def xyz(v):
    values = {k: float(getattr(v,k)) for k in ('x','y','z')}
    if not all(math.isfinite(x) for x in values.values()):
        raise ValueError('nonfinite recorded motion value')
    return values

def stamp(t):
    return {'sec': int(t.sec), 'nanosec': int(t.nanosec)}

def pose(p):
    q = {k: float(getattr(p.orientation,k)) for k in ('x','y','z','w')}
    if not all(math.isfinite(x) for x in q.values()):
        raise ValueError('nonfinite recorded quaternion')
    return {'position':xyz(p.position),'orientation':q}

def normalize(topic,msg):
    if topic == '/mobile_base_controller/odom':
        return {'frame_id':msg.header.frame_id,'child_frame_id':msg.child_frame_id,'stamp':stamp(msg.header.stamp),
                **pose(msg.pose.pose), 'pose_covariance':[float(v) for v in msg.pose.covariance],
                'twist':{'linear':xyz(msg.twist.twist.linear),'angular':xyz(msg.twist.twist.angular)}}
    if topic in ('/cmd_vel','/mobile_base_controller/cmd_vel_out'):
        twist = msg.twist if topic.endswith('cmd_vel_out') else msg
        value = {'linear':xyz(twist.linear),'angular':xyz(twist.angular)}
        if hasattr(msg,'header'):
            value.update({'frame_id':msg.header.frame_id,'stamp':stamp(msg.header.stamp)})
        return value
    if topic.endswith('/_action/status'):
        return {'statuses':[{'goal_id_hex':bytes(s.goal_info.goal_id.uuid).hex(),
                             'goal_stamp':stamp(s.goal_info.stamp),'status':int(s.status)} for s in msg.status_list]}
    return {'frame_id':msg.header.frame_id,'stamp':stamp(msg.header.stamp),**pose(msg.pose)}

def extract(bag):
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message
    reader=rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(bag),storage_id='sqlite3'),rosbag2_py.ConverterOptions('',''))
    recorded={t.name:t.type for t in reader.get_all_topics_and_types()}
    for topic,expected in TOPICS.items():
        if topic in recorded and recorded[topic]!=expected:
            raise ValueError('Unexpected recorded motion message type: '+topic)
    types={t:get_message(v) for t,v in recorded.items() if t in TOPICS}
    events=[];counts={t:0 for t in TOPICS}; receipt={t:[] for t in TOPICS}; stamp_ns={t:[] for t in TOPICS}
    while reader.has_next():
        topic,blob,timestamp=reader.read_next()
        if topic not in TOPICS:continue
        value=normalize(topic,deserialize_message(blob,types[topic]))
        events.append({'event_id':f'motion-raw-{len(events):08d}','topic':topic,'recorded_ns':int(timestamp),'value':value})
        counts[topic]+=1;receipt[topic].append(int(timestamp))
        if 'stamp' in value:stamp_ns[topic].append(value['stamp']['sec']*10**9+value['stamp']['nanosec'])
    provenance={'schema':'hexar-native-motion-extraction-provenance/v1','phase':'development_only',
                'extractor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'bag_files':[{'file':p.name,'sha256':file_sha(p)} for p in sorted(bag.glob('*.db3'))],
                'bag_metadata_sha256':hashlib.sha256((bag/'metadata.yaml').read_bytes()).hexdigest(),
                'topic_provenance':{t:{'expected_type':v,'recorded_type':recorded.get(t),'messages':counts[t],
                    'availability':'present' if counts[t] else 'unavailable',
                    'receipt_ns_min':min(receipt[t]) if receipt[t] else None,'receipt_ns_max':max(receipt[t]) if receipt[t] else None,
                    'measurement_stamp_ns_min':min(stamp_ns[t]) if stamp_ns[t] else None,'measurement_stamp_ns_max':max(stamp_ns[t]) if stamp_ns[t] else None} for t,v in TOPICS.items()},
                'private_plan_family_seed_or_episode_report_read':False,'missing_goal_inferred':False,
                'numeric_validation':'all selected xyz/quaternion values finite; no rounding or winsorization',
                'limitations':['odometry is controller-estimated motion, not independent ground truth','cmd_vel_out is controller output command, not proof of applied wheel torque or displacement','unstamped input commands have bag receipt timestamps only','no wall/simulation clock conversion or TF frame transform is inferred','action status is software execution state, not proof of reaching a measured physical goal','goal_pose topic represents a published pose, not proof of accepted action goal; goal publication provenance must be preserved','no goal/status is fabricated when an action service was not recorded'],
                'model_or_judge_calls':0}
    return events,provenance

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--bag',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--provenance',type=Path,required=True);ap.add_argument('--phase',choices=('development',),required=True)
    args=ap.parse_args()
    if args.output.exists() or args.provenance.exists():raise SystemExit('Refusing prior artifact overwrite')
    events,provenance=extract(args.bag)
    provenance['normalized_events_sha256']=hashlib.sha256((json.dumps(events,indent=2)+'\n').encode()).hexdigest()
    with args.output.open('x') as f:json.dump(events,f,indent=2);f.write('\n')
    with args.provenance.open('x') as f:json.dump(provenance,f,indent=2);f.write('\n')
