"""Thin navigation ontology + primitive bindings for the pinned main CRANE core.

No evaluator references, scenario fields, released answers or labels are inputs.
The realization is deterministic and replaces component realization explicitly.
"""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_io import canonical_sha256,ontology_from_dict
from maximal_supported_diagnosis import diagnose
from realize_evidence_calibrated_explanation import realize

def check_core_pin():
    import hashlib
    pin=json.loads((ROOT/'data/hexar_external/audit/source_data_manifest.json').read_text())
    for name,digest in pin['crane_core_hashes'].items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError(f'Pinned core changed: {name}')

def ontology():
    reqs=[];claims=[];nodes=[]
    specs=[('timeout','navigation_outcomes','I did not complete navigation before the skill timed out.','TASK_OUTCOME',0,[]),
           ('manual','manual_state','Manual joystick mode was recorded.','OBSERVATION',0,[]),
           ('progress','navigation_logs','The controller reported that it failed to make progress.','SOFTWARE_ACTION',0,[]),
           ('physical','physical_cause_measurement','An obstacle physically caused the navigation failure.','SPECIFIC_PHYSICAL_CAUSE',2,['node-timeout'])]
    for name,role,text,kind,rank,parents in specs:
        reqs.append({'requirement_id':'req-'+name,'evidence_roles':[role],
            'predicate_id':'hexar-'+name+'-visible-v1','predicate_version':'v1-development',
            'description':{'timeout':'A retained failed navigation skill explicitly reports timeout.',
                'manual':'The latest retained joystick state is explicitly true; no absent-to-false conversion.',
                'progress':'An in-window retained controller log explicitly reports failure to make progress.',
                'physical':'Episode-linked direct physical-cause evidence, not a symptom or source conditional.'}[name]})
        claims.append({'claim_id':'claim-'+name,'proposition':text,'mechanism_family':'navigation',
            'claim_kind':kind,'diagnostic_node_id':'node-'+name,'required_evidence_ids':['req-'+name],
            'non_entailment_ids':['limit-cause'] if name in ('timeout','manual','progress') else []})
        nodes.append({'node_id':'node-'+name,'mechanism_family':'navigation','label':name,
            'rank_within_family':rank,'parent_node_ids':parents,'claim_ids':['claim-'+name]})
    out={'schema':'crane-evidence-calibration-ontology/v1','catalog_id':'hexar-navigation-development-v1',
         'catalog_version':'v1-development','evidence_requirements':reqs,'claim_contracts':claims,'diagnostic_nodes':nodes,
         'non_entailments':[{'non_entailment_id':'limit-cause','basis_claim_ids':['claim-timeout','claim-manual','claim-progress'],
            'unsupported_consequent_claim_ids':['claim-physical'],
            'additional_evidence_requirement_ids':['req-physical'],
            'rationale':'These records do not establish the physical cause of the navigation failure.'}]}
    ontology_from_dict(out)
    return out

def contract_answer(packet,job):
    check_core_pin();ont=ontology();evidence=packet['evidence']
    refs={
        'timeout':[x['evidence_id'] for x in evidence['navigation_outcomes'] if x['status'].lower()=='failed' and 'timed out' in (x['error_msg'] or '').lower()],
        'manual':[x['evidence_id'] for x in evidence['manual_state'] if x['value'] is True],
        'progress':[x['evidence_id'] for x in evidence['navigation_logs'] if x['logger']=='controller_server' and x['message']=='Failed to make progress'],
        'physical':[]}
    ids=sorted({x['evidence_id'] for rows in evidence.values() for x in rows})
    condition={'condition_id':job,'episode_id':'dev001','configuration_id':'hexar-navigation-component-v1',
        'method_packet_sha256':canonical_sha256(packet),'available_evidence_ids':ids}
    facts={'schema':'crane-visible-evidence-requirement-facts/v1','condition_id':job,
        'method_packet_sha256':canonical_sha256(packet),
        'question_contract':{'question_id':canonical_sha256(packet['question'])[:12],
            'failure_premise':True,'required_mechanism_families':['navigation']},
        'requirement_evaluations':[{'requirement_id':'req-'+key,'status':'SATISFIED' if value else 'ABSENT',
            'support_references':value,'detail':'Deterministic visible predicate; absence is unknown.'} for key,value in refs.items()],
        'ambiguity_node_ids':[]}
    result=diagnose(ont,{'condition':condition,'method_packet':packet},facts)
    selected=[x for x in ('claim-timeout','claim-manual') if x in result['approved_claim_ids']]
    if not selected:selected=[x for x in ('claim-progress',) if x in result['approved_claim_ids']]
    if not selected:raise ValueError('No registered useful proposition; technical extension required, not favorable abstention.')
    plan={'schema':'crane-claim-realization-plan/v1','plan_id':job,
        'diagnostic_result_sha256':canonical_sha256(result),'required_claim_ids':selected,
        'optional_claim_ids':[],'required_non_entailment_ids':result['required_non_entailment_ids'],
        'approved_numeric_values':[]}
    candidate={'schema':'crane-claim-realization-candidate/v1','response_id':job,
        'plan_sha256':canonical_sha256(plan),'clauses':[
            {'clause_id':f'c{i}','kind':'CLAIM','contract_id':cid,'numeric_values':[]} for i,cid in enumerate(selected)]+[
            {'clause_id':f'n{i}','kind':'NON_ENTAILMENT','contract_id':cid,'numeric_values':[]} for i,cid in enumerate(plan['required_non_entailment_ids'])]}
    answer=realize(ont,result,plan,candidate)
    if len(answer['final_response'].split())>60:raise ValueError('Common output allowance exceeded')
    return {'ontology':ont,'facts':facts,'diagnosis':result,'plan':plan,'realization':answer,
            'answer':answer['final_response'],'model_calls':0,'template':True,'fallback':False}
