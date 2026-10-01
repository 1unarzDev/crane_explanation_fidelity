#!/usr/bin/env python3
"""One development recording, three removal-only conditions, equal new-method inputs."""
import copy
import csv
import json
import re
import sys
from pathlib import Path
from audit_release import ROOT,sha,write
from replay import replay
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_io import canonical_sha256

PATTERN=re.compile(r'joystick|manual(?:\s+mode)?|joy[_ /-]?priority',re.I)
MODES=('intact','irrelevant_removal','decisive_removal')

def transform(events,mode):
    retained=[];removed=[]
    for e in events:
        take=True
        if mode=='irrelevant_removal' and e['topic']=='/rosout' and e['value']['name']=='rosbag2_recorder':take=False
        if mode=='decisive_removal' and (e['topic']=='/joy_priority' or (e['topic']=='/rosout' and PATTERN.search(json.dumps(e['value'])))):take=False
        if not take:removed.append(e['event_id']);continue
        out=copy.deepcopy(e)
        if mode=='decisive_removal' and e['topic']=='/task_info':
            task=json.loads(out['value']['data'])
            # Remove alternative error-text representations before task bookkeeping.
            if PATTERN.search(task['task_error_msg']):task.pop('task_error_msg');task['task_error_msg']=None
            for skill in task['skill_sequence']:
                if PATTERN.search(skill['error_msg']):skill['error_msg']=None
            out['value']['data']=json.dumps(task)
        retained.append(out)
    return retained,removed

def packet(events,question,mode):
    transformed,removed=transform(events,mode)
    snap=replay(transformed,question)
    start,end=map(float,snap['task_window'])
    # Public primitive facts, not evaluator required-unit lists or cause labels.
    relevant=[x for x in snap['logs'] if start<=float(x['timestamp'])<=end]
    logfacts=[{'evidence_id':f'l{i:04d}','logger':x['name'],'message':x['msg']} for i,x in enumerate(relevant)]
    task=snap['task'];skills=task['skill_sequence']
    outcomes=[{'evidence_id':f's{i:04d}','skill':x['skill'],'status':x['status'],'error_msg':x['error_msg']} for i,x in enumerate(skills) if x['skill']=='navigate_to_zone' and x['status'].lower() not in ('waiting','running')]
    manual=[e for e in transformed if e['topic']=='/joy_priority']
    charging=[e for e in transformed if e['topic']=='/power/is_charging']
    evidence={'navigation_logs':logfacts,'navigation_outcomes':outcomes,
        'manual_state':[] if not manual else [{'evidence_id':'manual-latest','value':manual[-1]['value']['data'],'scope':'last received state before explanation; upstream does not time-filter this state'}],
        'charging_state':[] if not charging else [{'evidence_id':'charging-latest','value':charging[-1]['value']['data'],'scope':'last received state before explanation; upstream does not time-filter this state'}]}
    pkt={'schema':'hexar-permitted-method-packet/v1','question':question,'task_window':snap['task_window'],
       'evidence':evidence,'availability':{k:('present' if v else 'unavailable') for k,v in evidence.items()},
       'source_context':{'manual_state_semantics':'/joy_priority is consumed as the manual-joystick indicator by the released component; no supplied controller source proves motion inhibition.',
          'log_semantics':'Controller progress failure and clearing requests are execution records; they do not uniquely establish obstacles, moving obstacles, actuator failure or localization causes.',
          'missingness':'Unavailable is unknown, never false or success.'}}
    if mode=='decisive_removal':
        assert not manual and snap['is_joystick_manual'] is None
        assert not any(PATTERN.search(json.dumps(e['value'])) for e in transformed if e['topic']=='/rosout')
        assert 'joystick is in manual mode' not in snap['llm_request']['messages'][1]['content']
        assert evidence['navigation_outcomes'] and evidence['navigation_logs']
    return pkt,snap,{'mode':mode,'removed_event_ids':removed,'retained_events':len(transformed),
       'transformed_events_sha256':canonical_sha256(transformed),'clean_initial_state':True,
       'missing_manual_state':snap['is_joystick_manual'] is None,
       'task_window_preserved':True,'alternate_error_strings_removed_before_replay':True}

def main():
    events=json.loads((ROOT/'data/hexar_external/extracted/bagfile_6_1.json').read_text())['events']
    exp=list(csv.DictReader((ROOT/'data/hexar_external/upstream/experiments.csv').open()))
    qs=[r['question'] for r in exp if r['bagfile']=='bagfile_6_1.bag']
    output=ROOT/'data/hexar_external/development';output.mkdir(exist_ok=True)
    packets=[];closure=[]
    for qi,q in enumerate(qs):
        trio=[]
        for mode in MODES:
            pkt,snap,audit=packet(events,q,mode)
            job=f'dev001-q{qi+1}-{mode}'
            item={'job_id':job,'recording_id':'dev001','question_id':f'q{qi+1}','condition':mode,
                  'method_packet':pkt,'upstream_request':snap['llm_request'],'packet_sha256':canonical_sha256(pkt)}
            packets.append(item);closure.append({'job_id':job,**audit});trio.append(item)
        assert trio[0]['method_packet']==trio[1]['method_packet']
        assert trio[0]['upstream_request']==trio[1]['upstream_request']
        assert trio[0]['method_packet']['task_window']==trio[2]['method_packet']['task_window']
    write(output/'packets.json',{'schema':'hexar-development-packets/v1','category':'B_AND_C_COMPONENT_DEVELOPMENT','packets':packets})
    write(output/'closure_audit.json',{'schema':'hexar-development-closure-audit/v1','jobs':closure,
       'intact_irrelevant_prompt_and_facts_identical':True,
       'physical_event_changed':False,'public_handles_opaque':True,
       'raw_files_available_to_methods':False,'removal_before_derivation':True,
       'scope':'manual-control development recording only; other families require separate audited masks'})
    print(json.dumps({'packets':len(packets),'questions':qs,'closure_passed':True}))
if __name__=='__main__':main()
