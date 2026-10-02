#!/usr/bin/env python3
"""Descriptive cluster reporting after finalized blinded support annotation."""
import argparse,json,hashlib
from pathlib import Path
from build_roboboat_terminal_batch import save


def analyze(root):
    rows=[];missing=[]
    for path in sorted((root/'evaluator_join').glob('*.json')):
        join=json.loads(path.read_text());opaque=join['opaque_response_id'];p=root/'annotations'/opaque/'final.json'
        if not p.exists():missing.append(join);continue
        final=json.loads(p.read_text())
        if not final['ready_for_separate_key_join'] or final['method_identity_visible']:raise ValueError('blind handoff gate closed')
        decisions=final['final_decisions'];claims=[v for k,v in decisions.items() if k.startswith('claim:')]
        units=[v for k,v in decisions.items() if k.startswith('unit:')]
        limits=[v for k,v in decisions.items() if k.startswith('limitation:')]
        outcome={'all_claims_supported':all(v=='SUPPORTED_BY_VISIBLE_EVIDENCE' for v in claims),
                 'required_units_covered':sum(units),'required_units_n':len(units),'limitations_preserved':all(limits)}
        # Strict conjunctive development feasibility score. No method-specific wording/rank demand.
        outcome['answer_success']=outcome['all_claims_supported'] and all(units) and all(limits)
        rows.append({**join,**outcome,'final_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    result={'schema':'roboboat-terminal-comparison-development-results/v1','agent_assessed':True,
            'human_validation':False,'confirmation_n':0,'alpha_allocated':0.,'rows':rows,
            'missing_annotations':missing,'independent_fresh_paired_clusters':1,
            'historical_replay_n_added':0,'comparative_inference':'NOT_ESTIMABLE: one valid fresh paired cluster; stopped pilot, no prospective confirmatory allocation',
            'p_value':None,'confidence_interval':None,
            'endpoint_status':'development feasibility only; sentence-level project inventory, not frozen atomic confirmation endpoint'}
    summaries=[]
    for batch in sorted({r['batch'] for r in rows}):
        s={'batch':batch,'historical':batch=='historical-replay'}
        for method in ('B2','B4'):
            selected=[r for r in rows if r['batch']==batch and r['method']==method]
            s[method]={'n_answers':len(selected),'successes':sum(r['answer_success'] for r in selected),
                       'mean_success':sum(r['answer_success'] for r in selected)/len(selected) if selected else None,
                       'required_units_covered':sum(r['required_units_covered'] for r in selected),
                       'required_units_n':sum(r['required_units_n'] for r in selected)}
        summaries.append(s)
    result['batch_summaries']=summaries
    fresh=[r for r in rows if not r['batch']=='historical-replay']
    result['fresh_cluster_summary']={m:{'n_answers':len([r for r in fresh if r['method']==m]),
            'successes':sum(r['answer_success'] for r in fresh if r['method']==m)} for m in ('B2','B4')}
    if not missing and len(rows)==18:
        b2=result['fresh_cluster_summary']['B2'];b4=result['fresh_cluster_summary']['B4']
        result['fresh_cluster_observed_mean_difference_B4_minus_B2']=(b4['successes']-b2['successes'])/6
    else:result['fresh_cluster_observed_mean_difference_B4_minus_B2']=None
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('comparison',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=analyze(a.comparison);save(a.output,result);print(json.dumps(result['batch_summaries'],indent=2))
if __name__=='__main__':main()
