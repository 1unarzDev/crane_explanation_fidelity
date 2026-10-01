"""Summarize the complete predeclared reliability assay, retaining every failure."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median


def binding(p):
    return {'path':str(p.resolve()),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}


def summarize(declaration_path):
    declaration_path=Path(declaration_path);d=json.loads(declaration_path.read_text())
    root=Path(d['output_root']);terminal_path=root/'terminal.json';t=json.loads(terminal_path.read_text())
    if t['status']!='RELIABILITY_ASSAY_FINISHED' or t['declaration_sha256']!=binding(declaration_path)['sha256']:
        raise ValueError('complete bound reliability terminal required')
    if [r['row']['id'] for r in t['results']]!=[u['operational_run_id'] for u in d['schedule']]:
        raise ValueError('all declared runs in declared order required')
    runs=[]
    for unit,record in zip(d['schedule'],t['results']):
        if record['trace_enabled'] is not unit['trace_enabled'] or record['new_independent_n']!=0:
            raise ValueError('nonstudy tracing condition mismatch')
        out=root/unit['operational_run_id'];row={'id':unit['operational_run_id'],'trace_enabled':unit['trace_enabled'],
            'status':record['status'],'strict_check_failures':[k for k,v in record.get('checks',{}).items() if not v],
            'error':record.get('error'),'measurements':{},'inputs':[binding(out/'capture-attempt.json')]}
        worker_path=out/'worker-0/result.json'
        if worker_path.exists():
            worker=json.loads(worker_path.read_text());row['inputs'].append(binding(worker_path))
            row['measurements'].update({k:worker.get(k) for k in ('realTimeFactor','staleActions','rejectedActions','acceptedActions','staleObservations','failedObservations','loggedErrors','loggedExceptions')})
            row['measurements']['commandTimeouts']=worker.get('actionTiming',{}).get('commandTimeouts')
        frame_path=out/'frame-timing.jsonl'
        if frame_path.exists():
            frames=[json.loads(s) for s in frame_path.read_text().splitlines() if s.strip()][1:]
            row['inputs'].append(binding(frame_path))
            row['measurements']['sparse_frame_rows']=len(frames)
            row['measurements']['sparse_retained_unscaled_delta_median']=median(f['unscaledDeltaTime'] for f in frames) if frames else None
            row['measurements']['sparse_retained_unscaled_delta_maximum']=max((f['unscaledDeltaTime'] for f in frames),default=None)
            row['measurements']['sparse_rows_four_plus_fixed_updates']=sum(f['fixedUpdates']>=4 for f in frames)
            row['measurements']['sparse_stale_increments']=sum(f['staleIncrement'] for f in frames)
        trace_path=out/'action-timing-audit.json'
        if trace_path.exists():
            trace=json.loads(trace_path.read_text());row['inputs'].append(binding(trace_path))
            row['measurements']['trace_integrity_pass']=trace['trace_integrity_pass']
        runs.append(row)
    return {'schema':'roboboat-tracing-overhead-summary/v1-development','declaration':binding(declaration_path),
            'terminal':binding(terminal_path),'runs':runs,'all_declared_runs_retained':True,
            'new_independent_n':0,'scientific_admission_authorized':False,'performance_equivalence_established':False,
            'limitations':['Two runs per condition provide descriptive engineering evidence only.',
                'Sparse frames retain anomalies and periodic samples; retained medians and maxima are not all-frame timing distributions.',
                'ABBA balances a linear order trend but cannot remove shared host-load changes or establish causal equivalence.',
                'Technical failures and missing measurements remain in the declared denominator; no explanation outcomes were generated.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('declaration',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();result=summarize(a.declaration)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
