"""Prospectively fixed unpaired full-B4 development validation; no provider calls."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from prepare_roboboat_fair_inputs_v2 import verify, ROOT
from run_roboboat_population_responses_v1 import binding, checked
from roboboat_runtime_source_closure_v1 import source_closure


def prepare(snapshot,root):
    snapshot,root=Path(snapshot).resolve(),Path(root).resolve();s=verify(snapshot)
    if root.exists():raise FileExistsError('fresh unpaired-candidate run namespace required')
    root.mkdir();d={'schema':'roboboat-unpaired-B4-candidate-declaration/v1','status':'DEVELOPMENT_ONLY_UNPAIRED_NO_ENDPOINT_SCORING','input_snapshot':binding(snapshot),'entries':s['entries'],'root':str(root),'sources':[binding(p) for p in source_closure([Path(__file__)])],'B4':'full shared CRANE development v3 candidate, default deterministic realization','candidate_override':None,'model_calls':0,'B2_calls':0,'timeout_s':60,'quality_retries':0,'stopping':'All fixed snapshot entries once; retain errors; no outcome-dependent stopping or source changes during this declaration. No promotion or superiority inference.','confirmation_n':0,'replication_n':0,'independent_n_added':0}
    (root/'declaration.json').write_text(json.dumps(d,indent=2)+'\n');return d


def execute(root):
    root=Path(root).resolve();dp=root/'declaration.json';d=json.loads(dp.read_text())
    if d['status']!='DEVELOPMENT_ONLY_UNPAIRED_NO_ENDPOINT_SCORING' or d['root']!=str(root):raise ValueError('unpaired development declaration required')
    for item in d['sources']:checked(item)
    s=verify(checked(d['input_snapshot']))
    if d['entries']!=s['entries']:raise ValueError('fixed candidate condition schedule changed')
    intent=root/'run-intent.json'
    if intent.exists():raise FileExistsError('prior candidate intent retained; no reissue')
    intent.write_text(json.dumps({'declaration':binding(dp),'conditions':len(d['entries'])},indent=2)+'\n');results=[]
    for e in d['entries']:
        work=Path(e['B4_private_workspace']);identifier=e['row_id']+f"-L{e['level']}";out=root/'conditions'/identifier;out.mkdir(parents=True,exist_ok=False)
        record={'row_id':e['row_id'],'cluster_id':e['cluster_id'],'level':e['level'],'status':'TECHNICAL_CANDIDATE_FAILURE','common_input_signature':e['common_file_hash_signature'],'input_snapshot':d['input_snapshot'],'declaration':binding(dp),'model_calls':0,'endpoint_score':None}
        with tempfile.TemporaryDirectory(prefix='boat-b4-unpaired-') as tmp:
            output=Path(tmp)/'full-pipeline.json';command=[sys.executable,'-B',str(work/'analysis/roboboat_full_crane_v3.py'),'--packet',str(work/'evidence.json'),'--output',str(output),'--configuration-id',e['cluster_id'],'--episode-id',e['row_id'],'--condition-id',identifier]
            try:
                call=subprocess.run(command,cwd=work,env={'PATH':os.environ.get('PATH','/usr/bin:/bin'),'PYTHONPATH':str(work/'analysis'),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=d['timeout_s'],check=False)
                (out/'process.json').write_text(json.dumps({'return_code':call.returncode,'stdout':call.stdout,'stderr':call.stderr,'command':command},indent=2)+'\n')
                if call.returncode!=0:raise ValueError('candidate process failed; retained process receipt')
                value=json.loads(output.read_text());answer=value['realization']['final_response']
                if value['schema']!='roboboat-full-crane/v3-development' or not isinstance(answer,str) or not answer.strip():raise ValueError('candidate full pipeline output malformed')
                (out/'full-pipeline.json').write_bytes(output.read_bytes());(out/'B4.json').write_text(json.dumps({'answer':answer,'model_calls':0,'development_candidate':True,'unpaired':True},indent=2)+'\n')
                record.update(status='CANDIDATE_GENERATED_UNPAIRED_UNJUDGED',full_pipeline=binding(out/'full-pipeline.json'),answer=binding(out/'B4.json'))
            except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:record['error_type']=type(error).__name__;record['error']=str(error)
        (out/'terminal.json').write_text(json.dumps(record,indent=2)+'\n');results.append(record)
    verify(checked(d['input_snapshot']))
    terminal={'schema':'roboboat-unpaired-B4-candidate-result/v1','status':'FIXED_UNPAIRED_DEVELOPMENT_BATCH_FINISHED','declaration':binding(dp),'conditions':len(results),'successful_generations':sum(r['status']=='CANDIDATE_GENERATED_UNPAIRED_UNJUDGED' for r in results),'results':results,'B2_calls':0,'model_calls':0,'judge_calls':0,'endpoint_scores_released':False,'candidate_promoted':False,'confirmation_n':0,'replication_n':0,'independent_n_added':0}
    (root/'terminal.json').write_text(json.dumps(terminal,indent=2)+'\n');return terminal

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','execute']);p.add_argument('--snapshot');p.add_argument('--root',required=True);a=p.parse_args();d=prepare(a.snapshot,a.root) if a.phase=='prepare' else execute(a.root);print(json.dumps({k:d[k] for k in ('status','conditions','successful_generations') if k in d}))
