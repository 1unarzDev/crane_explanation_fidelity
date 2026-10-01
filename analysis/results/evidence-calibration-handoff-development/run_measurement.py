#!/usr/bin/env python3
"""Small development-only full-answer annotation runner using the existing CLI transport."""
import argparse,hashlib,json,subprocess,sys,random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_support_execution import call_once,VALID
HERE=Path(__file__).resolve().parent

def validate(returned,cases,schema):
    if set(returned)!={"annotations"}:raise ValueError("expected annotations only")
    rows={r['case_id']:r for r in returned['annotations']}
    if len(rows)!=len(cases) or set(rows)!={c['case_id'] for c in cases}:raise ValueError('missing/duplicate case IDs')
    for c in cases:
        r=rows[c['case_id']];text=c['response_text']
        if r['primary_failure']!=bool(r['primary_violations']):raise ValueError('failure/count inconsistency')
        units={u['unit_id']:u for u in r['required_units']}
        if len(units)!=len(c['reference']['required_units']) or set(units)!=set(c['reference']['required_units']):raise ValueError('unit IDs mismatch')
        for u in units.values():
            if u['communicated'] and (not u['quote'] or u['quote'] not in text):raise ValueError('communicated unit lacks exact span')
            if not u['communicated'] and u['quote'] is not None:raise ValueError('uncommunicated unit quote must be null')
        for v in r['primary_violations']+r['factual_numeric_errors']:
            if not v['quote'] or v['quote'] not in text:raise ValueError('violation/error span not exact')

def execute(cases,output,slot,batch_size,workers,source_assets=None,prompt_path=None,group_by_episode=False,scope='DEVELOPMENT_ONLY',timeout_seconds=600,reasoning_effort="high",preserve_episode_order=False):
    prompt=(prompt_path or HERE/'annotation-prompt-v1.md').read_text();schema=json.loads((HERE/'annotation-schema-v1.json').read_text())
    config={'candidate':{'model':'gpt-6-astra','reasoning_effort':reasoning_effort,'transport':'codex-cli-chatgpt-login-ephemeral/v1'},'timeout_s':timeout_seconds}
    stamp=hashlib.sha256(json.dumps({'prompt':prompt,'schema':schema,'config':config},sort_keys=True).encode()).hexdigest()
    version=subprocess.run(['codex','--version'],capture_output=True,text=True,check=True).stdout.strip()
    if group_by_episode:
        groups={}
        for case in cases:
            identity=case['reference']['robot_visible_evidence']['configuration_id']
            groups.setdefault(identity,[]).append(case)
        rng=random.Random('episode-scoring-v1-'+slot)
        batches=list(groups.values())
        if not preserve_episode_order:
            for batch in batches:rng.shuffle(batch)
        tasks=[(i*batch_size,batch) for i,batch in enumerate(batches)]
    else:
        tasks=[(i,cases[i:i+batch_size]) for i in range(0,len(cases),batch_size)]
    output.mkdir(parents=True,exist_ok=True)
    def run(task):
        i,batch=task
        payload={'scope':scope,'independent_annotation_pass':slot,'shared_exact_source_assets':source_assets or [],'cases':[{k:v for k,v in c.items() if k!='expected'} for c in batch]}
        path=output/f'{slot}-batch-{i//batch_size:03d}.json'
        (output/f'{slot}-batch-{i//batch_size:03d}.request.json').write_text(json.dumps(payload,indent=2)+'\n')
        rec=call_once(output=path,payload=payload,schema=schema,prompt=prompt,freeze=config,freeze_sha256=stamp,cli_version=version,validate=lambda x:validate(x,batch,schema))
        print(slot,i,rec['status'],flush=True)
        return rec
    with ThreadPoolExecutor(max_workers=workers) as pool:records=list(pool.map(run,tasks))
    return records

def qualify():
    cases=json.loads((HERE/'measurement-suite-v1.json').read_text())['cases']
    out=HERE/'qualification-v1';records=[]
    for slot in ['A','B']:records+=execute(cases,out,slot,12,2)
    summary={'scope':'DEVELOPMENT_ONLY_SYNTHETIC','case_count':len(cases),'human_validation_claimed':False,'passes':{},'technical_failures':sum(r['status']!=VALID for r in records)}
    for slot in ['A','B']:
        annotations=[a for p in sorted(out.glob(f'{slot}-batch-*.json')) if not p.name.endswith('.request.json') for a in json.loads(p.read_text()).get('parsed_final',{}).get('annotations',[])]
        rows={a['case_id']:a for a in annotations};errors=[]
        for c in cases:
            e=c['expected'];r=rows.get(c['case_id'])
            if r is None:errors.append({'case_id':c['case_id'],'field':'missing'});continue
            vals={'primary_failure':r['primary_failure'],'communicated_unit_ids':[u['unit_id'] for u in r['required_units'] if u['communicated']],'factual_numeric_error':bool(r['factual_numeric_errors'])}
            for field,value in vals.items():
                want=e[field]
                if (set(value)!=set(want) if isinstance(value,list) else value!=want):errors.append({'case_id':c['case_id'],'field':field,'expected':want,'observed':value})
        summary['passes'][slot]={'annotated':len(rows),'errors':errors,'primary_failure_correct':sum(c['case_id'] in rows and rows[c['case_id']]['primary_failure']==c['expected']['primary_failure'] for c in cases),'unit_count':sum(len(c['reference']['required_units']) for c in cases),'unit_correct':sum(u['communicated']==(u['unit_id'] in c['expected']['communicated_unit_ids']) for c in cases if c['case_id'] in rows for u in rows[c['case_id']]['required_units'])}
    summary['status']='PASS_TARGETED_DEVELOPMENT' if not summary['technical_failures'] and all(not v['errors'] for v in summary['passes'].values()) else 'DEVELOPMENT_DISAGREEMENTS_RETAINED'
    (HERE/'qualification-summary-v1.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--qualify',action='store_true');ap.add_argument('--cases',type=Path);ap.add_argument('--output',type=Path);ap.add_argument('--slot',default='A');ap.add_argument('--batch-size',type=int,default=4);ap.add_argument('--workers',type=int,default=2);ap.add_argument('--prompt',type=Path);ap.add_argument('--group-by-episode',action='store_true');ap.add_argument('--preserve-episode-order',action='store_true');ap.add_argument('--timeout-seconds',type=float,default=600);ap.add_argument('--reasoning-effort',choices=['low','medium','high','xhigh'],default='high');ap.add_argument('--scope',choices=['DEVELOPMENT_ONLY','CONFIRMATION','REPLICATION'],default='DEVELOPMENT_ONLY');a=ap.parse_args()
    if a.qualify:qualify()
    else:
        data=json.loads(a.cases.read_text())
        execute(data['cases'],a.output,a.slot,a.batch_size,a.workers,data.get('source_assets'),a.prompt,a.group_by_episode,a.scope,a.timeout_seconds,a.reasoning_effort,a.preserve_episode_order)
