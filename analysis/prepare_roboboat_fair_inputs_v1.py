"""Uniform source-matched development inputs; no response/model/judge execution."""
import argparse
import json
from pathlib import Path
import shutil
from evidence_calibration_io import canonical_sha256
from profile_roboboat_trace_development_v2 import profile
import prepare_roboboat_baseline_interface_v3 as common
from roboboat_runtime_source_closure_v1 import source_closure
from run_roboboat_population_responses_v1 import binding, checked

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'artifacts/roboboat-episode-clock-v10/full-build-v1.json'
AUDIT=ROOT/'artifacts/roboboat-episode-clock-v10/compiled-source-audit-v2.json'
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
    private={s['relative_path'] for s in private_sources}
    for source in private_sources:
        target=b4_workspace/source['relative_path']
        if target.read_bytes()!=checked(source['snapshot']).read_bytes() or target.read_bytes()!=checked(source['original']).read_bytes():raise ValueError('B4 candidate source snapshot changed')
    actual={p.relative_to(b4_workspace).as_posix() for p in b4_workspace.rglob('*') if p.is_file()}
    if actual!=set(public)|private:raise ValueError('undeclared private/evaluator/output in B4 input workspace')
    return canonical_sha256(public)


def prepare(collection_declaration,output):
    collection_declaration,output=map(lambda p:Path(p).resolve(),(collection_declaration,output))
    if output.exists():raise FileExistsError('immutable all-eligible input snapshot required')
    distribution=profile(collection_declaration);d=json.loads(collection_declaration.read_text())
    if d.get('new_candidate_geometry_draws')!=24 or d.get('model_calls_authorized_by_this_declaration')!=0:
        raise ValueError('current fresh exploratory physical batch required')
    paths=set(source_closure([METHOD]));paths.add(CATALOG)
    # The corpus remains evaluator-side. Only scoped common files go to B2;
    # private treatment implementation/catalog goes exclusively to B4.
    private=[{'relative_path':p.relative_to(ROOT).as_posix(),'original':binding(p)} for p in sorted(paths)]
    output.mkdir();private_root=output/'private-B4-source-snapshot'
    for item in private:
        target=private_root/item['relative_path'];copy_bound(checked(item['original']),target);item['snapshot']=binding(target)
    entries=[]
    for row in distribution['rows']:
        if row['status']!='VALID_TRACE_QUALIFIED_DEVELOPMENT':continue
        capture=Path(d['output_root'])/row['id']
        for level in range(3):
            case=output/'cases'/(row['id']+f'-L{level}');b2=case/'common-inputs';b4=case/'B4-private-workspace'
            m=common.prepare(capture/'exports-v2/method_packets'/f'L{level}.json',capture/'exports-v2/effective-configuration.yaml',b2,compiled_audit=AUDIT,build_manifest=BUILD)
            for item in m['sources']+m['inputs']:copy_bound(checked(item['snapshot']),b4/item['relative_path'])
            for item in private:copy_bound(checked(item['snapshot']),b4/item['relative_path'])
            manifest=b2/'interface-manifest.json';signature=verify_pair(manifest,private,b4)
            entries.append({'row_id':row['id'],'cluster_id':row['cluster_id'],'family':row['family'],'level':level,'common_manifest':binding(manifest),'B4_private_workspace':str(b4.resolve()),'common_file_hash_signature':signature,'capture_terminal':binding(capture/'capture-export-terminal-trace-v4.json')})
    record={'schema':'roboboat-fair-development-input-snapshot/v1','status':'INPUTS_PREPARED_METHODS_UNEXECUTED_UNQUALIFIED','collection_declaration':binding(collection_declaration),'builder':binding(__file__),'runtime_source_closure':[binding(p) for p in source_closure([Path(__file__)])],'build_manifest':binding(BUILD),'compiled_source_audit':binding(AUDIT),'capture_accounting':distribution,'entries':entries,'private_B4_sources':private,'eligible_recordings':distribution['valid_recordings'],'prepared_conditions':len(entries),'scope':'All completed admitted records in the immutable snapshot, every L0-L2 condition; failures/running/unattempted preserved; no answer or task-outcome selection. Each method has byte-identical common inputs. B2 excludes treatment sources; B4 includes its private full shared planner/realizer/verifier/repair candidate.','B4_candidate':'full CRANE development v3, not promoted','B2_candidate':'common diagnostic helpers/current generic robot sources plus own tool-enabled reasoning; actual provider capability and strongest-baseline qualification pending','capability_qualified':False,'methods_executed':False,'model_calls':0,'judge_calls':0,'call_readiness':False,'baseline_promotion':False,'confirmation_frozen':False,'confirmation_n':0,'replication_n':0,'independent_n_added_by_preparation':0,'future_requirements':'Prospectively declare model/tool/prompt settings and execution after provider/tool qualification; authenticate exact served public workspace in provider receipts; source-complete judging and faithful text-only extraction before endpoint scoring. No prepared output is an explanation or scored observation.'}
    target=output/'input-snapshot.json';target.write_text(json.dumps(record,indent=2)+'\n');verify(target);return record


def verify(snapshot_path):
    r=json.loads(Path(snapshot_path).read_text())
    if r['schema']!='roboboat-fair-development-input-snapshot/v1' or r['methods_executed']is not False or r['call_readiness']is not False:raise ValueError('unexecuted development input snapshot only')
    for key in ('collection_declaration','builder','build_manifest','compiled_source_audit'):checked(r[key])
    expected={str(p.resolve()) for p in source_closure([Path(__file__)])}
    if len(r['runtime_source_closure'])!=len(expected) or {p['path'] for p in r['runtime_source_closure']}!=expected:raise ValueError('complete preparation runtime closure required')
    for item in r['runtime_source_closure']:checked(item)
    eligible={x['id'] for x in r['capture_accounting']['rows'] if x['status']=='VALID_TRACE_QUALIFIED_DEVELOPMENT'}
    actual={(e['row_id'],e['level']) for e in r['entries']}
    if len(r['entries'])!=len(actual) or actual!={(i,l) for i in eligible for l in range(3)}:raise ValueError('all eligible evidence conditions required without duplication')
    for entry in r['entries']:
        checked(entry['capture_terminal']);m=checked(entry['common_manifest'])
        if verify_pair(m,r['private_B4_sources'],entry['B4_private_workspace'])!=entry['common_file_hash_signature']:raise ValueError('served common input signature changed')
    return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--collection-declaration',required=True);p.add_argument('--output',required=True);a=p.parse_args();r=prepare(a.collection_declaration,a.output);print(json.dumps({'status':r['status'],'eligible_recordings':r['eligible_recordings'],'prepared_conditions':r['prepared_conditions'],'calls':r['model_calls']}))
