#!/usr/bin/env python3
"""Fresh infrastructure-validation calls on a fixed, all-family development slice.

No old response/label imports, no new physical episodes, no endpoint selection.
"""
import copy,json
from audit_release import ROOT,sha,write
from study_v2 import V2
V3=ROOT/'data/hexar_external/v3'
def main():
 source=json.loads((V2/'development/packets.json').read_text());refs=json.loads((V2/'development/references.json').read_text());account=json.loads((V2/'development/accounting.evaluator-only.json').read_text())
 # Select query position 1 in every declared family before any v3 calls; not known failures.
 packets=[];references=[]
 for p in source['packets']:
  if p['question_id']!='q1':continue
  out=copy.deepcopy(p);out['recording_id']='P'+p['recording_id'][1:];out['job_id']=out['recording_id']+p['job_id'][4:];packets.append(out)
  r=copy.deepcopy(next(r for r in refs['references'] if r['job_id']==p['job_id']));r.update(job_id=out['job_id'],recording_id=out['recording_id']);references.append(r)
 for r in account['records']:r['recording_id']='P'+r['recording_id'][1:]
 values={'packets.json':{'schema':'hexar-fresh-interface-development-packets/v3','cohort':'development','packets':packets},'references.json':{**{k:v for k,v in refs.items() if k not in ('references','independent_numerical_state_time_checks')},'references':references},'accounting.evaluator-only.json':account,'slice_declaration.json':{'scope':'prospective evaluator-interface validation; no physical sample increment','rule':'query position q1 for every one of six repetition-1 bags, all three masks, all three methods','generation':'fresh calls with new job IDs, no v2 response/cache/label reuse','n_recordings':6,'n_jobs':18,'n_method_outputs':54,'primary_heldout_endpoint':'unchanged original 3 queries x3 masks per recording','original_packet_source_sha256':sha(V2/'development/packets.json'),'original_reference_source_sha256':sha(V2/'development/references.json'),'selection_used_method_outcomes':False,'quality_retries':0,'technical_retries':0,'alpha_consumed':0}}
 for name,value in values.items():
  dest=V3/'development'/name
  if dest.exists():assert json.loads(dest.read_text())==value
  else:write(dest,value)
 print('FRESH_ALL_FAMILY_Q1_SLICE_FROZEN',len(packets))
if __name__=='__main__':main()
