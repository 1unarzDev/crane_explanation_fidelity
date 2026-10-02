"""Uniform source-matched development inputs; no response/model/judge execution."""
import argparse
import json
from pathlib import Path
import shutil
from evidence_calibration_io import canonical_sha256
from profile_roboboat_trace_development_v2 import profile
import prepare_roboboat_baseline_interface_v4 as common
from roboboat_runtime_source_closure_v1 import source_closure
from run_roboboat_population_responses_v1 import binding, checked

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'artifacts/roboboat-command-shutdown-v17/full-build-v1.json'
AUDIT=ROOT/'artifacts/roboboat-command-shutdown-v17/compiled-source-audit-v4.json'
METHOD=ROOT/'analysis/roboboat_full_crane_v3.py'
CATALOG=ROOT/'configs/roboboat_claim_contracts_v3_development.json'


def copy_bound(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.read_bytes()!=source.read_bytes():raise ValueError('private/common source collision')
    else:shutil.copyfile(source,target);target.chmod(0o444)


def verify_pair(common_manifest,private_sources,b4_workspace):
    m=common.verify(common_manifest);b4_workspace=Path(b4_workspace).resolve();public={}
    for item in m['sources']+m['inputs']:
        source=checked(item['snapshot']);target=b4_workspace/item['relative_path']
        if not target.is_file() or target.read_bytes()!=source.read_bytes():raise ValueError('unequal method-visible common inputs')
        public[item['relative_path']]=binding(source)['sha256']
    expected_private={p.relative_to(ROOT).as_posix() for p in source_closure([METHOD])}|{CATALOG.relative_to(ROOT).as_posix()}
    private={s['relative_path'] for s in private_sources}
    if len(private_sources)!=len(expected_private) or private!=expected_private:raise ValueError('exact full B4 candidate source closure required')
    for source in private_sources:
        target=b4_workspace/source['relative_path']
        if target.read_bytes()!=checked(source['snapshot']).read_bytes() or target.read_bytes()!=checked(source['original']).read_bytes():raise ValueError('B4 candidate source snapshot changed')
    actual={p.relative_to(b4_workspace).as_posix() for p in b4_workspace.rglob('*') if p.is_file()}
    if actual!=set(public)|private:raise ValueError('undeclared private/evaluator/output in B4 input workspace')
    return canonical_sha256(public)


def authenticate_capture(capture,declaration,declaration_path):
    """Bind admitted recording to exact build/collector/declared inputs.

    Does not assert deployed/reflected closure or method/judge qualification.
    """
    import run_roboboat_varied_start_development_v27 as collector
    capture=Path(capture).resolve()
    original=json.loads((capture/'capture-attempt.json').read_text())
    published=json.loads((capture/'capture-export-terminal-trace-v4.json').read_text())
    expected=binding(BUILD)
    if original['full_compiled_build']!=expected or published['original_capture_terminal']!=binding(capture/'capture-attempt.json'):
        raise ValueError('recording/build binding mismatch')
    if original['collector_sha256']!=binding(Path(collector.__file__))['sha256']:
        raise ValueError('recording collector mismatch')
    if original['prospective_declaration']!=binding(declaration_path) or published['prospective_declaration']!=binding(declaration_path):
        raise ValueError('recording admission declaration mismatch')
    if not all(original['checks'].values()) or original['status']!='VALID_TRACE_QUALIFIED_DEVELOPMENT':
        raise ValueError('all original gates required')
    if original['operational_replay']is not False or published['operational_replay']is not False:
        raise ValueError('operational cases are not fresh development')
    if original['platform_version']!=declaration['platform_version'] or published['platform_version']!=declaration['platform_version']:
        raise ValueError('revised platform version mismatch')
    worker=json.loads((capture/'worker-0/result.json').read_text())
    if worker['scene']!='Assets/Scenes/Roboboat Course.unity' or worker['runtimeProfile']!='train-gpu':
        raise ValueError('recording runtime scene/profile mismatch')
    collector.verify_bundle(capture/'owned-player')
    for record in published['raw_sources']:checked(record)
    return {'schema':'roboboat-current-recording-build-authentication/v1',
        'original':binding(capture/'capture-attempt.json'),'published':binding(capture/'capture-export-terminal-trace-v4.json'),
        'build_manifest':expected,'collector':binding(Path(collector.__file__)),
        'worker':binding(capture/'worker-0/result.json'),'scene':worker['scene'],'runtime_profile':worker['runtimeProfile'],
        'all_original_admission_gates_pass':True,'scope':'Exact recorded build, declared inputs, admitted trace and runtime scene/profile. Full external/reflected deployment and physical equivalence remain unproven.',
        'provider_qualified':False,'judge_qualified':False,'independent_n_added':0}


def prepare(collection_declaration,output):
    collection_declaration,output=map(lambda p:Path(p).resolve(),(collection_declaration,output))
    if output.exists():raise FileExistsError('immutable all-eligible input snapshot required')
    distribution=profile(collection_declaration);d=json.loads(collection_declaration.read_text())
    import run_roboboat_varied_start_development_v27 as collector
    _, registry, scheduled = collector.validate_declaration(d, collection_declaration)
    if len(scheduled)!=len(d['rows']) or registry['independent_geometry_draws']<1:
        raise ValueError('current prospectively declared varied-start development required')
    paths=set(source_closure([METHOD]));paths.add(CATALOG)
    # The corpus remains evaluator-side. Only scoped common files go to B2;
    # private treatment implementation/catalog goes exclusively to B4.
    private=[{'relative_path':p.relative_to(ROOT).as_posix(),'original':binding(p)} for p in sorted(paths)]
    output.mkdir();accounting=output/'capture-accounting.json';accounting.write_text(json.dumps(distribution,indent=2)+'\n');private_root=output/'private-B4-source-snapshot'
    for item in private:
        target=private_root/item['relative_path'];copy_bound(checked(item['original']),target);item['snapshot']=binding(target)
    entries=[]
    for row in distribution['rows']:
        if row['status']!='VALID_TRACE_QUALIFIED_DEVELOPMENT':continue
        capture=Path(d['output_root'])/row['id']
        authentication=authenticate_capture(capture,d,collection_declaration)
        for level in range(3):
            case=output/'cases'/(row['id']+f'-L{level}');b2=case/'common-inputs';b4=case/'B4-private-workspace'
            m=common.prepare(capture/'exports-v2/method_packets'/f'L{level}.json',capture/'exports-v2/effective-configuration.yaml',b2,compiled_audit=AUDIT,build_manifest=BUILD)
            for item in m['sources']+m['inputs']:copy_bound(checked(item['snapshot']),b4/item['relative_path'])
            for item in private:copy_bound(checked(item['snapshot']),b4/item['relative_path'])
            manifest=b2/'interface-manifest.json';signature=verify_pair(manifest,private,b4)
            entries.append({'row_id':row['id'],'cluster_id':row['cluster_id'],'family':row['family'],'level':level,'common_manifest':binding(manifest),'B4_private_workspace':str(b4.resolve()),'common_file_hash_signature':signature,'capture_terminal':binding(capture/'capture-export-terminal-trace-v4.json'),'recording_build_authentication':authentication})
    record={'schema':'roboboat-fair-development-input-snapshot/v3-varied-start','status':'INPUTS_PREPARED_METHODS_UNEXECUTED_UNQUALIFIED','collection_declaration':binding(collection_declaration),'builder':binding(__file__),'runtime_source_closure':[binding(p) for p in source_closure([Path(__file__)])],'build_manifest':binding(BUILD),'compiled_source_audit':binding(AUDIT),'capture_accounting':distribution,'capture_accounting_binding':binding(accounting),'entries':entries,'private_B4_sources':private,'eligible_recordings':distribution['valid_recordings'],'prepared_conditions':len(entries),'scope':'All completed admitted records in the immutable snapshot, every L0-L2 condition; failures/running/unattempted preserved; no answer or task-outcome selection. Each method has byte-identical common inputs. B2 excludes treatment sources; B4 includes its private full shared planner/realizer/verifier/repair candidate.','B4_candidate':'full CRANE development v3, not promoted','B2_candidate':'common diagnostic helpers/current generic robot sources plus own tool-enabled reasoning; actual provider capability and strongest-baseline qualification pending','capability_qualified':False,'methods_executed':False,'model_calls':0,'judge_calls':0,'call_readiness':False,'baseline_promotion':False,'confirmation_frozen':False,'confirmation_n':0,'replication_n':0,'independent_n_added_by_preparation':0,'future_requirements':'Prospectively declare model/tool/prompt settings and execution after provider/tool qualification; authenticate exact served public workspace in provider receipts; source-complete judging and faithful text-only extraction before endpoint scoring. No prepared output is an explanation or scored observation.'}
    target=output/'input-snapshot.json';target.write_text(json.dumps(record,indent=2)+'\n');verify(target);return record


def verify(snapshot_path):
    r=json.loads(Path(snapshot_path).read_text())
    if r['schema']!='roboboat-fair-development-input-snapshot/v3-varied-start' or r['methods_executed']is not False or r['call_readiness']is not False:raise ValueError('unexecuted development input snapshot only')
    for key in ('collection_declaration','builder','build_manifest','compiled_source_audit'):checked(r[key])
    expected={str(p.resolve()) for p in source_closure([Path(__file__)])}
    if len(r['runtime_source_closure'])!=len(expected) or {p['path'] for p in r['runtime_source_closure']}!=expected:raise ValueError('complete preparation runtime closure required')
    for item in r['runtime_source_closure']:checked(item)
    captured=json.loads(checked(r['capture_accounting_binding']).read_text())
    if captured!=r['capture_accounting']:raise ValueError('retained capture accounting changed')
    d=json.loads(checked(r['collection_declaration']).read_text())
    if [row['id'] for row in captured['rows']]!=d['rows']:raise ValueError('full declared physical denominator required')
    for item in captured['dependencies']:checked(item)
    eligible={x['id'] for x in r['capture_accounting']['rows'] if x['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT'}
    actual={(e['row_id'],e['level']) for e in r['entries']}
    if len(r['entries'])!=len(actual) or actual!={(i,l) for i in eligible for l in range(3)}:raise ValueError('all eligible evidence conditions required without duplication')
    for entry in r['entries']:
        checked(entry['capture_terminal']);m=checked(entry['common_manifest'])
        capture=Path(d['output_root'])/entry['row_id']
        if authenticate_capture(capture,d,Path(r['collection_declaration']['path']))!=entry['recording_build_authentication']:
            raise ValueError('recording/build authentication changed')
        if verify_pair(m,r['private_B4_sources'],entry['B4_private_workspace'])!=entry['common_file_hash_signature']:raise ValueError('served common input signature changed')
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--collection-declaration',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=prepare(a.collection_declaration,a.output);print(json.dumps({'status':r['status'],'eligible_recordings':r['eligible_recordings'],'prepared_conditions':r['prepared_conditions'],'calls':r['model_calls']}))
