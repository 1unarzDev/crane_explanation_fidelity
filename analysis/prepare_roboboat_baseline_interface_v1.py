#!/usr/bin/env python3
"""Immutable shared-diagnostics architecture input preparation; no study calls."""
import argparse
import ast
import hashlib
import json
import re
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys

from roboboat_shared_public_scope_v1 import validate_public_inputs

ROOT = Path(__file__).resolve().parents[1]
SCOPE = ROOT/'docs/roboboat_terminal_evidence/shared_public_scope_v1.json'
SCHEMA = 'roboboat-shared-diagnostics-interface/v1-development'
HELPERS = tuple('analysis/'+name for name in (
    'roboboat_temporal_certificate.py', 'roboboat_temporal_certificate_v2.py',
    'roboboat_temporal_renderer_v2.py', 'roboboat_temporal_renderer_v3.py',
    'roboboat_temporal_renderer_v4.py'))
TREATMENT = frozenset(('analysis/roboboat_full_crane_v1.py', 'analysis/roboboat_full_crane_v2.py',
    'analysis/maximal_supported_diagnosis.py', 'analysis/realize_evidence_calibrated_explanation.py',
    'analysis/evidence_calibration.py', 'analysis/evidence_calibration_io.py',
    'configs/roboboat_claim_contracts_v1_development.json',
    'configs/roboboat_claim_contracts_v2_development.json'))
# Reviewed common robot source candidates and their conservative local symbol
# dependencies. Shared Utils references land types, so those dependencies remain
# visible; no scene, instance asset, evaluator, raw log or episode result is copied.
ROBOT_FILES = tuple('packages/crane_ml/Assets/Scripts/'+name for name in (
    'Actuators/Motors/IMotorConfig.cs','Actuators/Motors/MotorBase.cs',
    'Actuators/Motors/ROSThruster.cs','Actuators/Motors/Thruster.cs','Actuators/Motors/ThrusterConfig.cs',
    'Controllers/AckermanController.cs','Controllers/CraneROSNavigationState.cs',
    'Controllers/IControllerBase.cs','Controllers/OmniXController.cs','Controllers/ROSOmniXCommand.cs',
    'Physics/Land/AckermannRoverDynamics.cs','Physics/Land/DifferentialDriveDynamics.cs',
    'Physics/Land/ROSAckermannCommand.cs','Physics/Land/ROSDifferentialCommand.cs',
    'Physics/Processing/Patch.cs','Physics/Processing/SubmersionLib.cs','Physics/Processing/WaterUtils.cs',
    'Sensors/IROSSensor.cs','Sensors/Nav/Odom.cs','Utils/ArticulationBodyAdapter.cs',
    'Utils/Constants.cs','Utils/IPhysicsBody.cs','Utils/PID.cs','Utils/Performance/CraneActionGate.cs',
    'Utils/Performance/CraneEpisodeReset.cs','Utils/Performance/CraneObservationJournal.cs',
    'Utils/Performance/CraneProfiler.cs','Utils/Performance/CraneSimulationClock.cs',
    'Utils/ROS/Clock.cs','Utils/ROS/ROSClock.cs','Utils/ROS/ROSPublisher.cs',
    'Utils/ROS/ROSSubscriber.cs','Utils/RigidbodyAdapter.cs','Utils/Utils.cs'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    return {'path':str(Path(path).resolve()),'sha256':digest(path)}


def checked(value):
    path=Path(value['path'])
    if digest(path)!=value['sha256']: raise ValueError('immutable input changed: '+str(path))
    return path


def admitted(relative):
    path=Path(relative)
    if path.is_absolute() or '..' in path.parts or relative in TREATMENT:
        raise ValueError('excluded treatment/path source: '+relative)
    lowered=relative.lower()
    if any(token in lowered for token in ('reference_', 'evaluator','judge','candidate_outputs','/responses/','gold')):
        raise ValueError('excluded evaluator/output source: '+relative)
    if relative not in (*HELPERS,'analysis/roboboat_shared_public_scope_v1.py') and relative not in ROBOT_FILES:
        raise ValueError('source outside reviewed common source namespace: '+relative)
    return relative


def python_closure(roots=None):
    pending=list(roots or (*HELPERS,'analysis/roboboat_shared_public_scope_v1.py'))
    closure=set(); external=set()
    while pending:
        relative=admitted(pending.pop())
        if relative in closure: continue
        path=ROOT/relative
        if path.resolve().parent!=ROOT/'analysis': raise ValueError('unexpected Python source location')
        closure.add(relative)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.module:
                names=[node.module.split('.')[0]]
            elif isinstance(node,ast.Import): names=[item.name.split('.')[0] for item in node.names]
            else: continue
            for name in names:
                local='analysis/'+name+'.py'
                if (ROOT/local).is_file(): pending.append(local)
                else: external.add(name)
    if not set(HELPERS)<=closure: raise ValueError('all five legacy diagnostic helpers required')
    return sorted(closure),sorted(external)


def robot_symbol_graph():
    """Conservative source-token resolution, not a C# compiler/deployment proof."""
    texts={path:(ROOT/path).read_text() for path in ROBOT_FILES}
    definitions={}
    for path,text in texts.items():
        for name in re.findall(r'\b(?:class|struct|interface|enum)\s+(\w+)',text):
            definitions.setdefault(name,set()).add(path)
    graph={}
    for path,text in texts.items():
        code=re.sub(r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"','',text)
        graph[path]=sorted({target for name in set(re.findall(r'\b\w+\b',code))
                            for target in definitions.get(name,()) if target!=path})
    return {'method':'Conservative identifier matching within reviewed local declarations; not compiled or reflective closure.',
            'dependencies':graph,'external_package_and_reflective_closure_authenticated':False}


def build_source_audit(build_manifest):
    if build_manifest is None:
        return {'status':'BUILD_SOURCE_AUTHENTICATION_PENDING','matched_common_sources':[],
                'missing_common_sources':list(ROBOT_FILES),'mismatched_common_sources':[]}
    path=Path(build_manifest).resolve(); manifest=json.loads(path.read_text())
    if manifest['schema']!='crane-build-manifest-v1': raise ValueError('unsupported build manifest')
    assets={row['path']:row for row in manifest['assets']}
    matched,missing,mismatched=[],[],[]
    for relative in ROBOT_FILES:
        asset=assets.get(relative.removeprefix('packages/crane_ml/'))
        if asset is None: missing.append(relative)
        elif digest(ROOT/relative)==asset['sha256'].lower(): matched.append(relative)
        else: mismatched.append(relative)
    return {'status':'SOURCE_LIST_COMPARISON_ONLY_NOT_DEPLOYMENT_AUTHENTICATION',
            'build_manifest':binding(path),'build_guid':manifest['buildGuid'],
            'unity_version':manifest['unityVersion'],'matched_common_sources':matched,
            'missing_common_sources':missing,'mismatched_common_sources':mismatched,
            'limitations':['Scene dependency manifest can omit RuntimeInitialize sources.',
                          'SourceCommit/sourceDirty defaults are not proof of source provenance.',
                          'Source list comparison does not bind deployed managed assemblies or Nav2.']}


def prepare(packet_path, configuration_path, output_root, *, build_manifest=None):
    packet_path,configuration_path,output_root=map(lambda p:Path(p).resolve(),
                                                 (packet_path,configuration_path,output_root))
    if output_root.exists(): raise FileExistsError('immutable interface namespace already exists')
    packet=json.loads(packet_path.read_text()); configuration=configuration_path.read_bytes()
    validation=validate_public_inputs(packet,configuration)
    python_sources,external=python_closure()
    sources=[*python_sources,*ROBOT_FILES]
    for relative in sources: admitted(relative)
    audit=build_source_audit(build_manifest)
    # The public specification is a generic scope contract, with no case-specific
    # inventory, approved claims, diagnostic plan, judge references or answer.
    scope=json.loads(SCOPE.read_text())
    if scope['schema']!='roboboat-shared-public-scope/v1-development': raise ValueError('public scope changed')
    output_root.mkdir(parents=True,exist_ok=False); workspace=output_root/'workspace';workspace.mkdir()
    copied=[]
    for relative in sources:
        source=ROOT/relative;target=workspace/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target);target.chmod(0o444)
        copied.append({'relative_path':relative,'original':binding(source),'snapshot':binding(target)})
    inputs=[]
    for source,name in ((packet_path,'evidence.json'),(configuration_path,'effective-configuration.yaml'),
                        (SCOPE,'public-scope.json')):
        target=workspace/name;shutil.copyfile(source,target);target.chmod(0o444)
        inputs.append({'relative_path':name,'original':binding(source),'snapshot':binding(target)})
    manifest={'schema':SCHEMA,'status':'DEVELOPMENT_INTERFACE_PREPARED_READINESS_INCOMPLETE',
        'namespace':'shared-marine-diagnostics-architecture-v1','workspace':str(workspace),
        'sources':copied,'inputs':inputs,'preparation_source':binding(__file__),
        'preparation_tests':binding(ROOT/'tests/test_prepare_roboboat_baseline_interface_v1.py'),
        'scope_tests':binding(ROOT/'tests/test_roboboat_shared_public_scope_v1.py'),
        'public_input_validation':validation,'robot_source_build_audit':audit,
        'local_import_requirements':external,
        'observed_preparation_runtime':{'python':sys.version.split()[0], 'PyYAML':importlib.metadata.version('PyYAML'),
            'actual_provider_workspace_runtime_verified':False},
        'robot_local_symbol_resolution':robot_symbol_graph(),
        'external_source_scope':'Unity/ROS-TCP/HDRP dependencies are not claimed source-authenticated by this local C# candidate bundle.',
        'nav2_deployed_source_authentication':{'status':'NOT_AUTHENTICATED',
            'reason':'Installed controller/action/goal-checker source/version and its link to the deployed worker image are not supplied.'},
        'capability_checks':{'local_helper_imports':'TESTED_IN_CONSTRUCTION_ONLY',
            'actual_transport_inline_python':'PENDING','actual_transport_subprocess':'PENDING',
            'actual_transport_writable_isolated_scratch':'PENDING','model_effort_availability':'PENDING'},
        'call_readiness':False,'method_outputs_staged':False,'baseline_selection_performed':False,
        'freedom':'Own reasoning, self-checks, verification and reuse of the supplied legacy renderer are permitted.',
        'comparison_scope':'Full CRANE integration versus shared diagnostic helpers and agent reasoning; unrestricted full-method reuse remains separate.',
        'confirmation_n':0,'replication_n':0,'alpha_consumed':0}
    target=output_root/'interface-manifest.json'
    with target.open('x') as stream: json.dump(manifest,stream,indent=2)
    target.chmod(0o444)
    return manifest


def verify(manifest_path):
    path=Path(manifest_path).resolve();manifest=json.loads(path.read_text())
    if manifest['schema']!=SCHEMA or manifest['call_readiness'] is not False:
        raise ValueError('development input interface only')
    expected_python,_=python_closure()
    if {r['relative_path'] for r in manifest['sources']}!=set(expected_python)|set(ROBOT_FILES):
        raise ValueError('complete declared common closure required')
    if len(manifest['sources'])!=len(expected_python)+len(ROBOT_FILES): raise ValueError('duplicate sources')
    if {r['relative_path'] for r in manifest['inputs']}!={'evidence.json','effective-configuration.yaml','public-scope.json'} or len(manifest['inputs'])!=3:
        raise ValueError('exact public packet/configuration/scope input set required')
    workspace=Path(manifest['workspace']).resolve()
    for item in manifest['sources']+manifest['inputs']:
        snapshot=checked(item['snapshot']);original=checked(item['original'])
        if snapshot.resolve()!=workspace/item['relative_path'] or snapshot.read_bytes()!=original.read_bytes():
            raise ValueError('snapshot source/path mismatch')
    for key in ('preparation_source','preparation_tests','scope_tests'): checked(manifest[key])
    if 'build_manifest' in manifest['robot_source_build_audit']:
        checked(manifest['robot_source_build_audit']['build_manifest'])
    expected_files={r['relative_path'] for r in manifest['sources']+manifest['inputs']}
    if {p.relative_to(workspace).as_posix() for p in workspace.rglob('*') if p.is_file()}!=expected_files:
        raise ValueError('workspace contains undeclared source or output')
    if (workspace/'public-scope.json').read_bytes()!=SCOPE.read_bytes():
        raise ValueError('public scope specification mismatch')
    validate_public_inputs(json.loads((workspace/'evidence.json').read_text()),
                           (workspace/'effective-configuration.yaml').read_bytes())
    return manifest


def probe_local_workspace(workspace, scratch):
    """Offline Python/scratch probe; not proof of provider CLI sandbox behavior."""
    workspace,scratch=Path(workspace).resolve(),Path(scratch).resolve()
    if scratch==workspace or workspace in scratch.parents: raise ValueError('scratch must be separate from immutable sources')
    scratch.mkdir(parents=True,exist_ok=False)
    code="import sys,json,pathlib;sys.path.insert(0,sys.argv[1]);"+''.join(
        'import '+Path(name).stem+';' for name in HELPERS)+"pathlib.Path(sys.argv[2],'probe.txt').write_text('scratch works')"
    subprocess.run([sys.executable,'-B','-I','-c',code,str(workspace/'analysis'),str(scratch)],
                   cwd=scratch,check=True,capture_output=True,text=True,timeout=30)
    return {'status':'OFFLINE_HELPER_IMPORTS_AND_SCRATCH_PASS','actual_transport_sandbox_verified':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('packet','configuration','output-root'): parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--build-manifest',type=Path)
    args=parser.parse_args();result=prepare(args.packet,args.configuration,args.output_root,build_manifest=args.build_manifest)
    print(json.dumps({'schema':result['schema'],'call_readiness':result['call_readiness']}))


if __name__=='__main__': main()
