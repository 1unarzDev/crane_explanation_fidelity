#!/usr/bin/env python3
"""Immutable bounded matched-model execution; no semantic retries."""
import argparse,json,os,random,sys,tempfile,time
from concurrent.futures import ThreadPoolExecutor
from audit_release import ROOT,sha,write
from study_v2 import V2,contract
from verify_v2 import qualified,study
sys.path.insert(0,str(ROOT/'analysis'))
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller
ANSWER={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);a=ap.parse_args()
 out=V2/a.cohort
 assert json.loads((V2/'qualification/qualification-result.json').read_text())['status']=='QUALIFIED'
 assert json.loads((ROOT/'data/hexar_external/replay/native-parity.json').read_text())['full_state_and_prompt_equal']
 qualified()
 if a.cohort=='reserved':study()
 temp=V2/'tmp';temp.mkdir(exist_ok=True);os.environ['TMPDIR']=str(temp);tempfile.tempdir=str(temp)
 caller=StructuredCodexCliAgentCaller(out/'model_cache',model='gpt-6-sol',effort='high',timeout_s=180)
 packets=json.loads((out/'packets.json').read_text())['packets'];calibration=(ROOT/'docs/hexar_external/prompt_calibration_v1.txt').read_text()
 declaration={'schema':'hexar-execution/v2','cohort':a.cohort,'methods':['HX-ORIGINAL','HX-PROMPT','HX-CONTRACT'],'model':'gpt-6-sol','effort':'high','weight_digest':None,'hosted_immutability':'unverified','historical_phi4_reproduction':False,'api':'ephemeral no-tool Codex CLI structured wrapper','contract':'deterministic realization replacement through pinned core; zero model calls','workers':2,'quality_retries':0,'technical_retries':0,'timeout_seconds':180,'alpha_allocated':0,'packets_sha256':sha(out/'packets.json'),'calibration_sha256':sha(ROOT/'docs/hexar_external/prompt_calibration_v1.txt'),'adapter_sha256':sha(ROOT/'analysis/hexar_external/study_v2.py'),'schedule_seed':260930}
 dest=out/'execution_declaration.json'
 if dest.exists():assert json.loads(dest.read_text())==declaration
 else:write(dest,declaration)
 jobs=[(p,m) for p in packets for m in declaration['methods']];random.Random(260930).shuffle(jobs)
 def run(item):
  p,m=item;job=p['job_id']+'-'+m;dest=out/'responses'/f'{job}.json'
  if dest.exists():return json.loads(dest.read_text())
  start=time.perf_counter();r={'schema':'hexar-response/v2','job_id':job,'method':m,'recording_id':p['recording_id'],'condition':p['condition'],'question_id':p['question_id'],'packet_sha256':p['packet_sha256']}
  try:
   if m=='HX-CONTRACT':
    c=contract(p['method_packet'],job,p['recording_id']);r.update(status='VALID',answer=c['answer'],contract_artifact=c,model_calls=0,template=True,fallback=False)
   else:
    if m=='HX-ORIGINAL':
     msgs=p['upstream_request']['messages'];prompt=msgs[0]['content'];payload={'user_message':msgs[1]['content']}
    else:prompt=calibration;payload=p['method_packet']
    call=caller.call(logical_role=job,payload=payload,schema=ANSWER,prompt=prompt)
    r.update(status='VALID',answer=call['parsed_final']['answer'],call_cache_key=call['cache_key'],latency_ms=call['latency_ms'],model_calls=1,template=False,fallback=False,cost_usd=None)
  except Exception as e:r.update(status='TECHNICAL_FAILURE',error=str(e),semantic_failure=None,retry=False)
  r['end_to_end_ms']=(time.perf_counter()-start)*1000;write(dest,r);print(job,r['status'],flush=True);return r
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(run,jobs))
 write(out/'run_summary.json',{'n_recordings':len({p['recording_id'] for p in packets}),'valid':sum(r['status']=='VALID' for r in results),'technical_failures':sum(r['status']!='VALID' for r in results),'alpha_consumed':0})
if __name__=='__main__':main()
