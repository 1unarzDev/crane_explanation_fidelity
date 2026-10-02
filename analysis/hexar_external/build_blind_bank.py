#!/usr/bin/env python3
"""Opaque export before atomic inventory; method key stays out of judge payloads."""
import hashlib
import json
import os
import random
import secrets
from audit_release import ROOT,sha,write

def main():
    out=ROOT/'data/hexar_external/annotation';out.mkdir(exist_ok=True)
    if (out/'blind_bank.json').exists():print('EXISTING_BLIND_BANK_REUSED');return
    packets={p['job_id']:p for p in json.loads((ROOT/'data/hexar_external/development/packets.json').read_text())['packets']}
    refs={p['job_id']:p for p in json.loads((ROOT/'data/hexar_external/development/independent_references.json').read_text())['references']}
    records=[json.loads(p.read_text()) for p in (ROOT/'data/hexar_external/development/responses').glob('*.json')]
    if len(records)!=27 or any(p['status']!='VALID' for p in records):raise ValueError('Incomplete development batch; no silent semantic omission')
    random.SystemRandom().shuffle(records);items=[];key=[]
    for r in records:
        rid=secrets.token_hex(8);base=r['job_id'].rsplit('-HX-',1)[0];p=packets[base];ref=refs[base]
        item={'response_id':rid,'response_text':r['answer'],'question_text':p['method_packet']['question'],
              'robot_visible_evidence':p['method_packet'],'independent_reference':{k:v for k,v in ref.items() if k not in ('job_id','condition','method_packet_sha256')},
              'sanitized_physical_facts':[],'physical_truth_status':'No mechanism truth supplied; do not infer from familiarity.'}
        items.append(item);key.append({'response_id':rid,'job_id':r['job_id'],'method':r['method'],'recording_id':r['recording_id'],'condition':r['condition'],'question_id':r['question_id']})
    write(out/'blind_bank.json',{'schema':'hexar-blinded-answer-bank/v1','items':items,'method_key_exported':False})
    write(out/'join_key.evaluator-only.json',{'schema':'hexar-evaluator-only-join-key/v1','key':key})
    write(out/'bank_manifest.json',{'blind_bank_sha256':sha(out/'blind_bank.json'),'responses':27,
        'key_sha256':sha(out/'join_key.evaluator-only.json'),'reference_source_sha256':sha(ROOT/'data/hexar_external/development/independent_references.json'),
        'atomization_route':'independent method-blind developer inventory; not a qualified model atomizer',
        'identity_limitation':'Template wording may reveal method style; opaque IDs do not guarantee method blindness.'})
    print('BLIND_BANK_BUILT')
if __name__=='__main__':main()
