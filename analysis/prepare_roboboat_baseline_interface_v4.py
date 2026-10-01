"""Version-matched common baseline inputs; no model calls or readiness promotion."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from prepare_roboboat_baseline_interface_v1 import ROOT, SCOPE, HELPERS, TREATMENT as OLD_TREATMENT, ROBOT_FILES as OLD_ROBOT_FILES, python_closure, digest, binding, checked, admitted as old_admitted
from roboboat_shared_public_scope_v1 import validate_public_inputs
from roboboat_owned_player_bundle_v1 import verify_build
from run_roboboat_population_responses_v1 import BASIS

SCHEMA='roboboat-shared-diagnostics-interface/v4-command-shutdown-development'
EXPERIMENTAL_PROJECT=Path('/home/lunarz/worktrees/roboboat-command-shutdown-v17/crane_ml')
ROBOT_FILES=(*OLD_ROBOT_FILES,'packages/crane_ml/Assets/Scripts/Utils/Performance/CraneActionTimingAudit.cs',
    'packages/crane_ml/Assets/Scripts/Controllers/RoboBoatInitialPose.cs',
    'packages/crane_ml/Assets/Scripts/Performance/CraneCaptureCompletion.cs',
    'packages/crane_ml/Assets/Scripts/Performance/CraneBenchmarkRunner.cs')
TREATMENT=OLD_TREATMENT|{'analysis/roboboat_full_crane_v3.py','configs/roboboat_claim_contracts_v3_development.json'}


def admitted(relative):
    if relative in TREATMENT:raise ValueError('excluded treatment source')
    if relative in ROBOT_FILES[len(OLD_ROBOT_FILES):]:return relative
    return old_admitted(relative)


def compiled_source_bindings(audit_path, build_manifest):
    audit_path,build_manifest=Path(audit_path).resolve(),Path(build_manifest).resolve()
    a=json.loads(audit_path.read_text());manifest,build_root=verify_build(build_manifest)
    if a['schema']!='roboboat-compiled-document-source-audit/v2-development' or checked(a['build_manifest'])!=build_manifest:
        raise ValueError('compiled audit does not bind this experimental build')
    current_audit=a; seen={str(audit_path)}
    allowed_roots={
        '/home/lunarz/worktrees/roboboat-capture-complete-v15/crane_ml',
        '/home/lunarz/worktrees/roboboat-start-pose-v13/crane_ml',
        '/home/lunarz/worktrees/roboboat-episode-clock-v10/crane_ml',
        '/home/lunarz/worktrees/roboboat-action-timing-v9/crane_ml'}
    while 'original_audit' in current_audit:
        for key in ('original_audit','mapping_audit_source','parent_build_manifest'):checked(current_audit[key])
        if checked(current_audit['build_manifest'])!=build_manifest or current_audit['project']!=a['project']:
            raise ValueError('mapping chain build/project mismatch')
        if current_audit['explicit_imported_compiler_root'] not in allowed_roots:
            raise ValueError('unreviewed imported compiler root')
        previous=checked(current_audit['original_audit'])
        if str(previous) in seen:raise ValueError('cyclic mapping audit chain')
        seen.add(str(previous));current_audit=json.loads(previous.read_text())
    if checked(current_audit['build_manifest'])!=build_manifest or current_audit['project']!=a['project']:
        raise ValueError('original mapping chain build/project mismatch')
    checked(current_audit['utility'])
    if a['explicit_imported_compiler_root']!='/home/lunarz/worktrees/roboboat-start-pose-v13/crane_ml':raise ValueError('unexpected imported compiler root')
    project=Path(a['project']).resolve()
    if project!=EXPERIMENTAL_PROJECT or build_root!=project/'Builds/CRANE-Worker':raise ValueError('v4 common inputs require the declared command-shutdown-v17 platform')
    files={r['path']:r['sha256'] for r in manifest['full_build_files']}
    result=[]
    for relative in ROBOT_FILES:
        source=project/relative.removeprefix('packages/crane_ml/')
        hits=[(r,d) for r in a['records'] for d in r.get('source_documents',[]) if d.get('relative')==relative.removeprefix('packages/crane_ml/')]
        if not hits:raise ValueError('missing compiled common source: '+relative)
        for record,document in hits:
            metadata=record.get('metadata',{})
            if record['status']!='MATCHED_METADATA' or document['status']!='MATCH' or checked(document['source'])!=source.resolve():
                raise ValueError('unqualified compiled common source: '+relative)
            doc=document['document']
            if 'compiler_source' in document:
                compiler=checked(document['compiler_source'])
                if str(compiler)!=doc['name'] or compiler.read_bytes()!=source.read_bytes():raise ValueError('imported compiler source mapping differs')
            algorithm={'8829d00f-11b8-4213-878b-770e8597ac16':'sha256','ff1816ec-aa5e-4d10-87f7-6f4963833460':'sha1'}.get(doc['algorithm'])
            if algorithm is None or doc not in metadata['documents'] or hashlib.new(algorithm,source.read_bytes()).hexdigest()!=doc['checksum']:
                raise ValueError('compiled document checksum mismatch')
            for kind in ('assembly','pdb'):
                path=Path(metadata[kind]).resolve()
                if not path.is_relative_to(build_root) or files.get(path.relative_to(build_root).as_posix())!=metadata[kind+'_sha256'] or digest(path)!=metadata[kind+'_sha256']:
                    raise ValueError('compiled metadata/build identity mismatch')
            if metadata['assembly_pdb_identity_match']is not True or metadata['pe_pdb_checksum_match']is not True:
                raise ValueError('unqualified PE/PDB identity')
        result.append({'relative_path':relative,'original':binding(source),'compiled_occurrences':len(hits)})
    return result


def prepare(packet_path,configuration_path,output_root,*,compiled_audit,build_manifest):
    packet_path,configuration_path,output_root=map(lambda p:Path(p).resolve(),(packet_path,configuration_path,output_root))
    if output_root.exists():raise FileExistsError('immutable common-interface namespace required')
    validation=validate_public_inputs(json.loads(packet_path.read_text()),configuration_path.read_bytes())
    robots=compiled_source_bindings(compiled_audit,build_manifest);python_sources,external=python_closure()
    sources=[{'relative_path':r,'original':binding(ROOT/r)} for r in python_sources]+robots
    for item in sources:admitted(item['relative_path'])
    output_root.mkdir(parents=True,exist_ok=False);workspace=output_root/'workspace';workspace.mkdir()
    for item in sources:
        target=workspace/item['relative_path'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked(item['original']),target);target.chmod(0o444);item['snapshot']=binding(target)
    inputs=[]
    for source,name in ((packet_path,'evidence.json'),(configuration_path,'effective-configuration.yaml'),(SCOPE,'public-scope.json')):
        target=workspace/name;shutil.copyfile(source,target);target.chmod(0o444);inputs.append({'relative_path':name,'original':binding(source),'snapshot':binding(target)})
    public_basis={'schema':'roboboat-common-robot-source-basis/v1','sources':[{'relative_path':r['relative_path'],'sha256':r['original']['sha256'],'compiled_document_identity_verified':True} for r in robots],
        'experimental_version':'isolated command-shutdown-v17; EpisodeId-bound publisher scheduling, opt-in initial pose and capture completion, explicit command intake closure before counters; .02 fixed step; .04 catch-up cap',
        'deployment_wiring_proven':False,'external_package_and_reflective_closure_authenticated':False,'nav2_deployed_source_authenticated':False}
    for name,value in (('configuration-basis.json',BASIS),('robot-source-basis.json',public_basis)):
        target=workspace/name;target.write_text(json.dumps(value,indent=2)+'\n');target.chmod(0o444);inputs.append({'relative_path':name,'snapshot':binding(target),'generated_common_value':value})
    manifest={'schema':SCHEMA,'status':'VERSION_MATCHED_COMMON_INPUTS_PREPARED_READINESS_INCOMPLETE','workspace':str(workspace),
        'sources':sources,'inputs':inputs,'public_input_validation':validation,'configuration_basis':BASIS,
        'compiled_audit':binding(compiled_audit),'build_manifest':binding(build_manifest),
        'preparation_source':binding(__file__),'preparation_parent':binding(ROOT/'analysis/prepare_roboboat_baseline_interface_v1.py'),
        'basis_source':binding(ROOT/'analysis/run_roboboat_population_responses_v1.py'),
        'common_robot_source_project':json.loads(Path(compiled_audit).read_text())['project'],'compiled_common_sources':len(robots),
        'local_import_requirements':external,'comparison_scope':'Full CRANE versus shared diagnostic helpers and own agent reasoning; current generic robot sources and configuration basis available equally.',
        'no_method_outputs_staged':True,'packet_platform_authenticated':False,'operational_platform_qualified_by_preparation':False,'deployment_wiring_proven':False,'external_source_closure_authenticated':False,
        'nav2_deployed_source_authentication':'NOT_AUTHENTICATED','actual_provider_tool_scratch_capability':'PENDING',
        'call_readiness':False,'baseline_promotion':False,'confirmation_n':0,'replication_n':0}
    (output_root/'interface-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    verify(output_root/'interface-manifest.json');return manifest


def verify(manifest_path):
    manifest_path=Path(manifest_path).resolve();m=json.loads(manifest_path.read_text())
    if m['schema']!=SCHEMA or m['call_readiness']is not False or m.get('packet_platform_authenticated')is not False or m.get('operational_platform_qualified_by_preparation')is not False:raise ValueError('prepared development interface only')
    for k in ('preparation_source','preparation_parent','basis_source','compiled_audit','build_manifest'):checked(m[k])
    qualified=compiled_source_bindings(checked(m['compiled_audit']),checked(m['build_manifest']))
    originals={r['relative_path']:r['original'] for r in m['sources']}
    if any(originals.get(r['relative_path'])!=r['original'] for r in qualified):raise ValueError('common robot source is not from the qualified experimental version')
    expected_python,_=python_closure();expected_sources=set(expected_python)|set(ROBOT_FILES)
    if len(m['sources'])!=len(expected_sources) or {r['relative_path'] for r in m['sources']}!=expected_sources:raise ValueError('exact reviewed common source closure required')
    expected_inputs={'evidence.json','effective-configuration.yaml','public-scope.json','configuration-basis.json','robot-source-basis.json'}
    if len(m['inputs'])!=len(expected_inputs) or {r['relative_path'] for r in m['inputs']}!=expected_inputs:raise ValueError('exact common public input set required')
    workspace=Path(m['workspace']).resolve()
    if {p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file()}!=expected_sources|expected_inputs:raise ValueError('undeclared source/output in common workspace')
    for item in m['sources']+m['inputs']:
        snapshot=checked(item['snapshot'])
        if snapshot!=workspace/item['relative_path']:raise ValueError('snapshot path mismatch')
        if 'original' in item and snapshot.read_bytes()!=checked(item['original']).read_bytes():raise ValueError('snapshot bytes differ')
        if 'generated_common_value' in item and json.loads(snapshot.read_text())!=item['generated_common_value']:raise ValueError('common generated basis differs')
    expected_robot_basis={'schema':'roboboat-common-robot-source-basis/v1', 'sources':[{'relative_path':r['relative_path'],'sha256':r['original']['sha256'],'compiled_document_identity_verified':True} for r in qualified],
        'experimental_version':'isolated command-shutdown-v17; EpisodeId-bound publisher scheduling, opt-in initial pose and capture completion, explicit command intake closure before counters; .02 fixed step; .04 catch-up cap',
        'deployment_wiring_proven':False,'external_package_and_reflective_closure_authenticated':False,'nav2_deployed_source_authenticated':False}
    if json.loads((workspace/'robot-source-basis.json').read_text())!=expected_robot_basis:raise ValueError('common robot source basis changed')
    if json.loads((workspace/'configuration-basis.json').read_text())!=BASIS:raise ValueError('common configuration basis changed')
    if (workspace/'public-scope.json').read_bytes()!=SCOPE.read_bytes():raise ValueError('common public scope changed')
    validate_public_inputs(json.loads((workspace/'evidence.json').read_text()),(workspace/'effective-configuration.yaml').read_bytes())
    return m

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--packet',type=Path,required=True);p.add_argument('--configuration',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--compiled-audit',type=Path,required=True);p.add_argument('--build-manifest',type=Path,required=True);a=p.parse_args()
    m=prepare(a.packet,a.configuration,a.output,compiled_audit=a.compiled_audit,build_manifest=a.build_manifest)
    print(json.dumps({'status':m['status'],'compiled_common_sources':m['compiled_common_sources'],'call_readiness':m['call_readiness']}))
