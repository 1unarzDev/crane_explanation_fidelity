"""Read-only compiled-source and sparse-counter review of fixed development failures."""
import argparse
from collections import Counter
import json
from pathlib import Path

from audit_roboboat_frame_timing_v1 import audit
from run_roboboat_population_responses_v1 import binding, checked


def review(profile_path, compiler_path):
    profile_path=Path(profile_path).resolve();compiler_path=Path(compiler_path).resolve()
    p=json.loads(profile_path.read_text())
    if p['schema']!='roboboat-trace-development-profile/v2' or p['confirmation_n']!=0:
        raise ValueError('development-only profile required')
    for item in p['dependencies']:checked(item)
    d=json.loads(checked(p['dependencies'][0]).read_text())
    if [row['id'] for row in p['rows']]!=d['rows']:
        raise ValueError('full declared denominator required')
    compiler=json.loads(compiler_path.read_text());checked(compiler['build_manifest'])
    names={'Assets/Scripts/Sensors/Vision/RosCameraAsync.cs',
        'Assets/Scripts/Sensors/Vision/RosDepthCameraAsync.cs',
        'Assets/Scripts/Utils/Performance/CraneProfiler.cs',
        'Assets/Scripts/Performance/CraneFrameTimingAudit.cs',
        'Assets/Scripts/Performance/CraneBenchmarkRunner.cs'}
    sources=[]
    for record in compiler['records']:
        for document in record.get('source_documents',[]):
            if document.get('relative') not in names:continue
            current=checked(document['source']);metadata=record['metadata']
            if document['status']!='MATCH' or document['document']['checksum']!=binding(current)['sha256']:
                raise ValueError('compiler-source mismatch')
            if 'compiler_source' in document:checked(document['compiler_source'])
            assembly={'path':metadata['assembly'],'sha256':metadata['assembly_sha256']}
            pdb={'path':metadata['pdb'],'sha256':metadata['pdb_sha256']}
            checked(assembly);checked(pdb)
            if not metadata['assembly_pdb_identity_match'] or not metadata['pe_pdb_checksum_match']:
                raise ValueError('assembly/PDB mismatch')
            sources.append({'relative':document['relative'],'source':binding(current),
                'compiled_document':document['document'],'assembly':assembly,'pdb':pdb})
    if {s['relative'] for s in sources}!=names:raise ValueError('source coverage incomplete')
    results=[]
    for row in p['rows']:
        if row['status']!='TECHNICAL_FAILURE':continue
        folder=Path(d['output_root'])/row['id'];terminal=folder/'capture-attempt.json'
        worker=folder/'worker-0/result.json';fixture=folder/'fixture-summary.json'
        r=json.loads(terminal.read_text());w=json.loads(worker.read_text());f=json.loads(fixture.read_text())
        if r['status']!=row['status'] or r['row']['id']!=row['id']:
            raise ValueError('original failure identity mismatch')
        a=audit(folder/'frame-timing.jsonl');failed=[k for k,v in r['checks'].items() if not v]
        if w['staleObservations']!=a['stale_increments']:
            raise ValueError('sparse increments do not reconstruct worker counter')
        results.append({'row_id':row['id'],'family':row['family'],'original_disposition':r['status'],
            'navigation_status':f['status'],'failed_checks':failed,
            'stale_observation_count':w['staleObservations'],'failed_observation_count':w['failedObservations'],
            'stale_observation_only_gates':set(failed)=={'stale_observations_zero','retained_benchmark_staleObservations'},
            'original_terminal':binding(terminal),'worker':binding(worker),'fixture':binding(fixture),
            'frame_diagnostics':a})
    return {'schema':'roboboat-observation-counter-source-review/v34','reviewer':binding(__file__),
        'profile':binding(profile_path),'compiled_source_audit':binding(compiler_path),'compiled_sources':sources,
        'frame_auditor':binding(audit.__code__.co_filename),'scheduled_denominator':len(p['rows']),
        'fixed_dispositions':p['recording_dispositions'],'results':results,
        'technical_failure_navigation_statuses':dict(Counter(r['navigation_status'] for r in results)),
        'stale_observation_only_gate_failures':sum(r['stale_observation_only_gates'] for r in results),
        'counter_semantics':'In both compiled camera sensor sources, a scheduled FixedUpdate readback is skipped when the pending queue is full and has a request from the current local epoch; that branch calls ReportStaleObservation. The profiler increments the shared counter. This counter alone does not establish publication of stale imagery. Sparse LateUpdate samples cannot attribute increments to RGB versus depth or reconstruct each request/completion.',
        'root_cause_established':False,'admissions_changed':False,
        'historical_external_runtime_closure_authenticated':False,'independent_n_added':0,
        'endpoint_scores':0,'confirmation_n':0,'replication_n':0,
        'scope':'Fixed full-denominator development snapshot, all technical failures, exact current compiled-document source chain and source-level interpretation. Every failed disposition retained. No failure salvage, weaker guard, causal navigation diagnosis, new runtime candidate or endpoint label.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',required=True)
    parser.add_argument('--compiled-audit',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args();result=review(args.profile,args.compiled_audit)
    with Path(args.output).open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'reviewed_failures':len(result['results']),
        'stale_observation_only_failures':result['stale_observation_only_gate_failures'],
        'technical_failure_navigation_statuses':result['technical_failure_navigation_statuses'],
        'matched_compiled_source_documents':len(result['compiled_sources']),
        'stale_counter_reconstructed_in_every_failure':True,'admissions_changed':False}))
