#!/usr/bin/env python3
"""Prepare complete response bank, then reuse qualified blind marine extraction."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from run_roboboat_atomization_extension_v5 import execute

OUT=ROOT/'artifacts/roboboat-contact-policy-inventory-v2'
SOURCE=ROOT/'artifacts/roboboat-contact-policy-comparison-v2'
DECLARATION=DOC/'contact_policy_inventory_declaration_v2.json'


def prepare():
    if OUT.exists() or DECLARATION.exists():raise ValueError('one-shot bank already exists')
    response_declaration=DOC/'contact_policy_response_declaration_v2.json'
    d=json.loads(response_declaration.read_text());joins=[];texts={};dependencies=[response_declaration,
        ROOT/'analysis/run_roboboat_contact_policy_inventory_v2.py',DOC/'marine_atomization_semantic_review_v5.json',DOC/'marine_atomization_freeze_v5.json']
    for entry in d['entries']:
        source=SOURCE/'responses'/entry['id'];terminal=source/'response-terminal.json'
        value=json.loads(terminal.read_text())
        expected={'declaration_sha256':digest(response_declaration),'packet_sha256':entry['packet']['sha256'],'candidate_sha256':entry['candidate']['sha256']}
        if value['status']!='COMPLETE_RESPONSE_SUPPORT_UNJUDGED' or value['source_identity']!=expected:
            raise ValueError('response identity/completeness gate closed')
        dependencies.append(terminal)
        for method in ('B2','B4'):
            path=source/f'{method}.json';answer=json.loads(path.read_text())['answer']
            key=hashlib.sha256(answer.encode()).hexdigest()
            if key in texts and texts[key]!=answer:raise ValueError('answer hash collision')
            texts[key]=answer;dependencies.append(path)
            joins.append({'opaque_response_id':key,'response_id':entry['id'],'level':entry['level'],'method':method,'episode':entry['episode'],'existing_cluster':entry['existing_cluster'],'answer_path':str(path.relative_to(ROOT)),'answer_file_sha256':digest(path)})
    if len(joins)!=12:raise ValueError('complete twelve-answer bank required')
    OUT.mkdir(parents=True)
    save(OUT/'blind-bank.json',{'entries':[{'opaque_response_id':key,'response_text':value} for key,value in sorted(texts.items())]})
    save(OUT/'evaluator-join.json',{'entries':joins,'annotation_input':False})
    dependencies += [OUT/'blind-bank.json',OUT/'evaluator-join.json']
    freeze=json.loads((DOC/'marine_atomization_freeze_v5.json').read_text())
    for key in ('prompt','output_schema','transport','runner','actor_appendix','qualified_disposition','qualified_freeze'):
        b=freeze[key]
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('extractor binding changed')
        dependencies.append(ROOT/b['path'])
    save(DECLARATION,{'schema':'roboboat-contact-policy-atomic-inventory-development/v2','disposition':'INSPECTED_DEVELOPMENT_EXTRACTION_ONLY','dependencies':[{'path':str(p.relative_to(ROOT)),'sha256':digest(p)} for p in dict.fromkeys(dependencies)],'unique_answer_texts':len(texts),'original_answers':12,'model':freeze['candidate'],'passes':2,'max_concurrent_calls':2,'quality_retries':0,'qualification':'Current unchanged qualified atomizer plus marine-only actor/clock/phase appendix v5. Structural completion still requires project full-source completeness reviews.','new_independent_configuration_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'primary_endpoint_qualified':False,'old_banks_replaced':False})
    print('prepared twelve-answer bank with',len(texts),'unique texts',flush=True)


def run():
    d=json.loads(DECLARATION.read_text())
    if d['disposition']!='INSPECTED_DEVELOPMENT_EXTRACTION_ONLY':raise ValueError('development gate closed')
    for b in d['dependencies']:
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('declared dependency changed')
    review=json.loads((DOC/'marine_atomization_semantic_review_v5.json').read_text())
    if review['status']!='PASS_BOUNDED_MARINE_ACTOR_CLOCK_PHASE_COMPLETENESS_EXTRACTION':raise ValueError('marine extraction gate closed')
    freeze=json.loads((DOC/'marine_atomization_freeze_v5.json').read_text())
    bank=json.loads((OUT/'blind-bank.json').read_text())
    if len(bank['entries'])!=d['unique_answer_texts'] or any(set(e)!={'opaque_response_id','response_text'} for e in bank['entries']):raise ValueError('blind metadata/population leak')
    with ThreadPoolExecutor(max_workers=2) as pool:
        for e in bank['entries']:
            jobs=[pool.submit(execute,{'case_id':e['opaque_response_id'],'response_text':e['response_text']},slot,freeze,OUT) for slot in ('A','B')]
            for job in jobs:job.result()
            print('structural contact-policy inventory',e['opaque_response_id'],flush=True)
    save(OUT/'structural-result.json',{'status':'COMPLETE_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING','original_answers':12,'unique_answer_texts':d['unique_answer_texts'],'passes':2,'semantic_completeness_established':False,'support_annotation_authorized':False,'endpoint_scoring_authorized':False,'new_independent_configuration_n':0,'alpha_consumed':0})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run']);a=p.parse_args()
    prepare() if a.phase=='prepare' else run()
