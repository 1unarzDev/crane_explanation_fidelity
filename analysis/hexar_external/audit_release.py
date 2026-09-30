#!/usr/bin/env python3
"""Read-only release audit; original labels are never rewritten."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[2]
CORE_PIN = '9a81db8'

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temp.replace(path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--upstream', type=Path, default=ROOT/'data/hexar_external/upstream')
    ap.add_argument('--output', type=Path, default=ROOT/'data/hexar_external/audit')
    a = ap.parse_args(); p=a.upstream; out=a.output
    rows=list(csv.DictReader((p/'detailed_results.csv').open()))
    exp=list(csv.DictReader((p/'experiments.csv').open()))
    keys=('testcase_id','test_repetition','question_repetition')
    methods=sorted({r['ablation'] for r in rows})
    expected={tuple(r[k] for k in keys) for r in exp}
    count=collections.Counter(tuple(r[k] for k in keys)+(r['ablation'],) for r in rows)
    issues=[]
    for metric in ('correctness','has_wrong_info','accuracy'):
        for r in rows:
            votes=[int(r[f'{metric}_{i}']) for i in (1,2,3)]
            if int(r[f'{metric}_majority']) != int(sum(votes)>=2):
                issues.append({'row':r['index'],'metric':metric,'votes':votes,'released':r[f'{metric}_majority']})
    def summarize(sub):
        return {'n':len(sub),'recordings':len({r['bagfile'] for r in sub}),
                **{m:{'positive':sum(int(r[m+'_majority']) for r in sub),
                       'rate':sum(int(r[m+'_majority']) for r in sub)/len(sub)}
                   for m in ('correctness','has_wrong_info','accuracy')},
                'missing_answers':sum(not r['generated_explanation'].strip() for r in sub)}
    summary={'schema':'hexar-historical-recalculation/v1','category':'A_RELEASED_HISTORICAL_LABELS',
             'total_rows':len(rows),'experiment_rows':len(exp),'methods':{},
             'duplicates':[{'key':k,'n':v} for k,v in count.items() if v>1],
             'majority_mismatches':issues,
             'per_rater_accuracy':{str(i):{m:sum(int(r[f'accuracy_{i}']) for r in rows if r['ablation']==m)/sum(r['ablation']==m for r in rows) for m in methods} for i in (1,2,3)},
             'accuracy_composition_mismatches':[],
             'missing_pairs':[]}
    for r in rows:
        for i in (1,2,3):
            if int(r[f'accuracy_{i}']) != (int(r[f'correctness_{i}']) and not int(r[f'has_wrong_info_{i}'])):
                summary['accuracy_composition_mismatches'].append([r['index'],i])
    for m in methods:
        sub=[r for r in rows if r['ablation']==m]
        summary['methods'][m]={'all':summarize(sub),
            'by_module':{c:summarize([r for r in sub if r['category']==c]) for c in sorted({r['category'] for r in sub})},
            'by_situation':{c:summarize([r for r in sub if r['testcase_name']==c]) for c in sorted({r['testcase_name'] for r in sub})}}
        summary['missing_pairs'].extend({'method':m,'key':k} for k in sorted(expected-{tuple(r[k] for k in keys) for r in sub}))
    # Public fields are evaluator-only; this does not put them into method packets.
    lookup={tuple(r[k] for k in keys):r for r in exp}
    summary['experiment_correspondence_mismatches']=[]
    for r in rows:
        base=lookup.get(tuple(r[k] for k in keys))
        if base is None:
            summary['experiment_correspondence_mismatches'].append({'row':r['index'],'reason':'unknown experiment key'})
        else:
            for field in ('bagfile','question','category','testcase_name'):
                if base[field]!=r[field]:summary['experiment_correspondence_mismatches'].append({'row':r['index'],'field':field})
    summary['selected_components']={m:dict(collections.Counter(r['selected_component'] or 'NOT_RECORDED' for r in rows if r['ablation']==m)) for m in methods}
    write(out/'historical_results.json',summary)
    bags=sorted({r['bagfile'] for r in exp if r['category']=='navigation'})
    nav=[]
    for name in bags:
        folder=p/'bagfiles'/name
        meta=yaml.safe_load((folder/'metadata.yaml').read_text())['rosbag2_bagfile_information']
        declared={x['topic_metadata']['name']:x['message_count'] for x in meta['topics_with_message_count']}
        topics={};files=[]; timestamps=[]
        for db in sorted(folder.glob('*.db3')):
            conn=sqlite3.connect(f'file:{db.resolve()}?mode=ro&immutable=1',uri=True)
            for topic,typ,n in conn.execute('SELECT t.name,t.type,count(m.id) FROM topics t LEFT JOIN messages m ON m.topic_id=t.id GROUP BY t.id'):
                entry=topics.setdefault(topic,{'type':typ,'messages':0}); entry['messages']+=n
            timestamps.append(conn.execute('select min(timestamp),max(timestamp),count(*) from messages').fetchone())
            files.append({'path':str(db.relative_to(p)),'sha256':sha(db),'bytes':db.stat().st_size});conn.close()
        label=next(r for r in exp if r['bagfile']==name)
        nav.append({'bagfile':name,'situation':label['testcase_name'],'testcase_id':label['testcase_id'],
                    'execution':label['test_repetition'],'metadata_sha256':sha(folder/'metadata.yaml'),
                    'metadata_message_count':meta['message_count'],'sql_message_count':sum(x['messages'] for x in topics.values()),
                    'topics':topics,'files':files,'ranges':timestamps,
                    'metadata_count_mismatches':{k:[n,topics.get(k,{}).get('messages',0)] for k,n in declared.items() if n!=topics.get(k,{}).get('messages',0)},
                    'sql_only_topics':sorted(set(topics)-set(declared))})
    write(out/'navigation_inventory.json',{'schema':'hexar-navigation-inventory/v1','recordings':nav,
        'raw_scan_path_costmap_topics':[{'bagfile':b['bagfile'],'topics':[t for t in b['topics'] if any(x in t for x in ('scan','path','costmap'))]} for b in nav]})
    tracked=subprocess.check_output(['git','-C',str(p),'ls-files','-z']).decode().split('\0')
    manifest={'schema':'hexar-source-data-manifest/v1','repository':'https://github.com/fgebelli/HEXAR',
        'commit':subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD']).decode().strip(),
        'dirty':subprocess.check_output(['git','-C',str(p),'status','--porcelain']).decode(),
        'files':[{'path':f,'sha256':sha(p/f),'bytes':(p/f).stat().st_size} for f in tracked if f and (p/f).is_file()],
        'historical_model':{'tag':'phi4:latest','artifact_digest':None,'status':'NOT_RELEASED_DIGEST_NOT_RESOLVED','temperature':0},
        'code_license':'Package metadata declares Apache-2.0; see SOURCE_AUDIT.md.',
        'data_asset_license':'Not independently established; raw data not redistributed in this commit.',
        'crane_core_commit':subprocess.check_output(['git','rev-parse',CORE_PIN],cwd=ROOT).decode().strip(),
        'crane_core_hashes':{f:sha(ROOT/f) for f in ('analysis/evidence_calibration.py','analysis/evidence_calibration_io.py','analysis/maximal_supported_diagnosis.py','analysis/realize_evidence_calibrated_explanation.py')},
        'governance_hashes':{f:sha(ROOT/f) for f in ('docs/CURRENT_STATE_2026-09-30.md','docs/ARCHITECTURE.md','docs/EVIDENCE_CALIBRATION_PROTOCOL.md','manifests/study/evidence-calibration-agent-qualification-disposition-v1.json','manifests/study/diagnostic-sequential-error-ledger-v2.json')}}
    write(out/'source_data_manifest.json',manifest)
    split={'schema':'hexar-recording-split/v1','status':'DEVELOPMENT_DECLARATION_NOT_CONFIRMATORY_FREEZE',
        'rule':'execution repetition 1 development; repetitions 2 and 3 reserved before semantic tuning',
        'development':sorted(b for b in bags if '_1.bag' in b),
        'reserved':sorted(b for b in bags if '_1.bag' not in b),
        'inspected_development_ids':['bagfile_6_1.bag'],
        'reserved_semantic_outputs_inspected':False,'families_held_out':False}
    if not (out/'split.json').exists(): write(out/'split.json',split)
    print(json.dumps({'rows':len(rows),'navigation_recordings':len(nav),
       'all':{m:summary['methods'][m]['all'] for m in methods},
       'navigation':{m:summary['methods'][m]['by_module']['navigation'] for m in methods},
       'majority_mismatches':len(issues),'duplicates':len(summary['duplicates'])},indent=2))
if __name__=='__main__':main()
