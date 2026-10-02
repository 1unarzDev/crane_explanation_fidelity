"""Development rich-interface adapter through the unchanged pinned CRANE core.

Approved numeric facts, planner and deterministic verification/realization are
bound to visible packet IDs. Independent evaluation references are not inputs.
"""
import copy
import math
import sys
from pathlib import Path

LEGACY = str(Path(__file__).resolve().parents[1])
if LEGACY not in sys.path:
    sys.path.insert(0, LEGACY)
from study_v2 import ontology as old_ontology, primitive_bindings
from contract_adapter import check_core_pin
from evidence_calibration_io import canonical_sha256, ontology_from_dict
from maximal_supported_diagnosis import diagnose
from realize_evidence_calibrated_explanation import realize

OUTCOMES = ('timeout','abort','failure','success')
DIAGNOSTICS = ('manual','charging','uncertainty','planner','progress')


def ontology():
    value = copy.deepcopy(old_ontology())
    value.update(catalog_id='hexar-simulated-navigation-development-v1',catalog_version='v1-development')
    propositions = {'timeout':'Navigation software reported a timeout.',
                    'abort':'Navigation software reported an abort.',
                    'failure':'Navigation software reported failure.',
                    'success':'Navigation software reported success.',
                    'manual':'The manual-priority indicator was on.',
                    'charging':'The charging-interlock indicator was on.',
                    'uncertainty':'The localization callback reported high uncertainty.',
                    'planner':'The planner reported a failed planning attempt.',
                    'progress':'The controller reported failure to make progress.'}
    for claim in value['claim_contracts']:
        key = claim['claim_id'].removeprefix('claim-')
        if key in propositions:
            claim['proposition'] = propositions[key]
    # Joint clauses allow outcome+diagnostic+motion+limitation within the same
    # strong comparator's unchanged three-sentence/60-word allowance.
    for outcome in OUTCOMES:
        for diagnostic in DIAGNOSTICS:
            key = outcome+'-'+diagnostic
            value['claim_contracts'].append(dict(claim_id='claim-'+key,
                proposition=propositions[outcome].rstrip('.')+'; '+propositions[diagnostic][0].lower()+propositions[diagnostic][1:],
                mechanism_family='navigation',claim_kind='TASK_OUTCOME',diagnostic_node_id='node-'+key,
                required_evidence_ids=['req-'+outcome,'req-'+diagnostic],non_entailment_ids=['limit-physical-and-delay']))
            value['diagnostic_nodes'].append(dict(node_id='node-'+key,mechanism_family='navigation',
                label=key,rank_within_family=0,parent_node_ids=[],claim_ids=['claim-'+key]))
    value['evidence_requirements'].append(dict(requirement_id='req-motion',evidence_roles=['odometry_observation'],
        predicate_id='finite-sampled-odometry-path',predicate_version='v1-development',
        description='Visible finite recording-sampled XY path distance in a nonempty odometry frame.'))
    value['claim_contracts'].append(dict(claim_id='claim-motion',
        proposition='Recorded odometry estimates XY travel in its recorded frame over its sampled recording window.',
        mechanism_family='navigation',claim_kind='OBSERVATION',diagnostic_node_id='node-motion',
        required_evidence_ids=['req-motion'],non_entailment_ids=['limit-physical-and-delay'],
        numeric_slots=[dict(slot_id='path_distance',unit='m',tolerance=0)]))
    value['diagnostic_nodes'].append(dict(node_id='node-motion',mechanism_family='navigation',label='sampled odometry',
        rank_within_family=0,parent_node_ids=[],claim_ids=['claim-motion']))
    value['non_entailments'][0]['basis_claim_ids'] += ['claim-motion']
    value['non_entailments'][0]['rationale'] = 'Reported status and sampled observations do not alone establish physical goal attainment, unique causes, or reasons for delay.'
    ontology_from_dict(value)
    return value


def contract(packet, job, recording):
    if packet.get('schema') != 'hexar-simulated-navigation-development-packet/v1':
        raise ValueError('rich development navigation packet required')
    check_core_pin()
    ont = ontology(); refs = primitive_bindings(packet)
    motion = packet['evidence'].get('odometry_observation', [])
    if len(motion) > 1:
        raise ValueError('ambiguous motion summaries')
    refs['motion'] = []
    if motion:
        row = motion[0]; distance = row['sampled_xy_path_distance_m']
        if type(distance) not in (int,float) or not math.isfinite(distance) or distance < 0 or not row['frame_id'] or row['messages'] < 2:
            raise ValueError('invalid visible sampled motion')
        refs['motion'] = [row['evidence_id']]
    condition = dict(condition_id=job,episode_id=recording,configuration_id='hexar-simulated-navigation-development-v1',
        method_packet_sha256=canonical_sha256(packet),
        available_evidence_ids=sorted({r['evidence_id'] for rows in packet['evidence'].values() for r in rows}))
    facts = dict(schema='crane-visible-evidence-requirement-facts/v1',condition_id=job,
        method_packet_sha256=canonical_sha256(packet),question_contract=dict(question_id=canonical_sha256(packet['question'])[:16],
        failure_premise=False,required_mechanism_families=['navigation']),ambiguity_node_ids=[],
        requirement_evaluations=[dict(requirement_id='req-'+key,status='SATISFIED' if ids else 'ABSENT',support_references=ids,
            detail='Positive visible predicate; missing evidence remains unknown.') for key,ids in refs.items()])
    result = diagnose(ont,dict(condition=condition,method_packet=packet),facts)
    outcome = next((key for key in OUTCOMES if refs[key]),None)
    if outcome is None:
        raise ValueError('no terminal navigation software outcome')
    diagnostic = next((key for key in DIAGNOSTICS if refs[key]),None)
    selected = ['claim-'+outcome+('-'+diagnostic if diagnostic else '')]
    numbers = []
    if refs['motion']:
        selected.append('claim-motion')
        numbers.append(dict(claim_id='claim-motion',slot_id='path_distance',value=motion[0]['sampled_xy_path_distance_m'],
                            unit='m',support_reference=motion[0]['evidence_id']))
    plan = dict(schema='crane-claim-realization-plan/v1',plan_id=job,diagnostic_result_sha256=canonical_sha256(result),
        required_claim_ids=selected,optional_claim_ids=[],required_non_entailment_ids=result['required_non_entailment_ids'],
        approved_numeric_values=numbers)
    clauses = [dict(clause_id='c'+str(i),kind='CLAIM',contract_id=cid,
        numeric_values=[{k:n[k] for k in ('slot_id','value','unit')} for n in numbers if n['claim_id']==cid])
        for i,cid in enumerate(selected)]
    clauses += [dict(clause_id='n'+str(i),kind='NON_ENTAILMENT',contract_id=cid,numeric_values=[])
                for i,cid in enumerate(plan['required_non_entailment_ids'])]
    candidate = dict(schema='crane-claim-realization-candidate/v1',response_id=job,plan_sha256=canonical_sha256(plan),clauses=clauses)
    realization = realize(ont,result,plan,candidate)
    if len(realization['final_response'].split()) > 60 or len(realization['final_clauses']) > 3:
        raise ValueError('unchanged common output allowance exceeded')
    return dict(answer=realization['final_response'],diagnostic_result=result,facts=facts,plan=plan,realization=realization,
                template=True,fallback=False,model_calls=0,phase='development_only')
