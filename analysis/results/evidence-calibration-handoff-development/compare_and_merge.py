#!/usr/bin/env python3
"""Combine retained development-only reviews, preserving every initial pass as sensitivity."""
import collections,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
def read_annotations(directory,slot):
 rows=[]
 for f in sorted((HERE/directory).glob(f'{slot}-batch-*.json')):
  if f.name.endswith('.request.json'):continue
  d=json.loads(f.read_text())
  if d['status']!='STRUCTURALLY_VALID_SUPPORT_RETURN':raise ValueError(f'Technical failure: {f}')
  rows+=d['parsed_final']['annotations']
 return {r['case_id']:r for r in rows}
def binomial_interval(k,n,tail=.0125):
 def upper_tail(p):return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k,n+1))
 def lower_tail(p):return sum(math.comb(n,j)*p**j*(1-p)**(n-j) for j in range(k+1))
 low=0.;high=1.
 if k:
  lo,hi=0.,1.
  for _ in range(80):
   mid=(lo+hi)/2
   if upper_tail(mid)<tail:lo=mid
   else:hi=mid
  low=(lo+hi)/2
 if k<n:
  lo,hi=0.,1.
  for _ in range(80):
   mid=(lo+hi)/2
   if lower_tail(mid)>tail:lo=mid
   else:hi=mid
  high=(lo+hi)/2
 return low,high

def paired_interval(b,c,n):
 if b+c==0:return [-(1-.05**(1/n)),1-.05**(1/n)]
 bl,bu=binomial_interval(b,n);cl,cu=binomial_interval(c,n)
 return [bl-cu,bu-cl]

def main():
 a=read_annotations('pilot-annotations-v1','A');b=read_annotations('pilot-annotations-v1','B');c=read_annotations('corrected-review-v2','C');v4=read_annotations('v4-annotations-v2','A');v5=read_annotations('v5-annotations-v2','A')
 wanted={r['case_id'] for r in json.loads((HERE/'corrected-review-cases-v2.json').read_text())['cases']}
 if len(a)!=171 or len(b)!=171 or set(c)!=wanted or len(v5)!=57:raise ValueError('Not all prioritized annotation calls complete')
 joins={e['response_id']:e for e in json.loads((HERE/'development-join-key-v3.json').read_text())['entries']}
 inv={r['condition_id']:r for r in json.loads((ROOT/'analysis/results/development/evidence-calibration-recovery-2026-09-30/paired-inventory.json').read_text())['records']}
 disagreement={'condition_primary_disagreements':sum(a[i]['primary_failure']!=b[i]['primary_failure'] for i in a),'condition_coverage_disagreements':sum({u['unit_id']:u['communicated'] for u in a[i]['required_units']}!={u['unit_id']:u['communicated'] for u in b[i]['required_units']} for i in a),'required_unit_disagreements':sum({u['unit_id']:u['communicated'] for u in a[i]['required_units']}[v['unit_id']]!=v['communicated'] for i in a for v in b[i]['required_units']),'required_unit_count_per_pass':sum(len(r['required_units']) for r in a.values()),'corrected_review_count':len(c),'corrected_review_primary_changes_from_A':sum(c[i]['primary_failure']!=a[i]['primary_failure'] for i in c)}
 final={**a,**c,**v4,**v5};rows=[]
 for identifier,r in final.items():
  e=joins[identifier];v=inv[e['condition_id']]
  rows.append({**r,'method':e['method_id'],'condition_id':e['condition_id'],'episode_id':v['episode_id'],'configuration_id':e['configuration_id'],'family':v['family'],'paired_complete_episode':v['paired_complete_episode'],'annotation_procedure':'corrected_review_v2' if identifier in c else 'qualified_v2' if identifier in v4 or identifier in v5 else 'both_v1_agree_no_flag','covered_units':sum(u['communicated'] for u in r['required_units']),'required_unit_count':len(r['required_units'])})
 episodes={}
 for r in rows:
  if not r['paired_complete_episode']:continue
  key=(r['episode_id'],r['method']);v=episodes.setdefault(key,{'episode_id':r['episode_id'],'method':r['method'],'family':r['family'],'primary_failure':False,'covered_units':0,'required_units':0,'condition_n':0})
  v['primary_failure']|=r['primary_failure'];v['covered_units']+=r['covered_units'];v['required_units']+=r['required_unit_count'];v['condition_n']+=1
 summary={}
 methods=['B2','B4','B4v3','B4v4','B4v5']
 for population in ['all','primary']:
  selected=[e for e in episodes.values() if population=='all' or e['family'] in ['persistent_command_motion_discrepancy','measured_response_recovery']]
  m={name:{e['episode_id']:e for e in selected if e['method']==name} for name in methods};report={'methods':{},'comparisons':{}}
  for name,es in m.items():
   report['methods'][name]={'n':len(es),'primary_failure_count':sum(e['primary_failure'] for e in es.values()),'failure_rate':sum(e['primary_failure'] for e in es.values())/len(es) if es else None,'required_unit_coverage':sum(e['covered_units'] for e in es.values())/sum(e['required_units'] for e in es.values()) if es else None,'covered_units':sum(e['covered_units'] for e in es.values()),'required_units':sum(e['required_units'] for e in es.values()),'episode_mean_coverage':sum(e['covered_units']/e['required_units'] for e in es.values())/len(es) if es else None}
  for name in methods[1:]:
   ids=sorted(set(m['B2'])&set(m[name]));n=len(ids);bf=sum(m['B2'][i]['primary_failure'] and not m[name][i]['primary_failure'] for i in ids);cf=sum(m[name][i]['primary_failure'] and not m['B2'][i]['primary_failure'] for i in ids);d=bf+cf
   report['comparisons'][name]={'paired_n':n,'B2_fails_B4_passes':bf,'B4_fails_B2_passes':cf,'absolute_paired_risk_difference_B2_minus_B4':(bf-cf)/n if n else None,'exact_one_sided_p_descriptive_only':sum(math.comb(d,k) for k in range(bf,d+1))/2**d if d else 1.,'exact_two_sided_p_descriptive_only':min(1.,2*sum(math.comb(d,k) for k in range(min(bf,cf)+1))/2**d) if d else 1.,'whole_episode_conservative_95_ci':paired_interval(bf,cf,n) if n else None,'coverage_difference_B4_minus_B2':sum(m[name][i]['covered_units']/m[name][i]['required_units']-m['B2'][i]['covered_units']/m['B2'][i]['required_units'] for i in ids)/n if n else None}
  summary[population]=report
 levels={}
 for name in methods:
  for level in range(4):
   selected=[r for r in rows if r['method']==name and r['paired_complete_episode'] and r['condition_id'].endswith(f'-E{level}')]
   levels[f'{name}/E{level}']={'conditions':len(selected),'failures':sum(r['primary_failure'] for r in selected),'covered_units':sum(r['covered_units'] for r in selected),'required_units':sum(r['required_unit_count'] for r in selected)}
 decomposition={}
 for name in methods:
  selected=[r for r in rows if r['method']==name and r['paired_complete_episode']]
  primary=[r for r in selected if r['family'] in ['persistent_command_motion_discrepancy','measured_response_recovery']]
  decomposition[name]={'all_condition_violations_by_kind':dict(collections.Counter(v['kind'] for r in selected for v in r['primary_violations'])),'primary_condition_violations_by_kind':dict(collections.Counter(v['kind'] for r in primary for v in r['primary_violations'])),'factual_numeric_error_conditions_secondary':sum(bool(r['factual_numeric_errors']) for r in selected),'unsupported_specific_physical_mechanism_conditions':sum(any(v['kind']=='unsupported_mechanism' for v in r['primary_violations']) for r in selected)}
 result={'scope':'DEVELOPMENT_ONLY','human_validation_claimed':False,'confirmation_n':0,'alpha_spent':0,'status':'COMPLETE_INITIAL_PAIRED_DEVELOPMENT_WITH_CORRECTED_MEASUREMENT_AND_VERSIONED_METHODS','measurement_limitations':'Automated same-model independent passes. Initial prompt conflated software recovery with measured recovery and omitted public API code context; corrected with fresh qualification and retained reannotation. All initial passes remain sensitivity evidence. No human validation claimed.','agreement':disagreement,'decomposition':decomposition,'technical_missingness':{'initial_prepared_episodes':16,'complete_paired_episodes':15,'primary_complete_paired_episodes':11,'technical_failure_episode':'cm-land-conf-042','missing_B2_conditions':['cm-land-conf-042-E0','cm-land-conf-042-E1','cm-land-conf-042-E2'],'valid_E3_retained_descriptive_only':True,'reason':'Unknown retired B2 request/cache technical state; no performance-driven retry or episode replacement.'},'summaries':summary,'evidence_levels':levels,'episode_rows':list(episodes.values()),'condition_rows':rows,'interval_method':'Nonzero discordances: project simultaneous97.5% exact Clopper-Pearson intervals on each discordant direction via Bonferroni (paired category count denominators are whole episodeN). Zero discordances: exact95% bound on discordance rate. Conservative intervals throughout.', 'zero_discordance_CI':'Exact one-sided95% upper bound on discordance probability is1-0.05^(1/n); absolute paired risk difference cannot exceed that probability. Symmetric bound gives conservative >=95% whole-episode interval, avoiding misleading zero-width bootstrap intervals.'}
 if (HERE/'v5-second-pass-agreement-v2.json').exists():result['v5_independent_second_pass']=json.loads((HERE/'v5-second-pass-agreement-v2.json').read_text())
 (HERE/'initial-paired-development-final-v2.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'agreement':disagreement,'decomposition':decomposition,'technical_missingness':{'initial_prepared_episodes':16,'complete_paired_episodes':15,'primary_complete_paired_episodes':11,'technical_failure_episode':'cm-land-conf-042','missing_B2_conditions':['cm-land-conf-042-E0','cm-land-conf-042-E1','cm-land-conf-042-E2'],'valid_E3_retained_descriptive_only':True,'reason':'Unknown retired B2 request/cache technical state; no performance-driven retry or episode replacement.'},'summaries':summary},indent=2))
if __name__=='__main__':main()
