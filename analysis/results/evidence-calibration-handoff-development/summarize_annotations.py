#!/usr/bin/env python3
"""Join DEVELOPMENT identities only after retained annotation calls; report paired counts."""
import argparse,collections,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def summarize(directory,slot):
    annotations=[];fails=[]
    for f in sorted(directory.glob(f'{slot}-batch-*.json')):
        if f.name.endswith('.request.json'):continue
        d=json.loads(f.read_text())
        if d['status']=='STRUCTURALLY_VALID_SUPPORT_RETURN':annotations+=d['parsed_final']['annotations']
        else:fails.append({'path':str(f.relative_to(ROOT)),'failure':d.get('failure')})
    joins={e['response_id']:e for e in json.loads((HERE/'development-join-key-v1.json').read_text())['entries']}
    inventory={r['condition_id']:r for r in json.loads((ROOT/'analysis/results/development/evidence-calibration-recovery-2026-09-30/paired-inventory.json').read_text())['records']}
    rows=[]
    for a in annotations:
        e=joins[a['case_id']];r=inventory[e['condition_id']]
        rows.append({**a,'condition_id':e['condition_id'],'configuration_id':e['configuration_id'],'episode_id':r['episode_id'],'family':r['family'],'method':e['method_id'],'paired_complete_episode':r['paired_complete_episode'],'covered_units':sum(u['communicated'] for u in a['required_units']),'required_unit_count':len(a['required_units'])})
    episodes={}
    for row in rows:
        if not row['paired_complete_episode']:continue
        identifier=(row['episode_id'],row['method']);e=episodes.setdefault(identifier,{'episode_id':row['episode_id'],'method':row['method'],'family':row['family'],'primary_failure':False,'covered_units':0,'required_unit_count':0,'condition_count':0,'violation_count':0})
        e['primary_failure']|=row['primary_failure'];e['covered_units']+=row['covered_units'];e['required_unit_count']+=row['required_unit_count'];e['condition_count']+=1;e['violation_count']+=len(row['primary_violations'])
    primary={'persistent_command_motion_discrepancy','measured_response_recovery'}
    summaries={}
    for population in ['all','primary']:
        selected=[v for v in episodes.values() if population=='all' or v['family'] in primary]
        methods={m:[e for e in selected if e['method']==m] for m in ['B2','B4','B4v3']}
        result={'methods':{},'comparisons':{}}
        for m,es in methods.items():
            result['methods'][m]={'observed_episode_n':len(es),'primary_failure_count':sum(e['primary_failure'] for e in es),'covered_units':sum(e['covered_units'] for e in es),'required_units':sum(e['required_unit_count'] for e in es),'episode_mean_coverage':sum(e['covered_units']/e['required_unit_count'] for e in es)/len(es) if es else None}
        for m in ['B4','B4v3']:
            m2={e['episode_id']:e for e in methods['B2']};m4={e['episode_id']:e for e in methods[m]};both=sorted(set(m2)&set(m4));b=sum(m2[i]['primary_failure'] and not m4[i]['primary_failure'] for i in both);c=sum(m4[i]['primary_failure'] and not m2[i]['primary_failure'] for i in both);n=len(both);d=b+c
            result['comparisons'][f'{m}-versus-B2']={'observed_paired_episode_n':n,'b2_fails_b4_passes':b,'b4_fails_b2_passes':c,'paired_risk_difference_B2_minus_B4':(b-c)/n if n else None,'descriptive_exact_one_sided_mcnemar_p':sum(math.comb(d,k) for k in range(b,d+1))/2**d if d else 1.,'descriptive_exact_two_sided_mcnemar_p':min(1.,2*sum(math.comb(d,k) for k in range(min(b,c)+1))/2**d) if d else 1.,'episode_mean_coverage_loss_B4_minus_B2':sum(m4[i]['covered_units']/m4[i]['required_unit_count']-m2[i]['covered_units']/m2[i]['required_unit_count'] for i in both)/n if n else None}
        summaries[population]=result
    levels={}
    for m in ['B2','B4','B4v3']:
        for level in ['E0','E1','E2','E3']:
            rs=[r for r in rows if r['method']==m and r['condition_id'].endswith(level) and r['paired_complete_episode']]
            levels[f'{m}/{level}']={'condition_n':len(rs),'primary_failures':sum(r['primary_failure'] for r in rs),'covered_units':sum(r['covered_units'] for r in rs),'required_units':sum(r['required_unit_count'] for r in rs)}
    complete=len(rows)==171 and not fails
    result={'scope':'DEVELOPMENT_ONLY','status':'COMPLETE_SINGLE_PASS' if complete else 'PARTIAL_NOT_EFFECT_ESTIMATE','annotation_pass':slot,'annotated_answer_count':len(rows),'expected_answer_count':171,'technical_annotation_failures':fails,'primary_family_values_found':sorted(set(r['family'] for r in rows)),'summaries':summaries,'evidence_levels':levels,'episode_rows':list(episodes.values()),'condition_rows':rows,'confirmation_n':0,'alpha_spent':0,'human_validation_claimed':False}
    (HERE/f'development-scoring-{slot}-v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['condition_rows','episode_rows']},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,default=HERE/'pilot-annotations-v1');ap.add_argument('--slot',default='A');a=ap.parse_args();summarize(a.directory,a.slot)
