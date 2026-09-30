#!/usr/bin/env python3
"""Combine finalized development rows while retaining original physical clusters."""
import argparse
import json
from pathlib import Path
from analyze_roboboat_terminal_comparison import analyze
from build_roboboat_terminal_batch import save

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/roboboat_terminal_evidence'


def summarize(comparison_roots):
    initial=json.loads((DOC/'pilot_registry_v1.json').read_text())
    continuation=json.loads((DOC/'pilot_continuation_v3.json').read_text())
    cluster={r['id']:r['cluster_id'] for r in initial['rows']}
    cluster.update({r['id']:r['cluster_id'] for r in continuation['rows']})
    rows=[];missing=[]
    for root in comparison_roots:
        inspected=analyze(root)
        rows.extend(r for r in inspected['rows'] if r['batch']!='historical-replay')
        missing.extend(inspected.get('missing_annotations',[]))
    seen=set()
    for r in rows:
        key=(r['batch'],r['method'],r['level'])
        if key in seen:raise ValueError('duplicate answer across comparison roots')
        seen.add(key)
    batches=[]
    for batch in sorted({r['batch'] for r in rows}):
        selected=[r for r in rows if r['batch']==batch]
        complete={(r['method'],r['level']) for r in selected}=={
            (m,l) for m in ('B2','B4') for l in range(3)}
        batch_scores={m:sum(r['answer_success'] for r in selected if r['method']==m)/3
                      for m in ('B2','B4')} if complete else None
        batches.append({'batch':batch,'cluster':cluster[batch],
                        'complete':complete,'scores':batch_scores})
    clusters=[]
    for name in sorted(set(cluster.values())):
        selected=[b for b in batches if b['cluster']==name and b['complete']]
        if len(selected)>2:raise ValueError('reruns cannot add independent variants')
        complete=len(selected)==2
        scores={m:sum(b['scores'][m] for b in selected)/2
                for m in ('B2','B4')} if complete else None
        clusters.append({'cluster':name,'complete_paired_cluster':complete,
                         'completed_batches':[b['batch'] for b in selected],
                         'scores':scores,'difference_B4_minus_B2':
                         scores['B4']-scores['B2'] if scores else None})
    differences=[c['difference_B4_minus_B2'] for c in clusters if c['complete_paired_cluster']]
    return {'schema':'roboboat-development-continuation-results/v1',
        'agent_assessed':True,'confirmation_n':0,'replication_n':0,'alpha_allocated':0,
        'rows':rows,'missing_annotations':missing,
        'complete_configuration_recordings':sum(b['complete'] for b in batches),
        'complete_independent_paired_clusters':len(differences),'batches':batches,
        'clusters':clusters,'finalized_fresh_answers':len(rows),
        'mean_cluster_difference_B4_minus_B2':sum(differences)/len(differences) if differences else None,
        'p_value':None,'confidence_interval':None,
        'inference':'Small inspected development sample; no inferential activation or superiority claim.',
        'judge_uncertainty':'Eight construction-defined marine qualification cases, two passes; passes do not double case N. Perfect observed accuracy is not zero population error.',
        'endpoint_limitation':'Method-blind project sentence inventory; confirmatory endpoint qualification pending.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('comparison_roots',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=summarize(args.comparison_roots)
    save(args.output,result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
