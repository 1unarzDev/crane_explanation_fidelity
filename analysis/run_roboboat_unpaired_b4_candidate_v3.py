"""Prospectively fixed unpaired full-B4 development validation; no provider calls."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from prepare_roboboat_fair_inputs_v3 import verify, ROOT
from run_roboboat_population_responses_v1 import binding, checked
from roboboat_runtime_source_closure_v1 import source_closure


def prepare(snapshot,root,prior_root=None):
    snapshot,root=Path(snapshot).resolve(),Path(root).resolve();s=verify(snapshot)
    if root.exists():raise FileExistsError('fresh unpaired-candidate run namespace required')
    root.mkdir();d={'schema':'roboboat-unpaired-B4-candidate-declaration/v3','status':'DEVELOPMENT_ONLY_UNPAIRED_NO_ENDPOINT_SCORING','input_snapshot':binding(snapshot),'entries':s['entries'],'root':str(root),'sources':[binding(p) for p in source_closure([Path(__file__)])],'B4':'full shared CRANE development v3 candidate, default deterministic realization','candidate_override':None,'model_calls':0,'B2_calls':0,'timeout_s':60,'quality_retries':0,'stopping':'All fixed snapshot entries once; retain errors; no outcome-dependent stopping or source changes during this declaration. No promotion or superiority inference.','confirmation_n':0,'replication_n':0,'independent_n_added':0}
    d['reuse']={}
    if prior_root is not None:
        prior_root=Path(prior_root).resolve();pd=json.loads((prior_root/'declaration.json').read_text())
        pt=json.loads((prior_root/'terminal.json').read_text());checked(pt['declaration'])
        if pt.get('endpoint_scores_released')is not False or pt.get('candidate_promoted')is not False:
            raise ValueError('prior run must remain unjudged and unpromoted')
        if any(pt.get(k)!=0 for k in ('B2_calls','model_calls','judge_calls')):
            raise ValueError('prior zero-model unpaired execution required')
        for source in pd['sources']:checked(source)
        old=verify(checked(pd['input_snapshot']))
        private=lambda value:{r['relative_path']:r['original']['sha256'] for r in value['private_B4_sources']}
        if private(old)!=private(s) or pd['candidate_override']is not None or pd['B4']!=d['B4']:
            raise ValueError('prior candidate sources/settings differ')
        old_entries={(e['row_id'],e['level']):e for e in old['entries']}
        old_results={(r['row_id'],r['level']):r for r in pt['results']}
        if len(old_results)!=len(pt['results']) or set(old_results)!=set(old_entries):
            raise ValueError('prior fixed outcome denominator incomplete')
        for entry in d['entries']:
            key=(entry['row_id'],entry['level']);former=old_entries.get(key)
            if former and former['common_file_hash_signature']==entry['common_file_hash_signature']:
                identifier=entry['row_id']+f"-L{entry['level']}"
                terminal=prior_root/'conditions'/identifier/'terminal.json'
                if json.loads(terminal.read_text())!=old_results[key]:raise ValueError('prior terminal mismatch')
                d['reuse'][identifier]=binding(terminal)
        d['prior_run']=binding(prior_root/'terminal.json')
    d['stopping']='Fixed all snapshot conditions; reuse every source/input-matched prior outcome including failures; execute only unmatched conditions once. No retries, scores or promotion.'
    (root/'declaration.json').write_text(json.dumps(d,indent=2)+'\n');return d


def execute(root):
    root=Path(root).resolve();dp=root/'declaration.json';d=json.loads(dp.read_text())
    if d['status']!='DEVELOPMENT_ONLY_UNPAIRED_NO_ENDPOINT_SCORING' or d['root']!=str(root):raise ValueError('unpaired development declaration required')
    for item in d['sources']:checked(item)
    if 'prior_run' in d:checked(d['prior_run'])
    s=verify(checked(d['input_snapshot']))
    if d['entries']!=s['entries']:raise ValueError('fixed candidate condition schedule changed')
    intent=root/'run-intent.json'
    if intent.exists():raise FileExistsError('prior candidate intent retained; no reissue')
    intent.write_text(json.dumps({'declaration':binding(dp),'conditions':len(d['entries'])},indent=2)+'\n');results=[]
    for e in d['entries']:
        work=Path(e['B4_private_workspace']);identifier=e['row_id']+f"-L{e['level']}";out=root/'conditions'/identifier;out.mkdir(parents=True,exist_ok=False)
        record={'row_id':e['row_id'],'cluster_id':e['cluster_id'],'level':e['level'],'status':'TECHNICAL_CANDIDATE_FAILURE','common_input_signature':e['common_file_hash_signature'],'input_snapshot':d['input_snapshot'],'declaration':binding(dp),'model_calls':0,'endpoint_score':None}
        if identifier in d['reuse']:
            prior=json.loads(checked(d['reuse'][identifier]).read_text())
            if (prior['row_id'],prior['level'])!=(e['row_id'],e['level']) or prior['common_input_signature']!=e['common_file_hash_signature']:
                raise ValueError('bound reused outcome identity mismatch')
            record.update(status=prior['status'],reused_prior_terminal=d['reuse'][identifier],execution_performed=False)
            if prior['status']=='CANDIDATE_GENERATED_UNPAIRED_UNJUDGED':
                for field,name in (('full_pipeline','full-pipeline.json'),('answer','B4.json')):
                    (out/name).write_bytes(checked(prior[field]).read_bytes());record[field]=binding(out/name)
            else:
                record['error_type']=prior.get('error_type');record['error']=prior.get('error')
            (out/'terminal.json').write_text(json.dumps(record,indent=2)+'\n');results.append(record);continue
        record['execution_performed']=True
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
    terminal={'schema':'roboboat-unpaired-B4-candidate-result/v3','status':'FIXED_UNPAIRED_DEVELOPMENT_BATCH_FINISHED','declaration':binding(dp),'conditions':len(results),'successful_generations':sum(r['status']=='CANDIDATE_GENERATED_UNPAIRED_UNJUDGED' for r in results),'new_executions':sum(r['execution_performed'] for r in results),'reused_outcomes':sum(not r['execution_performed'] for r in results),'results':results,'B2_calls':0,'model_calls':0,'judge_calls':0,'endpoint_scores_released':False,'candidate_promoted':False,'confirmation_n':0,'replication_n':0,'independent_n_added':0}
    (root/'terminal.json').write_text(json.dumps(terminal,indent=2)+'\n');return terminal

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','execute']);p.add_argument('--snapshot');p.add_argument('--prior-root');p.add_argument('--root',required=True);a=p.parse_args();d=prepare(a.snapshot,a.root,a.prior_root) if a.phase=='prepare' else execute(a.root);print(json.dumps({k:d[k] for k in ('status','conditions','successful_generations') if k in d}))
