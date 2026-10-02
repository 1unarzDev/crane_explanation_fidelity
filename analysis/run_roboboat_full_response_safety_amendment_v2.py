#!/usr/bin/env python3
"""One-shot transport safety amendment, untouched registered requests only."""
import argparse,json
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import run_roboboat_full_population_responses_v2 as original
import roboboat_isolated_transport_v3 as safe


def binding(p):return original.binding(p)


def prepare(declaration_path,output_root,amendment_path):
    declaration_path,output_root,amendment_path=map(lambda x:Path(x).resolve(),(declaration_path,output_root,amendment_path))
    d=json.loads(declaration_path.read_text());original.verify(d,declaration_path)
    untouched=[];existing=[]
    for e in d['entries']:
        intent=output_root/'intents'/(e['id']+'.json'); terminal=output_root/'responses'/e['id']/'response-terminal.json'
        folder=terminal.parent
        if intent.exists() or folder.exists():
            if not terminal.exists():raise ValueError('unresolved prior request; preserve and disposition first')
            t=json.loads(terminal.read_text())
            if t['source_identity']!={'declaration_sha256':original.digest(declaration_path),'entry':e}:raise ValueError('prior identity mismatch')
            existing.append(binding(terminal))
        else:untouched.append(e['id'])
    value={'schema':'roboboat-full-response-transport-safety-amendment/v2','phase':'DEVELOPMENT_ONLY_BEFORE_UNTOUCHED_CALLS',
        'original_declaration':binding(declaration_path),'output_root':str(output_root),'runner':binding(__file__),
        'safe_transport':binding(safe.__file__),'original_isolation_transport':binding(Path(original.ROOT)/'analysis/roboboat_isolated_transport.py'),
        'tests':binding(Path(original.ROOT)/'tests/test_roboboat_isolated_transport_v3.py'),
        'retained_terminals':existing,'untouched_entry_ids':untouched,'settings_unchanged':{'B2':d['B2'],'B4':d['B4'],'timeout_s':d['timeout_s'],'prompt':d['prompt'],'max_workers':2},
        'change':'Credential-safe decoded JSON traces/final returns, exception serialization and partial timeout trace retention; same original isolation/auth/source/evidence/prompt/model/tool/deadline interface. Original sources remain immutable.',
        'quality_retries':0,'reissued_entries':[],'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    with amendment_path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    return value


def run(amendment_path):
    amendment_path=Path(amendment_path).resolve();a=json.loads(amendment_path.read_text())
    for k in ('original_declaration','runner','safe_transport','original_isolation_transport','tests'):
        original.checked(a[k])
    for t in a['retained_terminals']:original.checked(t)
    declaration_path=original.checked(a['original_declaration']);d=json.loads(declaration_path.read_text());original.verify(d,declaration_path)
    root=Path(a['output_root']);entries={e['id']:e for e in d['entries']}
    if len(set(a['untouched_entry_ids']))!=len(a['untouched_entry_ids']):raise ValueError('duplicate successor request')
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(original.execute,entries[k],d,declaration_path,root,caller=safe.call) for k in a['untouched_entry_ids']]
        results=[]
        for job in as_completed(jobs):
            t=job.result();results.append(t);print(t['status'],flush=True)
    out=amendment_path.with_name(amendment_path.stem+'-terminal.json')
    with out.open('x') as f:json.dump({'status':'AMENDMENT_COMPLETED','amendment':binding(amendment_path),'terminals':[binding(root/'responses'/k/'response-terminal.json') for k in a['untouched_entry_ids']], 'quality_retries':0,'confirmation_n':0},f,indent=2);f.write('\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=['prepare','run']);p.add_argument('--amendment',required=True,type=Path);p.add_argument('--declaration',type=Path);p.add_argument('--output-root',type=Path);a=p.parse_args()
    if a.phase=='prepare':
        if not a.declaration or not a.output_root:p.error('prepare needs declaration and output root')
        print('Registered untouched requests:',len(prepare(a.declaration,a.output_root,a.amendment)['untouched_entry_ids']))
    else:run(a.amendment)


if __name__=='__main__':main()
