#!/usr/bin/env python3
"""Freeze and annotate reviewed fixed-stopping development answers.

Reuses the current qualified support runner without changing any land binding
or prior marine freeze. The added L2 coverage unit measures established partial
compliance; it is explicitly development-only and is supplied equally to judges
of both methods, never as a method response instruction after generation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from roboboat_reviewed_annotation_packet import build_reviewed_packet
from run_roboboat_atomic_reassessment import load_complete_reviews,binding
from run_evidence_calibration_agent_annotation import (
    run as annotate,StructuredCodexCliAgentCaller,PROMPT,RETURN_SCHEMA,ADJUDICATION_SCHEMA,AMENDMENT,MODEL,EFFORT)
from roboboat_isolated_transport import isolated_run

BANK=ROOT/'artifacts/roboboat-terminal-settling-atomic-inventory-v1'
SOURCE=ROOT/'artifacts/roboboat-terminal-settling-v1'
OUT=ROOT/'artifacts/roboboat-terminal-settling-support-v1'
DECLARATION=DOC/'settling_support_declaration_v1.json'
PARTIAL_UNIT=('When the declared dwell has complete sampled position, heading, speed, yaw-rate and hull compliance, '
              'communicate that supported partial compliance at sampled temporal scope; unknown contact does not erase it.')


def prepare():
    if DECLARATION.exists() or OUT.exists():raise ValueError('one-shot preparation already exists')
    entries,reviews=load_complete_reviews(BANK)
    answers={e['opaque_response_id']:e['response_text'] for e in entries}
    joins=json.loads((BANK/'evaluator-join.json').read_text())['entries']
    if len(joins)!=12 or len(entries)!=11:raise ValueError('fixed settling population differs')
    disposition=ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json'
    qualified=json.loads(disposition.read_text())['qualified_binding']
    if (qualified['model'],qualified['reasoning_effort'],qualified['isolated_passes'])!=(MODEL,EFFORT,2):
        raise ValueError('qualified judge binding differs from runner')
    dependencies=[Path(__file__).resolve(),ROOT/'analysis/run_roboboat_atomic_reassessment.py',
        ROOT/'analysis/roboboat_reviewed_annotation_packet.py',ROOT/'analysis/run_roboboat_terminal_comparison.py',
        ROOT/'analysis/run_evidence_calibration_agent_annotation.py',ROOT/'analysis/adjudicate_evidence_calibration_annotations.py',
        ROOT/'analysis/roboboat_isolated_transport.py',PROMPT,RETURN_SCHEMA,ADJUDICATION_SCHEMA,AMENDMENT,disposition,
        BANK/'blind-bank.json',BANK/'evaluator-join.json',BANK/'structural-result.json',
        DOC/'settling_atomic_inventory_declaration_v1.json',DOC/'settling_pilot_registry_v1.json',
        DOC/'marine_qualification_freeze_v2.json',DOC/'marine_qualification_suite_v1.json',
        ROOT/'artifacts/roboboat-terminal-v1/qualification-v2/qualification-result.json']
    if json.loads(dependencies[-1].read_text())['status']!='QUALIFIED':raise ValueError('marine support qualification gate closed')
    for value in qualified.values():
        if isinstance(value,dict) and 'path' in value:
            path=ROOT/value['path']
            if digest(path)!=value['sha256']:raise ValueError('qualified binding changed')
            dependencies.append(path)
    for key in reviews:
        dependencies.append(BANK/'project_reviews'/f'{key}.json')
        dependencies.extend(BANK/'returns'/f'{key}-{s}.json' for s in ('A','B'))
    packets=[];evaluator=[];seen=set()
    for join in joins:
        key=join['opaque_response_id'];source=ROOT/join['answer_path'];answer=answers[key]
        if digest(source)!=join['answer_file_sha256'] or json.loads(source.read_text())['answer']!=answer:
            raise ValueError('source answer changed')
        batch=SOURCE/'batches'/join['batch'];level=join['level']
        evidence_path=batch/'method_packets'/f'{level}.json';reference_path=batch/'evaluator'/f'{level}-reference.json'
        packet=build_reviewed_packet(json.loads(evidence_path.read_text()),answer,
            json.loads(reference_path.read_text()),reviews[key])
        if level=='L2':
            for form in packet['forms']:
                form['required_unit_coverage'].append({'unit_prompt':PARTIAL_UNIT,'communicated':None,'response_span':None})
        opaque=packet['forms'][0]['packet_id']
        if opaque in seen:raise ValueError('duplicate episode-scoped support packet')
        seen.add(opaque);target=OUT/'blind_packets'/f'{opaque}.json';save(target,packet)
        packets.append(binding(target));evaluator.append({**join,'support_packet_id':opaque})
        dependencies.extend((source,evidence_path,reference_path))
    save(OUT/'evaluator-join.json',{'entries':evaluator,'annotation_input':False})
    dependencies.append(OUT/'evaluator-join.json')
    save(DECLARATION,{'schema':'roboboat-settling-reviewed-support-development/v1',
        'disposition':'INSPECTED_DEVELOPMENT_REASSESSMENT_ONLY','status':'FROZEN_BEFORE_SUPPORT_CALLS',
        'dependencies':[binding(p) for p in dict.fromkeys(dependencies)],'packets':packets,
        'original_answers':12,'unique_answer_texts':11,
        'judge':{'model':qualified['model'],'effort':qualified['reasoning_effort'],'passes':2,'adjudication':'disagreement only'},
        'timeout_s':300,'max_concurrent_packets':2,'quality_retries':0,
        'coverage_extension':{'L2_unit':PARTIAL_UNIT,'scope':'development answerable-information sensitivity, declared after response inspection before judges; no primary confirmatory promotion',
                              'fairness':'identical complete evidence and coverage prompts for both methods'},
        'score':'Report inherited four-unit and additional partial-compliance-unit sensitivity separately. All claims supported and causal limitation preserved; unqualified abstraction tags excluded. No inference or posthoc superiority claim.',
        'new_independent_cluster_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0,
        'original_banks_replaced':False,'human_validation':False})
    print('prepared',len(packets),'settling support packets',flush=True)


def run_one(packet_binding,judge,timeout):
    path=ROOT/packet_binding['path'];key=path.stem;target=OUT/'annotations'/key
    terminal=target/'development-summary.json'
    if terminal.exists():
        result=json.loads(terminal.read_text())
        if result['packet_sha256']!=digest(path) or not result['finalized']:raise ValueError('terminal mismatch')
        return key
    intent=OUT/'intents'/f'{key}.json';intent.parent.mkdir(parents=True,exist_ok=True)
    with intent.open('x') as f:json.dump({'packet':packet_binding,'declaration_sha256':digest(DECLARATION)},f)
    annotate(path,target,caller=StructuredCodexCliAgentCaller(target/'calls',model=judge['model'],
        effort=judge['effort'],timeout_s=timeout,runner=isolated_run))
    return key


def run():
    declaration=json.loads(DECLARATION.read_text())
    if declaration['disposition']!='INSPECTED_DEVELOPMENT_REASSESSMENT_ONLY':raise ValueError('development gate closed')
    for item in declaration['dependencies']+declaration['packets']:
        if digest(ROOT/item['path'])!=item['sha256']:raise ValueError('frozen settling support input changed: '+item['path'])
    with ThreadPoolExecutor(max_workers=2) as pool:
        for job in as_completed([pool.submit(run_one,p,declaration['judge'],declaration['timeout_s']) for p in declaration['packets']]):
            print('settling support finalized',job.result(),flush=True)
    save(OUT/'structural-result.json',{'status':'COMPLETE_AGENT_ASSESSED_SETTLING_SUPPORT_SCORING_PENDING',
        'answers':12,'new_independent_cluster_n':0,'alpha_consumed':0,'confirmation_n':0,'replication_n':0})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('phase',choices=['prepare','run'])
    args=parser.parse_args();prepare() if args.phase=='prepare' else run()
