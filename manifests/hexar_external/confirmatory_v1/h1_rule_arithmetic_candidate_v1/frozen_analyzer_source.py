#!/usr/bin/env python3
"""One terminal frozen paired analysis, including pass and missingness sensitivities."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from run_evidence_calibration_b2_pilot import ROOT
from summarize_handoff_development_results import aggregate
from summarize_handoff_response_development import paired_interval


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',required=True,type=Path);parser.add_argument('--annotations',required=True,type=Path);parser.add_argument('--look',choices=['FIRST','FINAL'],default='FIRST');args=parser.parse_args()
    freeze=json.loads(args.freeze.read_text())
    if freeze['status']!='FROZEN_BEFORE_FIRST_CONFIRMATORY_SEMANTIC_OUTPUT':raise RuntimeError('No frozen design')
    base=ROOT/'analysis/results/confirmation'/freeze['study_id'];target_n=freeze['first_look_n'] if args.look=='FIRST' else freeze['valid_paired_episode_n']
    out=base/('look-'+str(target_n));target=out/'primary-analysis-v1.json'
    if target.exists():
        print('Frozen terminal analysis already retained at '+str(target));return
    accounting=json.loads((base/('execution-accounting-'+args.look+'.json')).read_text())
    if not accounting['complete'] or accounting['complete_paired_episode_n']!=target_n:raise RuntimeError('Frozen valid N incomplete')
    # Join method identities only after every blinded case has a validated final score.
    cases=json.loads((out/'blind-cases-v1.json').read_text())['cases'];expected={c['case_id'] for c in cases};passes={};sources=[]
    for slot in ['A','B']:
        rows={}
        for p in sorted(args.annotations.glob(slot+'-batch-*.json')):
            if p.name.endswith('request.json'):continue
            record=json.loads(p.read_text())
            if record['status']!='STRUCTURALLY_VALID_SUPPORT_RETURN':raise RuntimeError('Unresolved annotation technical failure: '+str(p))
            for r in record['parsed_final']['annotations']:
                if r['case_id'] in rows:raise RuntimeError('Duplicate score')
                rows[r['case_id']]=r
            sources.append(dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
        if set(rows)!=expected:raise RuntimeError('Incomplete or extra blind scores')
        passes[slot]=rows
    joins={j['response_id']:j for j in json.loads((out/'join-key-v1.json').read_text())['entries']}
    if set(joins)!=expected:raise RuntimeError('Blind key mismatch')
    merged={slot:[] for slot in ['A','B','primary']};disagreements=[]
    for i,j in joins.items():
        a,b=passes['A'][i],passes['B'][i];ua={u['unit_id']:u['communicated'] for u in a['required_units']};ub={u['unit_id']:u['communicated'] for u in b['required_units']}
        if set(ua)!=set(ub):raise RuntimeError('Unit mismatch')
        if a['primary_failure']!=b['primary_failure'] or ua!=ub:disagreements.append(dict(case_id=i,primary=a['primary_failure']!=b['primary_failure'],coverage=sum(ua[u]!=ub[u] for u in ua)))
        for slot,r in [('A',a),('B',b),('primary',a)]:
            merged[slot].append(dict(configuration_id=j['configuration_id'],method=j['method_id'],family=j['realized_family'],condition_id=j['condition_id'],
                primary_failure=a['primary_failure'] or b['primary_failure'] if slot=='primary' else r['primary_failure'],
                covered=sum(ua[u] and ub[u] for u in ua) if slot=='primary' else sum(ua.values()) if slot=='A' else sum(ub.values()),required=len(ua),
                primary_violations=list({(v['kind'],v['quote']):v for rr in (a,b) for v in rr['primary_violations']}.values()) if slot=='primary' else r['primary_violations'],
                factual_numeric_errors=list({v['quote']:v for rr in (a,b) for v in rr['factual_numeric_errors']}.values()) if slot=='primary' else r['factual_numeric_errors']))
    estimates={slot:aggregate(rows,b4_method='B4v7',interval_fn=lambda b,c,n:paired_interval(b,c,n,tail_probability=.00625)) for slot,rows in merged.items()};primary=estimates['primary']
    if primary['independent_episode_n']!=target_n:raise RuntimeError('Wrong independent N')
    if args.look=='FIRST' and primary['B2_fails_B4_passes']+primary['B4_fails_B2_passes']>0:
        target.write_text(json.dumps(dict(study_id=freeze['study_id'],study_stage='CONFIRMATION',look='FIRST',independent_episode_n=target_n,continuation_required=True,terminal_analysis=False,reason='At least one paired discordance; prospectively continue to1200 without an interim superiority test or method change.'),indent=2)+'\n')
        print('Frozen first look: continue to1200; no interim superiority test');return
    coverage=freeze['useful_coverage'];covered=primary['methods']['B4v7']['mean_episode_coverage']>=coverage['minimum_B4_mean_episode_fraction'] and primary['mean_episode_coverage_difference_B4_minus_B2']>=-coverage['maximum_mean_episode_loss_B4_vs_B2']
    significant=primary['descriptive_exact_one_sided_p']<=freeze['alpha'] and primary['paired_risk_difference_B2_minus_B4']>0
    missing=sum(r['disposition']=='METHOD_TECHNICAL_FAILURE' for r in accounting['records'] if 'disposition' in r)
    # Paired-output records have no disposition field; every incomplete attempted method pair is missing.
    missing+=sum(not r['complete_pair'] and 'b2_calls' in r for r in accounting['records'])
    n=primary['independent_episode_n'];net=primary['B2_fails_B4_passes']-primary['B4_fails_B2_passes']
    result=dict(study_id=freeze['study_id'],study_stage='CONFIRMATION',freeze_sha256=hashlib.sha256(args.freeze.read_bytes()).hexdigest(),alpha=freeze['alpha'],look=args.look,terminal_analysis=True,continuation_required=False,stopped_for_zero_discordance_futility=args.look=='FIRST',
        exact_one_sided_confirmatory_p=primary['descriptive_exact_one_sided_p'],significant_superiority=significant,useful_coverage_requirement_passed=covered,
        primary_scientific_success=significant and covered,primary=primary,pass_sensitivity=estimates,
        interval_method=freeze['interval'],disagreements=disagreements,annotation_sources=sources,
        missingness=dict(acquired_records=len(accounting['records']),physical_invalid_or_outside_population=sum('disposition' in r for r in accounting['records']),method_incomplete_pairs=missing,
            full_eligible_population_worst_case_risk_difference_bounds=[(net-missing)/(n+missing),(net+missing)/(n+missing)]),
        decomposition={m:dict(violation_kinds=dict(Counter(v['kind'] for r in merged['primary'] if r['method']==m for v in r['primary_violations'])),numeric_error_conditions=sum(bool(r['factual_numeric_errors']) for r in merged['primary'] if r['method']==m),
            levels={f'E{k}':dict(answers=len(rs),failures=sum(r['primary_failure'] for r in rs),covered=sum(r['covered'] for r in rs),required=sum(r['required'] for r in rs)) for k in range(4) for rs in [[r for r in merged['primary'] if r['method']==m and r['condition_id'].endswith(f'-E{k}')]]}) for m in ['B2','B4v7']},
        limitations=['Automated same-model independent judge passes; shared systematic error and style inference remain possible.','Inference is for the frozen simulator/configuration population and technically complete pairs; missingness may be associated with task difficulty.','No outcome-dependent method, endpoint, coverage, test or population revision permitted.'],condition_rows=merged['primary'])
    target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(independent_n=n,discordances=[primary['B2_fails_B4_passes'],primary['B4_fails_B2_passes']],paired_risk_difference=primary['paired_risk_difference_B2_minus_B4'],ci=primary['conservative_whole_episode_95_ci'],p=result['exact_one_sided_confirmatory_p'],coverage_passed=covered,scientific_success=result['primary_scientific_success']),indent=2))

if __name__=='__main__':main()
