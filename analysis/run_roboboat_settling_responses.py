#!/usr/bin/env python3
"""Same-evidence development responses; keep atomic extraction/judging separate."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from roboboat_isolated_transport import call
from run_roboboat_terminal_comparison import SCHEMA

OUT=ROOT/'artifacts/roboboat-terminal-settling-v1/responses'
BATCHES=ROOT/'artifacts/roboboat-terminal-settling-v1/batches'
DECLARATION=DOC/'settling_response_declaration_v1.json'


def execute(batch,level,declaration):
    packet_path=BATCHES/batch/'method_packets'/f'L{level}.json'
    packet=json.loads(packet_path.read_text());output=OUT/batch/f'L{level}'
    intent=OUT/'intents'/f'{batch}-L{level}.json';terminal=output/'response-terminal.json'
    b4=json.loads((BATCHES/batch/'candidate_v3_outputs'/f'L{level}.json').read_text())
    source_id={'packet_sha256':digest(packet_path),'declaration_sha256':digest(DECLARATION),
               'b4_sha256':digest(BATCHES/batch/'candidate_v3_outputs'/f'L{level}.json')}
    if terminal.exists():
        if json.loads(terminal.read_text())['source_identity']!=source_id:
            raise ValueError('retained response source mismatch')
        return batch,level
    intent.parent.mkdir(parents=True,exist_ok=True)
    with intent.open('x') as handle:json.dump(source_id,handle)
    with tempfile.TemporaryDirectory(prefix='boat-settling-b2-') as tmp:
        work=Path(tmp);save(work/'evidence.json',packet)
        for binding in declaration['method_sources']:
            source=ROOT/binding['path'];shutil.copyfile(source,work/source.name)
        result=call(OUT/'calls',f"{packet['packet_id']}-L{level}",work,
            (DOC/'marine_b2_settling_prompt_v1.txt').read_text(),
            declaration['B2']['model'],declaration['B2']['effort'],SCHEMA,allow_tools=True)
    save(output/'B2.json',{'answer':result['parsed_final']['answer'],'cache_key':result['cache_key'],
        'latency_s':result['latency_s'],'model_calls':1})
    save(output/'B4.json',{'answer':b4['answer'],'model_calls':0})
    save(terminal,{'source_identity':source_id,'status':'COMPLETE_RESPONSE_SUPPORT_UNJUDGED',
        'new_independent_cluster_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0})
    return batch,level


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--available-only',action='store_true');args=parser.parse_args()
    declaration=json.loads(DECLARATION.read_text())
    if declaration['disposition']!='DEVELOPMENT_EXPLORATORY_NO_CONFIRMATORY_ALLOCATION':
        raise ValueError('development gate closed')
    for binding in declaration['dependencies']+declaration['method_sources']:
        if digest(ROOT/binding['path'])!=binding['sha256']:
            raise ValueError('response binding changed: '+binding['path'])
    available=[b for b in declaration['batches'] if (BATCHES/b/'summary.json').exists()]
    pending=[b for b in declaration['batches'] if b not in available]
    if pending and not args.available_only:raise ValueError('declared captures not all published')
    print('pending declared batches',pending,flush=True)
    # One response call at a time; already-running annotation pool remains bounded.
    with ThreadPoolExecutor(max_workers=1) as pool:
        for job in as_completed([pool.submit(execute,b,level,declaration) for b in available for level in range(3)]):
            print('responses retained',job.result(),flush=True)


if __name__=='__main__':main()
