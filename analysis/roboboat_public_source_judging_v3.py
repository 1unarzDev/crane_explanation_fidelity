"""Source-complete common judge context; development construction only, no calls."""
import copy
import hashlib
import json
from pathlib import Path
from evidence_calibration_io import canonical_sha256
import roboboat_public_configuration_judging_v1 as configuration
import prepare_roboboat_baseline_interface_v4 as common
from run_roboboat_population_responses_v1 import BASIS, binding, checked
from run_evidence_calibration_agent_annotation import _annotation_payload

NAMESPACE='roboboat-common-public-source-judging/v3-command-shutdown-development'
SCOPE=('These are the exact common method-visible software/configuration sources, not runtime execution evidence. '
       'Compiled source correspondence does not establish scene wiring, internal observation consumption, '
       'external package semantics, deployed Nav2 source authentication or physical actuation. '
       'Distinguish source statements from runtime causal claims. Apply the same complete-answer rubric to either response.')
CONTEXT_KEYS={'schema','scope','files','source_set_sha256'}
FILE_KEYS={'relative_path','sha256','text'}
COMMON_INPUTS={'effective-configuration.yaml','public-scope.json','configuration-basis.json','robot-source-basis.json'}


def source_context(manifest_path):
    m=common.verify(manifest_path)
    sources=[*m['sources'],*[r for r in m['inputs'] if r['relative_path']!='evidence.json']]
    files=[]
    for item in sorted(sources,key=lambda r:r['relative_path']):
        path=checked(item['snapshot']);data=path.read_bytes()
        files.append({'relative_path':item['relative_path'],'sha256':hashlib.sha256(data).hexdigest(),'text':data.decode('utf-8')})
    return {'schema':NAMESPACE,'scope':SCOPE,'files':files,'source_set_sha256':canonical_sha256(files)},m


def build_packet(packet, common_manifest):
    context,m=source_context(common_manifest)
    evidence=json.loads((Path(m['workspace'])/'evidence.json').read_text())
    if any(f.get('robot_visible_evidence')!=evidence for f in packet.get('forms',[])):
        raise ValueError('common method workspace belongs to another evidence condition')
    result=configuration.build_packet(packet,BASIS)
    identity=canonical_sha256({'namespace':NAMESPACE,'original_packet':packet,'common_source_context':context})[:24]
    for form in result['forms']:
        form['public_source_context']=copy.deepcopy(context)
        form['packet_id']=identity;form['form_id']=identity+'-'+form['annotator_slot']
    validate_context(result)
    return result


def validate_context(packet):
    configuration.reject_join_metadata(packet)
    original=copy.deepcopy(packet);contexts=[f.pop('public_source_context',None) for f in original['forms']]
    if len(contexts)!=2 or contexts[0]!=contexts[1] or not isinstance(contexts[0],dict):raise ValueError('equal complete common source context required')
    c=contexts[0]
    if set(c)!=CONTEXT_KEYS or c['schema']!=NAMESPACE or c['scope']!=SCOPE or canonical_sha256(c['files'])!=c['source_set_sha256']:raise ValueError('common source context changed')
    expected_python,_=common.python_closure();expected=set(expected_python)|set(common.ROBOT_FILES)|COMMON_INPUTS
    files=c['files'];names=[f.get('relative_path') for f in files]
    if len(names)!=len(set(names)) or set(names)!=expected or names!=sorted(names):raise ValueError('exact reviewed common source/input set required')
    for item in files:
        if set(item)!=FILE_KEYS or not isinstance(item['text'],str) or hashlib.sha256(item['text'].encode('utf-8')).hexdigest()!=item['sha256']:raise ValueError('common source bytes changed')
        if item['relative_path'] in common.TREATMENT:raise ValueError('treatment source in common context')
    basis=next(f for f in files if f['relative_path']=='configuration-basis.json')
    if json.loads(basis['text'])!=BASIS:raise ValueError('public configuration basis changed')
    configuration.validate_context(original)
    return True


def annotation_payload(packet,slot):
    validate_context(packet)
    form=next(f for f in packet['forms'] if f['annotator_slot']==slot)
    return _annotation_payload(packet,form,slot)


def adjudication_payload(packet,handoff):
    validate_context(packet)
    if handoff.get('packet_id')!=packet['forms'][0]['packet_id'] or handoff.get('packet_set_sha256')!=canonical_sha256(packet):raise ValueError('adjudication source packet mismatch')
    return {'task':'BLINDED_DISAGREEMENT_ONLY_ADJUDICATION','annotation_origin':'automated_agent','agent_identity':'agent-C-astra-v4','blinded_form':packet['forms'][0],'handoff':handoff,'required_attestation':'DISAGREEMENT_ONLY_BLINDED_COMPLETE'}


def prepare(packet_path,common_manifest,target,receipt):
    packet_path,common_manifest,target,receipt=map(lambda p:Path(p).resolve(),(packet_path,common_manifest,target,receipt))
    if target.exists() or receipt.exists():raise FileExistsError('immutable source-context construction namespace required')
    packet=json.loads(packet_path.read_text());result=build_packet(packet,common_manifest)
    target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(result,indent=2)+'\n')
    # This receipt must be authenticated by any later qualified runner. In-packet
    # hashes check corruption/consistency, not independent source authenticity.
    from roboboat_runtime_source_closure_v1 import source_closure
    record={'schema':NAMESPACE,'original_packet':binding(packet_path),'common_manifest':binding(common_manifest),'new_packet':binding(target),'source_closure':[binding(p) for p in source_closure([Path(__file__)])],'source_answer_changed':False,'core_evidence_changed':False,'decision_inventory_changed':False,'calls_authorized':False,'scores_released':False,'source_context_files':len(result['forms'][0]['public_source_context']['files']),'qualification_required_before_calls':True,'qualification':'PENDING_SOURCE_COMPLETE_BALANCED_CONSTRUCTION_QUALIFICATION','confirmation_n':0,'replication_n':0,'independent_n_added':0}
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(record,indent=2)+'\n');return record


def verify_receipt(receipt_path):
    r=json.loads(Path(receipt_path).read_text())
    if r['schema']!=NAMESPACE or r['calls_authorized']is not False or r['scores_released']is not False:raise ValueError('construction-only source-context receipt required')
    for key in ('original_packet','common_manifest','new_packet'):checked(r[key])
    from roboboat_runtime_source_closure_v1 import source_closure
    expected_closure={str(p.resolve()) for p in source_closure([Path(__file__)])}
    if len(r['source_closure'])!=len(expected_closure) or {b['path'] for b in r['source_closure']}!=expected_closure:raise ValueError('complete source-context runtime closure required')
    for item in r['source_closure']:checked(item)
    original=json.loads(checked(r['original_packet']).read_text());expected=build_packet(original,checked(r['common_manifest']))
    if json.loads(checked(r['new_packet']).read_text())!=expected:raise ValueError('source context does not match authenticated common workspace')
    return r
