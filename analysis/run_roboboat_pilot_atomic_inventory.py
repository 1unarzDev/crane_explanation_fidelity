#!/usr/bin/env python3
"""Apply the separately checked marine extractor to the complete blind answer bank.

Identical answer bytes share extraction only. Evidence/support and statistical
clusters stay distinct. No method key or robot evidence reaches the extractor.
"""
import hashlib
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from build_roboboat_terminal_batch import save
from run_roboboat_atomization_extension_v5 import execute

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/roboboat_terminal_evidence'
OUT=ROOT/'artifacts/roboboat-terminal-atomic-inventory-v1'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    declaration=json.loads((DOC/'marine_pilot_atomic_inventory_declaration_v1.json').read_text())
    for key in ('bank','qualification_review','extractor_freeze','runner'):
        binding=declaration[key]
        if digest(ROOT/binding['path'])!=binding['sha256']:
            raise ValueError('declared binding changed: '+key)
    review=json.loads((ROOT/declaration['qualification_review']['path']).read_text())
    if review['status']!='PASS_BOUNDED_MARINE_ACTOR_CLOCK_PHASE_COMPLETENESS_EXTRACTION':
        raise ValueError('marine extraction gate closed')
    freeze=json.loads((ROOT/declaration['extractor_freeze']['path']).read_text())
    for key in ('prompt','output_schema','transport','runner','actor_appendix'):
        if digest(ROOT/freeze[key]['path'])!=freeze[key]['sha256']:
            raise ValueError('extractor binding changed: '+key)
    bank=json.loads((ROOT/declaration['bank']['path']).read_text())
    if any(set(e)!={'opaque_response_id','response_text'} for e in bank['entries']):
        raise ValueError('blind bank includes prohibited metadata')
    with ThreadPoolExecutor(max_workers=2) as pool:
        for entry in bank['entries']:
            case={'case_id':entry['opaque_response_id'],'response_text':entry['response_text']}
            jobs=[pool.submit(execute,case,slot,freeze,OUT) for slot in ('A','B')]
            for job in jobs:job.result()
            print('structural inventory',entry['opaque_response_id'],flush=True)
    save(OUT/'structural-result.json',{
        'status':'COMPLETE_BLIND_BANK_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING',
        'unique_answer_texts':len(bank['entries']),'passes':2,
        'original_answers':declaration['original_answer_n'],
        'semantic_completeness_established':False,'support_annotation_authorized':False,
        'endpoint_scoring_authorized':False,'physical_n_added':0,'alpha_consumed':0})


if __name__=='__main__':main()
