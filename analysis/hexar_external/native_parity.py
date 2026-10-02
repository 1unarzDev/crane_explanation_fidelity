#!/usr/bin/env python3
"""ROS Humble 1x DDS replay with original callbacks and traced receipt clock.

No model call, selector call, action service, robot control topic or external network.
Paired offline replay uses the exact observed receipt times/order for parity.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import rclpy
from rclpy.node import Node
from rclpy.serialization import deserialize_message
from rclpy.qos import QoSProfile,ReliabilityPolicy,DurabilityPolicy
from rcl_interfaces.msg import Log
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String,Bool
from replay import ROOT,Clock,objects,CALLBACKS,snapshot,replay

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bag',default='bagfile_6_1.bag');a=ap.parse_args()
    events=json.loads((ROOT/'data/hexar_external/extracted'/a.bag.replace('.bag','.json')).read_text())['events']
    raw={}
    for p in (ROOT/'data/hexar_external/upstream/bagfiles'/a.bag).glob('*.db3'):
        con=sqlite3.connect(f'file:{p}?mode=ro&immutable=1',uri=True)
        raw.update({mid:data for mid,data in con.execute('select id,data from messages')});con.close()
    types={'/rosout':Log,'/task_info':String,'/joy_priority':Bool,'/power/is_charging':Bool,'/amcl_pose':PoseWithCovarianceStamped}
    rclpy.init();nav,skill=objects(True)
    clock=Clock();nav.get_clock=lambda:clock;skill.get_clock=lambda:clock
    sender=Node('hexar_external_replayer',enable_rosout=False)
    receiver=Node('hexar_external_receiver',enable_rosout=False)
    qos=QoSProfile(depth=10,reliability=ReliabilityPolicy.RELIABLE,durability=DurabilityPolicy.VOLATILE)
    current={};trace=[];decoded_mismatches=[]
    def callback(topic,msg):
        e=current['event']; clock.ns=time.time_ns()
        obj=skill if topic=='/task_info' else nav
        getattr(obj,CALLBACKS[topic])(msg)
        trace.append({**e,'recorded_ns':clock.ns})
        # Compare actual ROS deserialization against rosbags extraction.
        v=e['value']
        if topic=='/amcl_pose':found={'covariance':list(msg.pose.covariance)}
        elif topic=='/rosout':found={'name':msg.name,'msg':msg.msg,'level':msg.level,'stamp':{'sec':msg.stamp.sec,'nanosec':msg.stamp.nanosec}}
        else:found={'data':msg.data}
        if found!=v:decoded_mismatches.append(e['event_id'])
    pubs={t:sender.create_publisher(typ,'/hexar_external/input'+t,qos) for t,typ in types.items()}
    subs=[receiver.create_subscription(typ,'/hexar_external/input'+t,lambda m,t=t:callback(t,m),qos) for t,typ in types.items()]
    for _ in range(20):rclpy.spin_once(receiver,timeout_sec=.1)
    started=time.monotonic();base=events[0]['recorded_ns']
    for idx,e in enumerate(events):
        due=started+(e['recorded_ns']-base)/1e9
        if due>time.monotonic():time.sleep(due-time.monotonic())
        current['event']=e
        pubs[e['topic']].publish(deserialize_message(raw[e['sql_id']],types[e['topic']]))
        deadline=time.monotonic()+3
        while len(trace)<=idx and time.monotonic()<deadline:rclpy.spin_once(receiver,timeout_sec=.01)
        if len(trace)<=idx:raise RuntimeError(f'DDS delivery timeout {idx}')
        if idx and idx%1000==0:print(f'dispatched {idx}',flush=True)
    question="What happened?"
    native=snapshot(nav,skill,question);offline=replay(trace,question)
    result={'schema':'hexar-native-parity/v1','bag':a.bag,'rate':1.0,
       'events':len(trace),'native_serialization_mismatches':decoded_mismatches,
       'full_state_and_prompt_equal':native==offline,
       'native_snapshot':native,'offline_snapshot':offline,
       'elapsed_seconds':time.monotonic()-started,
       'scope':'native ROS DDS serialized input, upstream callbacks/task bookkeeping/window/prompt; component-level only',
       'instrumentation':'freeze and retain receipt clock at each callback entry; offline consumes identical receipt clock trace',
       'not_validated':['historical callback jitter','full lifecycle/action/selector replay','physical robot runtime provenance']}
    out=ROOT/'data/hexar_external/replay';out.mkdir(exist_ok=True)
    (out/'native-parity.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'native-dispatch-trace.json').write_text(json.dumps(trace)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('snapshot')},indent=2))
    sender.destroy_node();receiver.destroy_node();nav.destroy_node();rclpy.shutdown()
    if native!=offline or decoded_mismatches:raise SystemExit(1)
if __name__=='__main__':main()
