"""Universal removal-only navigation packets and a thin pinned-core adapter.

Only recorded task/log/indicator facts enter production. Scenario/gold/performance
fields are not read here. One mask rule is used for every recording and question.
"""
import copy
import json
import re
import sys
from pathlib import Path
from audit_release import ROOT,sha,write
from replay import replay
from contract_adapter import check_core_pin
sys.path.insert(0,str(ROOT/'analysis'))
from evidence_calibration_io import canonical_sha256,ontology_from_dict
from maximal_supported_diagnosis import diagnose
from realize_evidence_calibrated_explanation import realize
V2=ROOT/'data/hexar_external/v2'
CONDITIONS=('intact','irrelevant_removal','diagnostic_removal')
SAFE_LOGS={'SkillNavigateToZone received a new goal','Waiting for NavigateToZone to finish...',
 'SkillNavigateToPose received a new goal','Waiting for NavigateToPose to finish...',
 'Skill completed successfully'}

def transform(events,condition):
    retained=[];removed=[];field_removals=[]
    for e in events:
        remove=False
        if condition=='irrelevant_removal':remove=e['topic']=='/rosout' and e['value']['name']=='rosbag2_recorder'
        elif condition=='diagnostic_removal':
            if e['topic'] in ('/joy_priority','/power/is_charging','/amcl_pose'):remove=True
            elif e['topic']=='/rosout':
                # Whitelist generic skill execution wrappers only; no arbitrary diagnostic aliases survive.
                remove=not (e['value']['name'] in ('skill_navigate_to_zone','skill_navigate_to_pose') and
                    (e['value']['msg'] in SAFE_LOGS or re.fullmatch(r'NavigateTo(?:Zone|Pose) action server returned code: \d+',e['value']['msg'])))
        if remove:removed.append(e['event_id']);continue
        out=copy.deepcopy(e)
        if condition=='diagnostic_removal' and e['topic']=='/task_info':
            task=json.loads(out['value']['data'])
            if task.get('task_error_msg') not in ('',None):
                task['task_error_msg']=None;field_removals.append(e['event_id']+'/task_error_msg')
            for i,s in enumerate(task['skill_sequence']):
                # Preserve timeout/abort as execution outcomes, not a physical mechanism.
                if s.get('error_msg') not in ('',None,'The skill has timed out','The skill has been aborted'):
                    s['error_msg']=None;field_removals.append(f"{e['event_id']}/skill_sequence/{i}/error_msg")
            out['value']['data']=json.dumps(task)
        retained.append(out)
    return retained,removed,field_removals

def build_packet(events,question,condition):
    transformed,removed,fields=transform(events,condition)
    snap=replay(transformed,question);lo,hi=map(float,snap['task_window'])
    logs=[x for x in snap['logs'] if lo<=float(x['timestamp'])<=hi]
    logfacts=[{'evidence_id':f'l{i:04d}','logger':x['name'],'message':x['msg'],'callback_time':x['timestamp']} for i,x in enumerate(logs)]
    task=copy.deepcopy(snap['task']);task['task_id']='task-opaque'
    nav=[(i,s) for i,s in enumerate(task['skill_sequence']) if s['skill']=='navigate_to_zone']
    outcomes=[{'evidence_id':f's{i:04d}','skill':s['skill'],'status':s['status'],'error_msg':s['error_msg']} for i,s in nav if s['status'].lower() in ('failed','succeeded')]
    def state(topic):
        records=[e for e in transformed if e['topic']==topic]
        return [] if not records else [{'evidence_id':'state-'+topic.strip('/').replace('/','-'),
             'value':records[-1]['value']['data'],'receipt_ns':records[-1]['recorded_ns'],
             'scope':'latest received indicator before explanation; upstream state is not time-filtered'}]
    evidence={'navigation_logs':logfacts,'navigation_outcomes':outcomes,'manual_state':state('/joy_priority'),
        'charging_state':state('/power/is_charging'),
        'recorded_task':[{'evidence_id':'task-latest','value':task}]}
    pkt={'schema':'hexar-permitted-method-packet/v2','question':question,'task_window':snap['task_window'],
      'evidence':evidence,'availability':{k:'present' if v else 'unavailable' for k,v in evidence.items()},
      'diagnostic_channels':{'manual':bool(evidence['manual_state']),'charging':bool(evidence['charging_state']),
          'localization_samples':any(e['topic']=='/amcl_pose' for e in transformed),
          'planner_controller_logs':any(e['topic']=='/rosout' and e['value']['name'] in ('planner_server','controller_server') for e in transformed)},
      'source_context':{
        'indicator_semantics':'The released component treats /joy_priority as manual mode and /power/is_charging as charging. No governing robot controller/arbitration source or applied-motion measurement is supplied.',
        'localization_semantics':'The original callback appends a high-uncertainty diagnostic after its count exceeds five samples with mean XY covariance or orientation variance above .2. Its count decrements on low samples; this is preserved, not a new localization detector.',
        'event_scope':'Planner/progress failure and clearing-request logs are software execution evidence, not direct geometry or unique physical causes. No supplied costmap/scan/path measurement proves an obstacle or moving obstacle. A clearing request does not prove completed clearing.',
        'timing_scope':'Requested window follows upstream task bookkeeping and its sec.nanosec conversion. A recorded navigation success does not establish a safety-speed policy or a measured cause of slowness.',
        'missingness':'Unavailable evidence is unknown; do not replace it with false, zero, success or normal behavior.'},
      'public_communication_requirements':{
        'useful_outcome':'Report the supported navigation outcome, if present; preserve timeout/abort only when explicit.',
        'useful_diagnosis':'If retained observations show manual/charging selection, localization uncertainty or planner/progress trouble, preserve at least one useful bounded fact rather than blanket refusal.',
        'scope':'Separate observed execution facts from unique physical causation and measured reasons for delay. Explicit uncertainty OR clearly source-bounded observation language is acceptable.',
        'extra_details':'Additional supported details are welcome, without requiring timestamps or exhaustive lists.'}}
    if condition=='diagnostic_removal':
        assert snap['is_joystick_manual'] is None and snap['is_charging'] is None
        assert not any(e['topic'] in ('/joy_priority','/power/is_charging','/amcl_pose') for e in transformed)
        assert not any(l['logger'] in ('planner_server','controller_server','amcl_pose','local_costmap.local_costmap','global_costmap.global_costmap') for l in logfacts)
    return pkt,snap,{'removed_event_ids':removed,'removed_fields':fields,'retained_events':len(transformed),
       'transformed_sha256':canonical_sha256(transformed),'fresh_state':True,
       'no_missing_state_to_false':snap['is_joystick_manual'] is None if condition=='diagnostic_removal' else True}

SPECS=[
 ('failure','navigation_outcomes','Recorded navigation ended in failure.','TASK_OUTCOME'),
 ('success','navigation_outcomes','The recorded navigation skills succeeded.','TASK_OUTCOME'),
 ('timeout','navigation_outcomes','The navigation skill reported a timeout.','TASK_OUTCOME'),
 ('abort','navigation_outcomes','The navigation skill reported an abort.','TASK_OUTCOME'),
 ('manual','manual_state','The latest received joystick-priority indicator was on.','OBSERVATION'),
 ('charging','charging_state','The latest received charging indicator was on.','OBSERVATION'),
 ('uncertainty','navigation_logs','The recorded pose estimate showed high localization uncertainty.','OBSERVATION'),
 ('planner','navigation_logs','The planner reported that it could not generate a valid path.','SOFTWARE_ACTION'),
 ('progress','navigation_logs','The controller reported failure to make progress.','SOFTWARE_ACTION'),
 ('physical','physical_cause_measurement','A unique physical cause was established.','SPECIFIC_PHYSICAL_CAUSE')]

def ontology():
    reqs=[];claims=[];nodes=[]
    for name,role,text,kind in SPECS:
        reqs.append({'requirement_id':'req-'+name,'evidence_roles':[role],
          'predicate_id':'hexar-visible-'+name,'predicate_version':'v2','description':'Recorded source-qualified '+name+' evidence; missing is unknown.'})
        claims.append({'claim_id':'claim-'+name,'proposition':text,'mechanism_family':'navigation','claim_kind':kind,
          'diagnostic_node_id':'node-'+name,'required_evidence_ids':['req-'+name],
          'non_entailment_ids':['limit-physical-and-delay'] if name!='physical' else []})
        nodes.append({'node_id':'node-'+name,'mechanism_family':'navigation','label':name,'rank_within_family':2 if name=='physical' else 0,
          'parent_node_ids':['node-failure'] if name=='physical' else [],'claim_ids':['claim-'+name]})
    ont={'schema':'crane-evidence-calibration-ontology/v1','catalog_id':'hexar-navigation-public-v2','catalog_version':'v2',
      'evidence_requirements':reqs,'claim_contracts':claims,'diagnostic_nodes':nodes,
      'non_entailments':[{'non_entailment_id':'limit-physical-and-delay','basis_claim_ids':['claim-'+s[0] for s in SPECS if s[0]!='physical'],
        'unsupported_consequent_claim_ids':['claim-physical'],'additional_evidence_requirement_ids':['req-physical'],
        'rationale':'These records do not establish a unique physical cause or a measured reason for navigation time.'}]}
    ontology_from_dict(ont);return ont

def primitive_bindings(packet):
    e=packet['evidence'];logs=e['navigation_logs'];out=e['navigation_outcomes'];task=e['recorded_task'][0]['value']
    nav=[s for s in task['skill_sequence'] if s['skill']=='navigate_to_zone']
    refs={key:[] for key,_,_,_ in SPECS}
    refs['failure']=[r['evidence_id'] for r in out if r['status'].lower()=='failed']
    refs['success']=[r['evidence_id'] for r in out if r['status'].lower()=='succeeded'] if nav and all(s['status'].lower()=='succeeded' for s in nav) else []
    refs['timeout']=[r['evidence_id'] for r in out if r['status'].lower()=='failed' and 'timed out' in (r['error_msg'] or '').lower()]
    refs['abort']=[r['evidence_id'] for r in out if r['status'].lower()=='failed' and 'aborted' in (r['error_msg'] or '').lower()]
    for key in ('manual','charging'):refs[key]=[r['evidence_id'] for r in e[key+'_state'] if r['value'] is True]
    refs['uncertainty']=[r['evidence_id'] for r in logs if r['logger']=='amcl_pose' and r['message']=="High uncertainty in the robot's position."]
    refs['planner']=[r['evidence_id'] for r in logs if r['logger']=='planner_server' and ('failed to create plan' in r['message'].lower() or 'failed to generate a valid path' in r['message'].lower())]
    refs['progress']=[r['evidence_id'] for r in logs if r['logger']=='controller_server' and r['message']=='Failed to make progress']
    return refs

def contract(packet,job,recording):
    check_core_pin();ont=ontology();refs=primitive_bindings(packet)
    ids=sorted({r['evidence_id'] for rows in packet['evidence'].values() for r in rows})
    cond={'condition_id':job,'episode_id':recording,'configuration_id':'hexar-navigation-component-v2',
      'method_packet_sha256':canonical_sha256(packet),'available_evidence_ids':ids}
    facts={'schema':'crane-visible-evidence-requirement-facts/v1','condition_id':job,'method_packet_sha256':canonical_sha256(packet),
      'question_contract':{'question_id':canonical_sha256(packet['question'])[:16],'failure_premise':False,'required_mechanism_families':['navigation']},
      'requirement_evaluations':[{'requirement_id':'req-'+key,'status':'SATISFIED' if v else 'ABSENT','support_references':v,
       'detail':'Deterministic positive evidence predicate; absence never proves normality.'} for key,v in refs.items()],
      'ambiguity_node_ids':[]}
    result=diagnose(ont,{'condition':cond,'method_packet':packet},facts)
    outcome=next((k for k in ('timeout','abort','failure','success') if refs[k]),None)
    if outcome is None:raise ValueError('No terminal navigation outcome: technical eligibility must be recorded.')
    salient=next((k for k in ('manual','charging','uncertainty','planner','progress') if refs[k]),None)
    selected=['claim-'+outcome]+(['claim-'+salient] if salient else [])
    plan={'schema':'crane-claim-realization-plan/v1','plan_id':job,'diagnostic_result_sha256':canonical_sha256(result),
      'required_claim_ids':selected,'optional_claim_ids':[],'required_non_entailment_ids':result['required_non_entailment_ids'],'approved_numeric_values':[]}
    clauses=[{'clause_id':f'c{i}','kind':'CLAIM','contract_id':cid,'numeric_values':[]} for i,cid in enumerate(selected)]
    clauses +=[{'clause_id':f'n{i}','kind':'NON_ENTAILMENT','contract_id':cid,'numeric_values':[]} for i,cid in enumerate(plan['required_non_entailment_ids'])]
    candidate={'schema':'crane-claim-realization-candidate/v1','response_id':job,'plan_sha256':canonical_sha256(plan),'clauses':clauses}
    realization=realize(ont,result,plan,candidate)
    if len(realization['final_response'].split())>60:raise ValueError('Common output allowance exceeded')
    return {'answer':realization['final_response'],'diagnostic_result':result,'facts':facts,'realization':realization,
       'template':True,'fallback':False,'model_calls':0}
