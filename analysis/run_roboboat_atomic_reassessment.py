#!/usr/bin/env python3
"""Freeze reviewed development packets, then run current isolated support judges.

No method responses are regenerated. The extraction bank must finish and every
unique answer must receive explicit project completeness review before prepare.
The run phase reads only frozen blind packets, never the method/evidence join.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path

from build_roboboat_terminal_batch import save
from roboboat_reviewed_annotation_packet import build_reviewed_packet, validate_review_provenance
from roboboat_isolated_transport import isolated_run
from run_evidence_calibration_agent_annotation import (
    run as annotate, StructuredCodexCliAgentCaller, PROMPT, RETURN_SCHEMA,
    ADJUDICATION_SCHEMA, AMENDMENT, MODEL, EFFORT)

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/roboboat_terminal_evidence'
BANK=ROOT/'artifacts/roboboat-terminal-atomic-inventory-v1'
OUT=ROOT/'artifacts/roboboat-terminal-atomic-reassessment-v1'
DECLARATION=DOC/'marine_atomic_reassessment_declaration_v1.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def binding(path):
    return {'path':str(path.relative_to(ROOT)),'sha256':digest(path)}


def load_complete_reviews(bank):
    structural=json.loads((bank/'structural-result.json').read_text())
    if structural['status']!='COMPLETE_BLIND_BANK_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING':
        raise ValueError('bank extraction incomplete')
    entries=json.loads((bank/'blind-bank.json').read_text())['entries']
    if len(entries)!=structural['unique_answer_texts']:
        raise ValueError('bank population mismatch')
    reviews={}
    for entry in entries:
        key=entry['opaque_response_id']
        review=json.loads((bank/'project_reviews'/f'{key}.json').read_text())
        validate_review_provenance(entry['response_text'],review,
            {slot:(bank/'returns'/f'{key}-{slot}.json').read_bytes() for slot in ('A','B')})
        if review['status']!='COMPLETE_FAITHFUL_PROJECT_REVIEW':
            raise ValueError('complete-bank project review gate closed')
        reviews[key]=review
    return entries,reviews


def prepare():
    if DECLARATION.exists():
        raise ValueError('development declaration already frozen; do not overwrite')
    if OUT.exists():
        raise ValueError('output root exists; inspect incomplete preparation, do not overwrite')
    entries,reviews=load_complete_reviews(BANK)
    answers={e['opaque_response_id']:e['response_text'] for e in entries}
    joins=json.loads((BANK/'evaluator-join.json').read_text())['entries']
    declaration=json.loads((DOC/'marine_pilot_atomic_inventory_declaration_v1.json').read_text())
    if len(joins)!=declaration['original_answer_n']:
        raise ValueError('original answer population mismatch')
    dependencies=[Path(__file__).resolve(),ROOT/'analysis/roboboat_reviewed_annotation_packet.py',
        ROOT/'analysis/run_roboboat_terminal_comparison.py',ROOT/'analysis/roboboat_isolated_transport.py',
        ROOT/'analysis/run_evidence_calibration_agent_annotation.py',
        ROOT/'analysis/adjudicate_evidence_calibration_annotations.py',PROMPT,RETURN_SCHEMA,
        ADJUDICATION_SCHEMA,AMENDMENT,
        ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json',
        ROOT/'artifacts/roboboat-terminal-v1/qualification-v2/qualification-result.json',
        BANK/'blind-bank.json',BANK/'evaluator-join.json',BANK/'structural-result.json',
        DOC/'marine_pilot_atomic_inventory_declaration_v1.json']
    qualification=json.loads(
        (ROOT/'artifacts/roboboat-terminal-v1/qualification-v2/qualification-result.json').read_text())
    if qualification['status']!='QUALIFIED':
        raise ValueError('marine support qualification gate closed')
    qualified=json.loads((ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json').read_text())['qualified_binding']
    if (qualified['model'],qualified['reasoning_effort'],qualified['isolated_passes'])!=(MODEL,EFFORT,2):
        raise ValueError('current binding differs from support runner; explicit successor required')
    for item in qualified.values():
        if isinstance(item,dict) and 'path' in item and 'sha256' in item:
            path=ROOT/item['path']
            if digest(path)!=item['sha256']:
                raise ValueError('qualified support binding changed: '+item['path'])
            dependencies.append(path)
    for key in reviews:
        dependencies.append(BANK/'project_reviews'/f'{key}.json')
        dependencies.extend(BANK/'returns'/f'{key}-{s}.json' for s in ('A','B'))
        prior=reviews[key].get('prior_project_review_sha256')
        if prior:
            history=BANK/'project_review_history'/f'{key}-{prior}.json'
            if digest(history)!=prior:
                raise ValueError('prior project review history changed')
            dependencies.append(history)
    packets=[];evaluator=[];seen=set()
    for join in joins:
        key=join['opaque_response_id'];answer=answers[key]
        root=ROOT/f"artifacts/roboboat-terminal-{join['source_version']}"
        source=root/'comparison'/join['batch']/join['level']/f"{join['method']}.json"
        if digest(source)!=join['answer_sha256'] or json.loads(source.read_text())['answer']!=answer:
            raise ValueError('original response changed')
        evidence_path=root/'batches'/join['batch']/'method_packets'/f"{join['level']}.json"
        reference_path=root/'batches'/join['batch']/'evaluator'/f"{join['level']}-reference.json"
        evidence=json.loads(evidence_path.read_text());reference=json.loads(reference_path.read_text())
        packet=build_reviewed_packet(evidence,answer,reference,reviews[key])
        opaque=packet['forms'][0]['packet_id']
        if opaque in seen:
            raise ValueError('duplicate episode/support identity')
        seen.add(opaque)
        target=OUT/'blind_packets'/f'{opaque}.json';save(target,packet)
        packets.append(binding(target));evaluator.append({**join,'support_packet_id':opaque})
        dependencies.extend((source,evidence_path,reference_path))
    save(OUT/'evaluator-join.json',{'entries':evaluator,'annotation_input':False})
    dependencies.append(OUT/'evaluator-join.json')
    save(DECLARATION,{'schema':'roboboat-reviewed-development-reassessment/v1',
        'disposition':'INSPECTED_DEVELOPMENT_REASSESSMENT_ONLY',
        'status':'FROZEN_BEFORE_NEW_SUPPORT_CALLS','dependencies':[binding(p) for p in dict.fromkeys(dependencies)],
        'packets':packets,'original_answers':len(joins),'unique_answer_texts':len(entries),
        'judge':{'model':qualified['model'],'effort':qualified['reasoning_effort'],
                 'passes':qualified['isolated_passes'],'adjudication':'disagreement only'},
        'max_concurrent_packets':2,'quality_retries':0,'agent_assessed':True,
        'inventory':'explicit project completeness review; unqualified abstraction tags removed',
        'score':'development required-unit coverage and complete asserted-claim support; materiality mapping unfrozen',
        'prior_scores_replaced':False,'confirmatory_endpoint_promoted':False,
        'physical_n_added':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0})
    print('prepared',len(packets),'blinded development packets',flush=True)


def run_one(packet_binding,judge):
    path=ROOT/packet_binding['path'];key=path.stem
    target=OUT/'annotations'/key;terminal=target/'development-summary.json'
    if terminal.exists():
        result=json.loads(terminal.read_text())
        if result['packet_sha256']!=digest(path) or not result['finalized']:
            raise ValueError('retained annotation terminal mismatch')
        return key
    intent=OUT/'intents'/f'{key}.json';intent.parent.mkdir(parents=True,exist_ok=True)
    # Exclusive creation also prevents two concurrent queue invocations from
    # submitting the same request. A missing terminal requires inspection.
    with intent.open('x') as handle:
        json.dump({'packet':packet_binding,'declaration_sha256':digest(DECLARATION)},handle)
    annotate(path,target,caller=StructuredCodexCliAgentCaller(
        target/'calls',model=judge['model'],effort=judge['effort'],runner=isolated_run))
    return key


def run():
    declaration=json.loads(DECLARATION.read_text())
    if declaration['disposition']!='INSPECTED_DEVELOPMENT_REASSESSMENT_ONLY':
        raise ValueError('development-only gate closed')
    for item in declaration['dependencies']+declaration['packets']:
        if digest(ROOT/item['path'])!=item['sha256']:
            raise ValueError('frozen reassessment binding changed: '+item['path'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        for job in as_completed([pool.submit(run_one,p,declaration['judge']) for p in declaration['packets']]):
            print('support finalized',job.result(),flush=True)
    save(OUT/'structural-result.json',{'status':'COMPLETE_AGENT_ASSESSED_SUPPORT_REASSESSMENT_SCORING_PENDING',
        'answers':len(declaration['packets']),'physical_n_added':0,'alpha_consumed':0,
        'original_scores_replaced':False,'confirmation_endpoint_promoted':False})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['prepare','run']);args=parser.parse_args()
    prepare() if args.phase=='prepare' else run()
