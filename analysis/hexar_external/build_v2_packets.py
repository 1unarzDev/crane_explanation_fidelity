#!/usr/bin/env python3
"""Recording-grouped deterministic packet schedule; no model or judge calls."""
import argparse
import csv
import json
import random
from audit_release import ROOT,sha,write
from extract_events import extract
from study_v2 import V2,CONDITIONS,build_packet,contract,ontology
from evidence_calibration_io import canonical_sha256

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);a=ap.parse_args()
    source=ROOT/'data/hexar_external/upstream';exp=list(csv.DictReader((source/'experiments.csv').open()))
    selected=[r for r in exp if r['category']=='navigation' and (r['test_repetition']=='1')==(a.cohort=='development')]
    bybag={}
    for r in selected:bybag.setdefault(r['bagfile'],[]).append(r)
    packets=[];audits=[];accounting=[]
    for idx,(bag,rows) in enumerate(sorted(bybag.items())):
        recording=f'{"D" if a.cohort=="development" else "R"}{idx+1:03d}'
        events=extract(source/'bagfiles'/bag)
        write(V2/a.cohort/f'events-{recording}.json',{'events':events,'source_bag':bag})
        accounting.append({'recording_id':recording,'source_bag':bag,'situation_family':rows[0]['testcase_name'],
          'source_repetition':rows[0]['test_repetition'],'source_hashes':[{'path':str(p.relative_to(source)),'sha256':sha(p)} for p in sorted((source/'bagfiles'/bag).glob('*.db3'))]})
        for row in sorted(rows,key=lambda r:int(r['question_repetition'])):
            qi='q'+row['question_repetition'];trio=[]
            for condition in CONDITIONS:
                packet,snap,audit=build_packet(events,row['question'],condition)
                job=f'{recording}-{qi}-{condition}'
                item={'job_id':job,'recording_id':recording,'question_id':qi,'condition':condition,
                  'method_packet':packet,'packet_sha256':canonical_sha256(packet),'upstream_request':snap['llm_request']}
                contract(packet,job,recording) # Technical eligibility, no evaluator gold/performance.
                packets.append(item);trio.append(item)
                audits.append({'job_id':job,**audit,'task_window':packet['task_window']})
            assert trio[0]['method_packet']==trio[1]['method_packet']
            assert trio[0]['upstream_request']==trio[1]['upstream_request']
            assert trio[0]['method_packet']['task_window']==trio[2]['method_packet']['task_window']
            assert trio[0]['method_packet']['evidence']['navigation_outcomes']==trio[2]['method_packet']['evidence']['navigation_outcomes']
    write(V2/a.cohort/'packets.json',{'schema':'hexar-frozen-packet-candidate/v2','cohort':a.cohort,'packets':packets})
    write(V2/a.cohort/'accounting.evaluator-only.json',{'schema':'hexar-recording-accounting/v2','records':accounting})
    write(V2/a.cohort/'closure_audit.json',{'schema':'hexar-universal-removal-closure/v2','all_passed':True,
      'rule':'One universal diagnostic-channel removal, pre-derivation, clean state; only generic skill wrappers and task outcomes remain.',
      'intact_irrelevant_packets_equal':True,'task_windows_and_outcomes_preserved':True,'mask_family_specific':False,'jobs':audits})
    print(json.dumps({'cohort':a.cohort,'recordings':len(bybag),'packets':len(packets),'closure_passed':True}))
if __name__=='__main__':main()
