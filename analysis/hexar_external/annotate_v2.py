#!/usr/bin/env python3
"""Blind inventory/qualified support annotation; immutable outputs and no retries."""
import argparse,copy,hashlib,json,os,random,secrets,sys,tempfile
from concurrent.futures import ThreadPoolExecutor
from audit_release import ROOT,sha,write
from study_v2 import V2
from verify_v2 import qualified,study
from qualify_v2 import effective_prompt
sys.path.insert(0,str(ROOT/'analysis'))
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller,run
from evidence_calibration_io import canonical_sha256

def bank(cohort):
 out=V2/cohort/'annotation';dest=out/'blind_bank.json'
 if dest.exists():return
 packets={p['job_id']:p for p in json.loads((V2/cohort/'packets.json').read_text())['packets']}
 refs={p['job_id']:p for p in json.loads((V2/cohort/'references.json').read_text())['references']}
 records=[json.loads(p.read_text()) for p in (V2/cohort/'responses').glob('*.json')]
 assert len(records)==3*len(packets)
 random.SystemRandom().shuffle(records);items=[];key=[]
 for r in records:
  rid=secrets.token_hex(8);base=r['job_id'].rsplit('-HX-',1)[0];p=packets[base];ref=refs[base]
  key.append({'response_id':rid,**{k:r[k] for k in ('job_id','method','recording_id','condition','question_id','status')}})
  if r['status']!='VALID':continue
  items.append({'response_id':rid,'response_text':r['answer'],'question_text':p['method_packet']['question'],'robot_visible_evidence':p['method_packet'],'independent_reference':{k:v for k,v in ref.items() if k not in ('job_id','recording_id','condition','method_packet_sha256')},'sanitized_physical_facts':[]})
 write(dest,{'schema':'hexar-blinded-answer-bank/v2','items':items,'method_key_exported':False})
 write(out/'join_key.evaluator-only.json',{'key':key})
 print('BANK',len(items),flush=True)

def packets(cohort):
 out=V2/cohort/'annotation';items=json.loads((out/'blind_bank.json').read_text())['items']
 inventory={x['response_id']:x for x in json.loads((out/'atomic_inventory.json').read_text())['items']}
 assert set(inventory)=={x['response_id'] for x in items}
 for x in items:
  inv=inventory[x['response_id']];assert inv['response_text_sha256']==hashlib.sha256(x['response_text'].encode()).hexdigest()
  assert inv['atoms'] and all(a['response_span'] in x['response_text'] for a in inv['atoms'])
  ref=x['independent_reference'];units=[r['requirement'] for r in ref['required_communication_units']];limits=[r['requirement'] for r in ref['required_scope_limits']]
  forms=[]
  for slot in ('A','B'):
   forms.append({'form_id':x['response_id']+'-'+slot,'packet_id':x['response_id'],'annotator_slot':slot,'response_text':x['response_text'],'question_text':x['question_text'],'robot_visible_evidence':x['robot_visible_evidence'],'independent_reference':ref,'sanitized_physical_facts':[],
    'atomic_statements':[{**a,'label':None,'visible_support_references':[],'annotation_notes':None} for a in inv['atoms']],
    'allowed_claim_labels':['SUPPORTED_BY_VISIBLE_EVIDENCE','CONTRADICTED_BY_VISIBLE_EVIDENCE','INSUFFICIENT_VISIBLE_EVIDENCE','PHYSICALLY_TRUE_BUT_UNSUPPORTED','UNINTERPRETABLE'],
    'required_unit_coverage':[{'unit_prompt':u,'communicated':None,'response_span':None} for u in units],
    'limitation_preservation':[{'limitation_prompt':u,'preserved':None,'response_span':None} for u in limits],
    'abstraction_level_options':['task_outcome','software_action_failure','recorded_override_state','specific_physical_cause','limitation'],'highest_asserted_abstraction_level':None,'false_premise_handling':'NOT_APPLICABLE','annotator_attestation':None})
  value={'schema':'crane-blinded-agent-atomic-annotation-packet-set/v1','builder_id':'hexar-external-v2','builder_version':'v2','packet_count':1,'annotation_origin':'automated_agent','response_text':x['response_text'],'forms':forms}
  dest=out/'packets'/f"{x['response_id']}.json"
  if dest.exists():assert json.loads(dest.read_text())==value
  else:write(dest,value)
 print('ANNOTATION_PACKETS',len(items),flush=True)

class QualifiedCaller:
 def __init__(self,out):self.caller=StructuredCodexCliAgentCaller(out/'calls',model='gpt-6-astra',effort='high',timeout_s=240)
 def call(self,**kw):kw['prompt']=effective_prompt();return self.caller.call(**kw)

def annotate(cohort):
 qualified()
 if cohort=='reserved':study()
 out=V2/cohort/'annotation';tmp=V2/'tmp';tmp.mkdir(exist_ok=True);os.environ['TMPDIR']=str(tmp);tempfile.tempdir=str(tmp)
 assert json.loads((V2/'qualification/qualification-result.json').read_text())['status']=='QUALIFIED'
 jobs=sorted((out/'packets').glob('*.json'))
 def job(p):
  dest=out/'judgments'/p.stem;end=dest/'external-summary.json'
  if end.exists():return json.loads(end.read_text())
  try:
   r=run(p,dest,caller=QualifiedCaller(dest));r.update(status='EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED',external_qualification_sha256=sha(V2/'qualification/qualification-result.json'),amendment_sha256=sha(ROOT/'docs/hexar_external/v2/annotation_amendment.txt'),primary_confirmatory=False)
  except Exception as e:r={'status':'TECHNICAL_FAILURE','error':str(e),'endpoint_score':None,'retry':False}
  write(end,r);print(p.stem,r['status'],flush=True);return r
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(job,jobs))
 write(out/'annotation_summary.json',{'n_responses':len(jobs),'qualified_completed':sum(r['status']=='EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED' for r in results),'technical_failures':sum(r['status']=='TECHNICAL_FAILURE' for r in results),'alpha_consumed':0,'human_validated':False})

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);ap.add_argument('--stage',choices=['bank','packets','annotate'],required=True);a=ap.parse_args();{'bank':bank,'packets':packets,'annotate':annotate}[a.stage](a.cohort)
if __name__=='__main__':main()
