#!/usr/bin/env python3
"""Bounded no-retry matched-model component development, not confirmation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from audit_release import ROOT,sha,write
from contract_adapter import contract_answer
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_io import canonical_sha256
from run_evidence_calibration_agent_annotation import StructuredCodexCliAgentCaller

ANSWER={'type':'object','properties':{'answer':{'type':'string'}},'required':['answer'],'additionalProperties':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--canary-only',action='store_true');ap.add_argument('--workers',type=int,default=2);a=ap.parse_args()
    if not 1<=a.workers<=2:raise ValueError('Development queue capped at 2; larger quota requires coordination')
    out=ROOT/'data/hexar_external/development';tmp=ROOT/'data/hexar_external/tmp';tmp.mkdir(exist_ok=True)
    os.environ['TMPDIR']=str(tmp);tempfile.tempdir=str(tmp)
    caller=StructuredCodexCliAgentCaller(out/'model_cache',model='gpt-6-sol',effort='high',timeout_s=180)
    pre=json.loads((ROOT/'data/hexar_external/transport-preflight.json').read_text())
    if pre['status']!='READY_FOR_SCHEMA_CANARY':raise ValueError('Transport preflight is closed')
    canary=caller.call(logical_role='hexar-nonstudy-schema-canary-v2-request-repair',payload={'scope':'NON_STUDY_INFRASTRUCTURE'},schema=ANSWER,prompt='This is a non-study transport/schema check. Return the single word READY in the answer field. Do not use tools.')
    if canary['parsed_final']!={'answer':'READY'}:raise ValueError('Canary did not pass')
    write(out/'canary.json',canary)
    if a.canary_only:print('NON_STUDY_CANARY_PASSED');return
    parity=json.loads((ROOT/'data/hexar_external/replay/native-parity.json').read_text())
    if not parity['full_state_and_prompt_equal'] or parity['native_serialization_mismatches']:raise ValueError('Native parity failed')
    packets=json.loads((out/'packets.json').read_text())['packets']
    calibration=(ROOT/'docs/hexar_external/prompt_calibration_v1.txt').read_text()
    declaration={'schema':'hexar-first-development-execution/v1','status':'DEVELOPMENT_ONLY_NOT_CONFIRMATORY',
       'recordings':['dev001'],'n_independent_recordings':1,'methods':['HX-ORIGINAL','HX-PROMPT','HX-CONTRACT'],
       'model':'gpt-6-sol','reasoning_effort':'high','model_weight_digest':None,'hosted_backend_immutability':'unverified',
       'model_configuration_basis':'retained main B2 pilot v1, model-backed methods identical; declared fresh adaptation',
       'sampling_temperature':None,'api_adaptation':'Codex CLI structured answer wrapper, not historical chat-completions',
       'workers':a.workers,'quality_retries':0,'technical_retries':0,'timeout_seconds':180,
       'contract_realization':'deterministic replacement using pinned core, 0 model calls',
       'packets_sha256':sha(out/'packets.json'),'calibration_prompt_sha256':sha(ROOT/'docs/hexar_external/prompt_calibration_v1.txt'),
       'adapter_sha256':sha(ROOT/'analysis/hexar_external/contract_adapter.py'),
       'caller_sha256':sha(ROOT/'analysis/run_evidence_calibration_agent_annotation.py'),
       'external_annotation_qualified':False,'alpha_allocated':0,'primary_endpoint_scoring_authorized':False}
    declaration_file=out/'execution_declaration.json'
    if declaration_file.exists() and json.loads(declaration_file.read_text())!=declaration:raise ValueError('Existing execution declaration differs; immutable run must not be overwritten')
    write(declaration_file,declaration)
    jobs=[(x,m) for x in packets for m in declaration['methods']]
    def run(item):
        p,m=item; job=p['job_id']+'-'+m;dest=out/'responses'/f'{job}.json'
        if dest.exists():return json.loads(dest.read_text())
        start=time.perf_counter()
        try:
            if m=='HX-CONTRACT':
                c=contract_answer(p['method_packet'],job)
                record={'status':'VALID','answer':c['answer'],'contract_artifact':c,'model_calls':0,'template':True,'fallback':False}
            else:
                if m=='HX-ORIGINAL':
                    messages=p['upstream_request']['messages'];prompt=messages[0]['content'];payload={'user_message':messages[1]['content']}
                else:prompt=calibration;payload=p['method_packet']
                call=caller.call(logical_role=job,payload=payload,schema=ANSWER,prompt=prompt)
                record={'status':'VALID','answer':call['parsed_final']['answer'],'call_cache_key':call['cache_key'],
                     'call_record_sha256':canonical_sha256(call),'latency_ms':call['latency_ms'],
                     'model_calls':1,'template':False,'fallback':False,'cost_usd':None,'cost_status':'not reported'}
            record={'schema':'hexar-development-response/v1','job_id':job,'method':m,
                'recording_id':p['recording_id'],'question_id':p['question_id'],'condition':p['condition'],
                'packet_sha256':p['packet_sha256'],'end_to_end_ms':(time.perf_counter()-start)*1000,**record}
        except Exception as e:
            record={'schema':'hexar-development-response/v1','job_id':job,'method':m,
                'recording_id':p['recording_id'],'question_id':p['question_id'],'condition':p['condition'],
                'packet_sha256':p['packet_sha256'],'status':'TECHNICAL_FAILURE','error':str(e),
                'semantic_failure':None,'retry':False}
        write(dest,record);print(json.dumps({'job':job,'status':record['status'],'answer':record.get('answer')}),flush=True)
        return record
    with ThreadPoolExecutor(max_workers=a.workers) as pool:results=list(pool.map(run,jobs))
    write(out/'run_summary.json',{'schema':'hexar-development-execution-summary/v1','n_recordings':1,
       'valid':sum(x['status']=='VALID' for x in results),'technical_failures':sum(x['status']!='VALID' for x in results),
       'qualified_endpoint_score':None,'alpha_consumed':0,'response_files':[str((out/'responses'/f"{x['job_id']}.json").relative_to(ROOT)) for x in results]})
if __name__=='__main__':main()
