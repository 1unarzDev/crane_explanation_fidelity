"""Prepare balanced source-scope construction probes; no model calls or scoring."""
import argparse
import json
from pathlib import Path
import random
from evidence_calibration_io import canonical_sha256
from roboboat_public_source_judging_v3 import source_context, NAMESPACE
from run_roboboat_population_responses_v1 import binding, BASIS
from build_atomic_claim_annotation_packets import LABELS


def prepare(manifest_path,output):
    manifest_path,output=Path(manifest_path).resolve(),Path(output).resolve()
    if output.exists():raise FileExistsError('immutable qualification candidate namespace required')
    context,m=source_context(manifest_path);evidence=json.loads((Path(m['workspace'])/'evidence.json').read_text())
    files={f['relative_path']:f for f in context['files']}
    command='packages/crane_ml/Assets/Scripts/Controllers/ROSOmniXCommand.cs'
    publisher='packages/crane_ml/Assets/Scripts/Controllers/CraneROSNavigationState.cs'
    for relative,fragment in [(command,'pending.TryApply(SetDesiredVelocity'),(command,'desiredVelocity = command;'),(command,'pending.Receive(command'),(publisher,'nextPublishTime = 0;'),(publisher,'publisherEpisodeId != CraneRuntimeMetrics.EpisodeId')]:
        if fragment not in files[relative]['text']:raise ValueError('qualified source seam changed')
    velocity=evidence['configuration']['trans_stopped_velocity'];wrong=velocity+1
    supported='SUPPORTED_BY_VISIBLE_EVIDENCE';insufficient='INSUFFICIENT_VISIBLE_EVIDENCE';contradicted='CONTRADICTED_BY_VISIBLE_EVIDENCE'
    cases=[
        (f'The supplied configuration sets trans_stopped_velocity to {velocity:g}.',supported,'effective-configuration.yaml','Exact supplied configured value; no internal-consumption claim.'),
        (f'The supplied configuration sets trans_stopped_velocity to {wrong:g}.',contradicted,'effective-configuration.yaml','Wrong configured value is contradicted, not merely an unknown runtime fact.'),
        ('The supplied basis identifies goal-checker values as pre-action node/plugin-specific ROS readback.',supported,'configuration-basis.json','Readback provenance is explicitly supplied.'),
        ('The controller internally consumed the delivered odometry because these goal-checker settings were read back.',insufficient,'configuration-basis.json','Readback does not establish internal consumption.'),
        ('In the supplied ROSOmniXCommand implementation, Receive queues the command via pending.Receive.',supported,command,'Source-level implementation statement; no episode execution asserted.'),
        ('The thrusters successfully executed every command in this episode exactly as it arrived on ROS.',insufficient,command,'No runtime command/payload-to-physics linkage is supplied; source code is insufficient.'),
        ('In this implementation, SetDesiredVelocity stores the command and marks desired velocity present; subsequent control work is separate.',supported,command,'Assignments are in the callback; ApplyVelocityControl occurs separately in FixedUpdate.'),
        ('Completion of SetDesiredVelocity establishes that the motors achieved the requested physical motion.',insufficient,command,'Desired-velocity state is not physical response evidence.'),
        ('The supplied navigation-state publisher resets nextPublishTime when the episode identity changes.',supported,publisher,'The explicit epoch check and reset are in the reviewed source.'),
        ('There was a warmup odometry publication gap during this particular episode.',insufficient,publisher,'Source behavior does not establish this episode timeline; no publication trace is in the common packet.'),
        ('The supplied source basis does not authenticate external/reflected closure or deployed Nav2 source.',supported,'robot-source-basis.json','Explicit scope limits are false authentication flags.'),
        ('The supplied source basis authenticates every external package and the deployed Nav2 implementation.',contradicted,'robot-source-basis.json','The supplied metadata explicitly disclaims those authentication claims.'),
    ]
    random.Random(43104).shuffle(cases);output.mkdir();inputs=output/'blind_inputs';inputs.mkdir();key=[]
    for claim,label,anchor,reason in cases:
        identifier=canonical_sha256({'namespace':NAMESPACE,'claim':claim,'source_set':context['source_set_sha256']})[:24]
        value={'schema':'roboboat-source-scope-construction-probe/v3','task':'NON_STUDY_SOURCE_SCOPE_QUALIFICATION','claim':claim,'allowed_claim_labels':LABELS,'robot_visible_evidence':evidence,'configuration_basis':BASIS,'public_source_context':context,'instruction':'Classify the claim using only supplied public evidence and common sources. Distinguish source statements, configured settings and episode execution. Do not infer runtime consumption, causation or physical actuation from source correspondence. This is construction qualification, not a study answer or method comparison.'}
        target=inputs/(identifier+'.json');target.write_text(json.dumps(value,indent=2)+'\n')
        key.append({'opaque_probe_id':identifier,'expected_label':label,'source_anchor':anchor,'root_source_audit_reason':reason,'input':binding(target)})
    private=output/'evaluator-key.json';private.write_text(json.dumps({'schema':'roboboat-source-scope-qualification-key/v3','review_origin':'root engineering/source audit; not independent model or human review','entries':key},indent=2)+'\n')
    from roboboat_runtime_source_closure_v1 import source_closure
    lock={'schema':'roboboat-source-scope-qualification-preparation/v3','status':'PREPARED_UNEXECUTED_UNQUALIFIED','common_manifest':binding(manifest_path),'evaluator_only_key':binding(private),'blind_inputs':[r['input'] for r in key],'source_closure':[binding(p) for p in source_closure([Path(__file__)])],'cases':12,'label_balance':{supported:6,insufficient:4,contradicted:2},'primary_endpoint_qualification':'This only exercises source/context use. It supplements, never replaces, the existing complete-supported-diagnostic-answer/rubric qualification cases. Full endpoint reliability remains unqualified.','planned_procedure':'Fresh independently isolated A/B model passes, complete source audit, disagreement-only adjudication; no outcome-driven repair or retries of governed attempts. Bind the final procedure/transport/acceptance criteria in a separate declaration before calls.','calls_authorized_by_this_preparation':False,'calls_executed':0,'scores_released':False,'independent_n_added':0,'confirmation_n':0,'replication_n':0}
    (output/'preparation-lock.json').write_text(json.dumps(lock,indent=2)+'\n');return lock

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--common-manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args();value=prepare(a.common_manifest,a.output);print(json.dumps({'status':value['status'],'cases':value['cases'],'calls':value['calls_executed']}))
