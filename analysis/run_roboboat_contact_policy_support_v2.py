#!/usr/bin/env python3
"""Current qualified support pipeline, separate contact-v2 development bank.

Whole-answer/partial-information extensions remain development sensitivities,
not qualified material primary scoring or inferential activation.
"""
import argparse
import copy
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
from build_roboboat_terminal_batch import ROOT,DOC,save,digest
from roboboat_reviewed_annotation_packet import build_reviewed_packet,validate_review_provenance
from run_roboboat_atomic_reassessment import binding
from reference_roboboat_temporal import calculate as independent_kinematics
from roboboat_temporal_certificate_v2 import certificate
from roboboat_material_endpoint_v1 import required_units,LIMITS
from run_evidence_calibration_agent_annotation import (
    run as annotate,StructuredCodexCliAgentCaller,PROMPT,RETURN_SCHEMA,ADJUDICATION_SCHEMA,AMENDMENT,MODEL,EFFORT)
from roboboat_isolated_transport import isolated_run

BANK=ROOT/'artifacts/roboboat-contact-policy-inventory-v2'
OUT=ROOT/'artifacts/roboboat-contact-policy-support-v2'
DECLARATION=DOC/'contact_policy_support_declaration_v2.json'


def partial_answerability(packet):
    """Independent evaluator-only isolation of kinematics, not contact sensing."""
    rows=packet.get('post_result',[])
    if not rows:return False
    p=copy.deepcopy(packet)
    p['contacts']={'complete':True,'clock':p['task']['clock'],
        'coverage':[rows[0]['simSeconds'],rows[-1]['simSeconds']],'samples':[]}
    answerable=independent_kinematics(p)['sampled_task_support']=='true'
    cert=certificate(packet)
    expected=cert['coverage']['complete_sampled_window'] and all(
        cert['component_support'][k]=='true' for k in ('position','heading','speed','yaw_rate','hull'))
    if answerable!=expected:raise ValueError('independent partial-answerability reference mismatch')
    return answerable


def load_reviews():
    structural=json.loads((BANK/'structural-result.json').read_text())
    if structural['status']!='COMPLETE_EXTRACTION_PROJECT_COMPLETENESS_REVIEW_PENDING':
        raise ValueError('complete extraction gate closed')
    entries=json.loads((BANK/'blind-bank.json').read_text())['entries']
    if len(entries)!=structural['unique_answer_texts']:raise ValueError('bank identity mismatch')
    reviews={}
    for e in entries:
        key=e['opaque_response_id'];review=json.loads((BANK/'project_reviews'/f'{key}.json').read_text())
        validate_review_provenance(e['response_text'],review,{s:(BANK/'returns'/f'{key}-{s}.json').read_bytes() for s in ('A','B')})
        if review['status']!='COMPLETE_FAITHFUL_PROJECT_REVIEW':raise ValueError('full-source completeness review required')
        reviews[key]=review
    return entries,reviews


def prepare():
    if OUT.exists() or DECLARATION.exists():raise ValueError('one-shot preparation already exists')
    entries,reviews=load_reviews();answers={e['opaque_response_id']:e['response_text'] for e in entries}
    joins=json.loads((BANK/'evaluator-join.json').read_text())['entries']
    if len(joins)!=12:raise ValueError('twelve original instances required')
    response_declaration=DOC/'contact_policy_response_declaration_v2.json'
    response_entries={e['id']:e for e in json.loads(response_declaration.read_text())['entries']}
    disposition=ROOT/'manifests/study/evidence-calibration-agent-qualification-disposition-v1.json'
    q=json.loads(disposition.read_text())['qualified_binding']
    if (q['model'],q['reasoning_effort'],q['isolated_passes'])!=(MODEL,EFFORT,2):raise ValueError('current support binding differs')
    old_qualification=ROOT/'artifacts/roboboat-terminal-v1/qualification-v2/qualification-result.json'
    if json.loads(old_qualification.read_text())['status']!='QUALIFIED':raise ValueError('existing bounded marine support gate closed')
    dependencies=[Path(__file__).resolve(),ROOT/'analysis/roboboat_reviewed_annotation_packet.py',ROOT/'analysis/run_roboboat_atomic_reassessment.py',ROOT/'analysis/run_roboboat_terminal_comparison.py',ROOT/'analysis/roboboat_material_endpoint_v1.py',ROOT/'analysis/reference_roboboat_temporal.py',ROOT/'analysis/roboboat_temporal_certificate_v2.py',ROOT/'analysis/roboboat_temporal_certificate.py',ROOT/'analysis/run_evidence_calibration_agent_annotation.py',ROOT/'analysis/adjudicate_evidence_calibration_annotations.py',ROOT/'analysis/roboboat_isolated_transport.py',PROMPT,RETURN_SCHEMA,ADJUDICATION_SCHEMA,AMENDMENT,disposition,old_qualification,response_declaration,DOC/'contact_policy_inventory_declaration_v2.json',DOC/'contact_scope_development_disposition_v3.json',DOC/'MATERIAL_ENDPOINT_V1.md',BANK/'blind-bank.json',BANK/'evaluator-join.json',BANK/'structural-result.json']
    for v in q.values():
        if isinstance(v,dict) and 'path' in v:
            p=ROOT/v['path']
            if digest(p)!=v['sha256']:raise ValueError('qualified binding changed')
            dependencies.append(p)
    for key in reviews:
        dependencies += [BANK/'project_reviews'/f'{key}.json',*[BANK/'returns'/f'{key}-{s}.json' for s in ('A','B')]]
    packets=[];evaluator=[];seen=set()
    for join in joins:
        key=join['opaque_response_id'];source=ROOT/join['answer_path']
        if digest(source)!=join['answer_file_sha256'] or json.loads(source.read_text())['answer']!=answers[key]:raise ValueError('source response changed')
        e=response_entries[join['response_id']]
        packet_path=ROOT/e['packet']['path'];reference_path=ROOT/e['reference']['path']
        for name in ('packet','reference'):
            if digest(ROOT/e[name]['path'])!=e[name]['sha256']:raise ValueError('response evidence/reference changed')
        evidence=json.loads(packet_path.read_text());answerable=partial_answerability(evidence)
        p=build_reviewed_packet(evidence,answers[key],json.loads(reference_path.read_text()),reviews[key])
        for form in p['forms']:
            form['required_unit_coverage']=[{'unit_prompt':u,'communicated':None,'response_span':None} for u in required_units(answerable)]
            form['limitation_preservation']=[{'limitation_prompt':l,'preserved':None,'response_span':None} for l in LIMITS]
        p['endpoint_status']='Unqualified material-primary mapping; strict/coverage/whole-answer development sensitivities only'
        opaque=p['forms'][0]['packet_id']
        if opaque in seen:raise ValueError('duplicate support identity')
        seen.add(opaque);target=OUT/'blind_packets'/f'{opaque}.json';save(target,p)
        packets.append(binding(target));evaluator.append({**join,'support_packet_id':opaque,'partial_information_answerable':answerable})
        dependencies += [source,packet_path,reference_path]
    save(OUT/'evaluator-join.json',{'entries':evaluator,'annotation_input':False});dependencies.append(OUT/'evaluator-join.json')
    save(DECLARATION,{'schema':'roboboat-contact-policy-reviewed-support/v2','disposition':'INSPECTED_DEVELOPMENT_SENSITIVITY_ONLY','packets':packets,'dependencies':[binding(p) for p in dict.fromkeys(dependencies)],'original_answers':12,'unique_answer_texts':len(entries),'judge':{'model':q['model'],'effort':q['reasoning_effort'],'passes':2,'adjudication':'disagreement only'},'max_concurrent_packets':2,'timeout_s':300,'quality_retries':0,'extensions':'Independent answerability selects positive sampled-information unit equally for both methods; whole-answer cause and temporal/evidence limitations are separately judged. Existing global/marine qualified binding remains unchanged; newer lexical-span qualification failures retained. These extra mappings are development sensitivities, not qualified primary endpoint or confirmatory promotion.','scoring':'All reviewed claim support, common-unit coverage, conditional positive-information coverage and whole-answer limitations reported separately; strict conjunction sensitivity only, no unsupported-material classification or exact-wording score. Missing judgments retained and complete-bank release required.','new_independent_configuration_n':0,'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'agent_assessed':True,'human_validation':False,'old_banks_replaced':False})
    print('prepared twelve current-binding support packets',flush=True)


def run_one(b,judge,timeout):
    path=ROOT/b['path'];key=path.stem;target=OUT/'annotations'/key;terminal=target/'development-summary.json'
    if terminal.exists():
        r=json.loads(terminal.read_text())
        if r['packet_sha256']!=digest(path) or not r['finalized']:raise ValueError('terminal mismatch')
        return key
    intent=OUT/'intents'/f'{key}.json';intent.parent.mkdir(parents=True,exist_ok=True)
    with intent.open('x') as f:json.dump({'packet':b,'declaration_sha256':digest(DECLARATION)},f)
    annotate(path,target,caller=StructuredCodexCliAgentCaller(target/'calls',model=judge['model'],effort=judge['effort'],timeout_s=timeout,runner=isolated_run))
    return key


def run():
    d=json.loads(DECLARATION.read_text())
    if d['disposition']!='INSPECTED_DEVELOPMENT_SENSITIVITY_ONLY':raise ValueError('development gate closed')
    for b in d['dependencies']+d['packets']:
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('frozen support input changed')
    plan=json.loads((DOC/'contact_policy_support_analysis_plan_v2.json').read_text())
    if plan['disposition']!='INSPECTED_DEVELOPMENT_SENSITIVITY_ONLY':raise ValueError('analysis lock missing')
    for b in plan['dependencies']:
        if digest(ROOT/b['path'])!=b['sha256']:raise ValueError('prospective analysis binding changed')
    with ThreadPoolExecutor(max_workers=2) as pool:
        for job in as_completed([pool.submit(run_one,p,d['judge'],d['timeout_s']) for p in d['packets']]):print('support finalized',job.result(),flush=True)
    save(OUT/'structural-result.json',{'status':'COMPLETE_AGENT_ASSESSED_SUPPORT_SCORING_PENDING','answers':12,'new_independent_configuration_n':0,'alpha_consumed':0})


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['prepare','run']);a=p.parse_args();prepare() if a.phase=='prepare' else run()
