#!/usr/bin/env python3
"""Declared blind extraction of the complete fixed-stopping response bank."""
from concurrent.futures import ThreadPoolExecutor
import json
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from run_roboboat_atomization_extension_v5 import execute

OUT=ROOT/'artifacts/roboboat-terminal-settling-atomic-inventory-v1'
DECLARATION=DOC/'settling_atomic_inventory_declaration_v1.json'


def main():
    declaration=json.loads(DECLARATION.read_text())
    if declaration['disposition']!='INSPECTED_DEVELOPMENT_REASSESSMENT_ONLY':
        raise ValueError('development extraction gate closed')
    for binding in declaration['dependencies']:
        if digest(ROOT/binding['path'])!=binding['sha256']:
            raise ValueError('settling inventory binding changed')
    review=json.loads((DOC/'marine_atomization_semantic_review_v5.json').read_text())
    if review['status']!='PASS_BOUNDED_MARINE_ACTOR_CLOCK_PHASE_COMPLETENESS_EXTRACTION':
        raise ValueError('bounded marine extractor gate closed')
    freeze=json.loads((DOC/'marine_atomization_freeze_v5.json').read_text())
    for key in ('prompt','output_schema','transport','runner','actor_appendix','qualified_disposition','qualified_freeze'):
        binding=freeze[key]
        if digest(ROOT/binding['path'])!=binding['sha256']:
            raise ValueError('current extractor freeze changed: '+key)
    bank=json.loads((OUT/'blind-bank.json').read_text())
    if len(bank['entries'])!=declaration['unique_answer_texts'] or any(
        set(e)!={'opaque_response_id','response_text'} for e in bank['entries']):
        raise ValueError('blind population or metadata leak')
    with ThreadPoolExecutor(max_workers=2) as pool:
        for entry in bank['entries']:
            case={'case_id':entry['opaque_response_id'],'response_text':entry['response_text']}
            jobs=[pool.submit(execute,case,slot,freeze,OUT) for slot in ('A','B')]
            for job in jobs:job.result()
            print('structural settling inventory',entry['opaque_response_id'],flush=True)
    save(OUT/'structural-result.json',{'status':'COMPLETE_BLIND_BANK_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING',
        'unique_answer_texts':len(bank['entries']),'passes':2,'original_answers':12,
        'semantic_completeness_established':False,'support_annotation_authorized':False,
        'endpoint_scoring_authorized':False,'new_independent_cluster_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0})


if __name__=='__main__':main()
