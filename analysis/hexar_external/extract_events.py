#!/usr/bin/env python3
"""Extract only declared navigation inputs, read-only and recording-ordered."""
from dataclasses import asdict
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
from rosbags.typesys import Stores, get_typestore
from audit_release import ROOT, sha, write

TOPICS={'/rosout','/task_info','/joy_priority','/power/is_charging','/amcl_pose'}

def extract(folder):
    store=get_typestore(Stores.ROS2_HUMBLE)
    events=[]
    for path in sorted(folder.glob('*.db3')):
        con=sqlite3.connect(f'file:{path.resolve()}?mode=ro&immutable=1',uri=True)
        for mid,ns,topic,typ,data in con.execute('SELECT m.id,m.timestamp,t.name,t.type,m.data FROM messages m JOIN topics t ON t.id=m.topic_id ORDER BY m.timestamp,m.id'):
            if topic not in TOPICS: continue
            m=store.deserialize_cdr(data,typ)
            if topic=='/rosout': value={'name':m.name,'msg':m.msg,'level':int(m.level),'stamp':{'sec':int(m.stamp.sec),'nanosec':int(m.stamp.nanosec)}}
            elif topic=='/task_info': value={'data':m.data}
            elif topic=='/amcl_pose': value={'covariance':m.pose.covariance.tolist()}
            else: value={'data':bool(m.data)}
            events.append({'event_id':f'e{len(events):06d}','recorded_ns':ns,'topic':topic,'type':typ,
                           'value':value,'serialized_sha256':hashlib.sha256(data).hexdigest(),'sql_id':mid})
        con.close()
    return events

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bag',default='bagfile_6_1.bag');a=ap.parse_args()
    src=ROOT/'data/hexar_external/upstream/bagfiles'/a.bag
    events=extract(src)
    dest=ROOT/'data/hexar_external/extracted'/a.bag.replace('.bag','')
    write(dest.with_suffix('.json'),{'schema':'hexar-extracted-events/v1','source_bag':a.bag,
        'message_order':'recorded timestamp then sqlite id','events':events})
    print(json.dumps({'bag':a.bag,'events':len(events),'topics':{t:sum(e['topic']==t for e in events) for t in sorted(TOPICS)}}))
    for e in events:
        if e['topic']=='/task_info': print(json.dumps(e))
if __name__=='__main__':main()
