#!/usr/bin/env python3
"""Successor orchestrator: corrected projection, preserved old attempts, no reruns."""
import argparse
import fcntl
import json
from pathlib import Path
import run_roboboat_population_development_v1 as inherited
from export_roboboat_population_v2 import project, publish_terminal
from generate_roboboat_population_v1 import digest
from build_roboboat_terminal_batch import save


def main():
    p=argparse.ArgumentParser();p.add_argument('--registry',required=True,type=Path);p.add_argument('--output-root',required=True,type=Path)
    p.add_argument('--domain',default=191,type=int);p.add_argument('--port',default=11481,type=int);a=p.parse_args()
    registry=json.loads(a.registry.read_text())
    if registry['status']!='DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION':raise ValueError('development registry required')
    config=inherited.bound(registry['nav2_configuration']);output=a.output_root.resolve()
    # Inherited launch and technical admission are unchanged. New packet projection
    # writes a different namespace; old partial exports and terminals remain intact.
    inherited.build=lambda row,out,conf:project(row,out,out/'exports-v2',conf)
    with Path('/tmp/crane-roboboat-population-render.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        results=[]
        for row in registry['rows']:
            capture=output/row['id'];original=capture/'capture-attempt.json'
            old=json.loads(original.read_text()) if original.exists() else None
            if old and old['status']=='TECHNICAL_FAILURE' and old.get('error')=='ladder is not removal-only nested':
                result=publish_terminal(row,a.registry,capture,config)
            else:
                result=inherited.capture(row,registry,a.registry.resolve(),output,a.domain,a.port)
                if result['status']=='VALID_DEVELOPMENT':result=publish_terminal(row,a.registry,capture,config)
            results.append(result)
            if len(results)>=2 and all(r['status']=='TECHNICAL_FAILURE' for r in results[-2:]):break
        save(output/'batch-accounting-v2.json',{'status':'DEVELOPMENT_ONLY','registry_sha256':digest(a.registry),
             'collector_v2_sha256':digest(Path(__file__)),'attempted':len(results),
             'valid_recordings':sum(r['status']=='VALID_DEVELOPMENT' for r in results),
             'technical_failures':sum(r['status']=='TECHNICAL_FAILURE' for r in results),
             'complete_paired_clusters':sum(all(any(r['row']['id']==identifier and r['status']=='VALID_DEVELOPMENT' for r in results) for identifier in cluster['rows']) for cluster in registry['clusters']),
             'unattempted':[row['id'] for row in registry['rows'] if row['id'] not in {r['row']['id'] for r in results}],
             'quality_retries':0,'confirmation_n':0,'land_n_added':0})

if __name__=='__main__':main()
