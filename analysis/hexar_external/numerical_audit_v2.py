#!/usr/bin/env python3
"""Independent packet-only numerical candidates; no semantic gold override."""
import argparse,json,re
from audit_release import ROOT,sha,write
from study_v2 import V2

def recovered_ns(s):
 sec,frac=s.split('.');return int(sec)*10**9+int(frac)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);a=ap.parse_args();out=V2/a.cohort/'annotation'
 bank={x['response_id']:x for x in json.loads((out/'blind_bank.json').read_text())['items']};inv=json.loads((out/'atomic_inventory.json').read_text());rows=[]
 for item in inv['items']:
  packet=bank[item['response_id']]['robot_visible_evidence'];logs=packet['evidence']['navigation_logs'];last={};durations=[]
  for log in logs:
   if 'received a new goal' in log['message']:last[log['logger']]=log
   elif log['message']=='Skill completed successfully' and log['logger'] in last:
    start=last.pop(log['logger']);durations.append({'start':start['evidence_id'],'end':log['evidence_id'],'legacy_float_seconds':float(log['callback_time'])-float(start['callback_time']),'recovered_receipt_seconds':(recovered_ns(log['callback_time'])-recovered_ns(start['callback_time']))/1e9})
  window=packet['task_window'];candidates=[float(window[1])-float(window[0])]+[d[k] for d in durations for k in ('legacy_float_seconds','recovered_receipt_seconds')]
  for atom in item['atoms']:
   numbers=re.findall(r'(?<!\w)-?\d+(?:\.\d+)?',atom['statement'])
   if not numbers:continue
   seconds=[float(n) for n in re.findall(r'(\d+(?:\.\d+)?)\s*(?:-|\s)?(?:second|seconds)',atom['statement'])]
   rows.append({'response_id':item['response_id'],'item_id':atom['item_id'],'statement':atom['statement'],'numbers':numbers,'numeric_tokens_occur_in_permitted_packet':{n:any(n in json.dumps(e,ensure_ascii=False) for rows in packet['evidence'].values() for e in rows) for n in numbers},'claimed_seconds':seconds,'near_any_logged_or_window_duration_1sec':[any(abs(v-c)<=1 for c in candidates) for v in seconds],'task_window_legacy_seconds':candidates[0],'navigation_goal_to_completion_candidates':durations,'scope':'Arithmetic candidates only: selection/rounding/identity and causal-delay semantics still require qualified packet assessment. Neither encoded nor recovered receipt duration measures motion or its cause.'})
 write(out/'numerical_predicate_audit.json',{'schema':'hexar-packet-numerical-audit/v2','bank_sha256':sha(out/'blind_bank.json'),'rows':rows,'external_raw_evidence_used':False,'semantic_gold_overridden':False})
 print('NUMERIC_ATOMS_AUDITED',len(rows))
if __name__=='__main__':main()
