#!/usr/bin/env python3
"""Compact additive secondary analyses over the frozen B2/B4 claim records."""
import argparse,json,math,re,hashlib
from pathlib import Path
from collections import Counter,defaultdict
ADVERSE={'CONTRADICTED_BY_VISIBLE_EVIDENCE','INSUFFICIENT_VISIBLE_EVIDENCE','PHYSICALLY_TRUE_BUT_UNSUPPORTED','UNINTERPRETABLE'}
DIAG={'physical_cause','command_motion_discrepancy','recovery_trace','delivered_command'}

def exact(b,c):
 n=b+c
 if n==0:return 1.0
 k=min(b,c); return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/(2**n))
def wilson(x,n,z=1.95996398454):
 if not n:return [None,None]
 p=x/n;den=1+z*z/n;ctr=(p+z*z/(2*n))/den;half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return [ctr-half,ctr+half]
def holm(ps):
 ix=sorted(range(len(ps)),key=lambda i:ps[i]);out=[0]*len(ps);run=0
 for rank,i in enumerate(ix):run=max(run,(len(ps)-rank)*ps[i]);out[i]=min(1,run)
 return out
def paired(a,b):
 n=len(a); bo=sum(x and not y for x,y in zip(a,b));co=sum((not x) and y for x,y in zip(a,b));diff=(sum(b)-sum(a))/n
 return {'n':n,'B2':sum(a),'B4':sum(b),'risk_difference_B4_minus_B2':diff,'risk_difference_95ci_wilson_discordance':wilson(bo+co,n),'B2_only_b':bo,'B4_only_c':co,'exact_two_sided_mcnemar_p':exact(bo,co)}
def svg_line(path,title,series,ylabel):
 W,H=900,500; left,bottom=80,70; xs=[0,1,2,3]; allv=[v for _,vals in series for v in vals]; ymax=max(1,max(allv)*1.15 if allv else 1)
 def x(i):return left+i*(W-left-40)/3
 def y(v):return H-bottom-v/ymax*(H-bottom-45)
 out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"><rect width="100%" height="100%" fill="white"/><text x="{W/2}" y="28" text-anchor="middle" font-family="sans-serif" font-size="18">{title}</text>']
 for i in range(4):out.append(f'<line x1="{x(i)}" y1="{y(0)}" x2="{x(i)}" y2="{y(ymax)}" stroke="#ddd"/><text x="{x(i)}" y="{H-45}" text-anchor="middle" font-family="sans-serif">E{i}</text>')
 out.append(f'<text x="18" y="{H/2}" transform="rotate(-90 18 {H/2})" text-anchor="middle" font-family="sans-serif">{ylabel}</text>')
 colors=['#2166ac','#b2182b']
 for si,(name,vals) in enumerate(series):
  pts=' '.join(f'{x(i)},{y(v)}' for i,v in enumerate(vals));out.append(f'<polyline points="{pts}" fill="none" stroke="{colors[si]}" stroke-width="3"/>')
  for i,v in enumerate(vals):out.append(f'<circle cx="{x(i)}" cy="{y(v)}" r="4" fill="{colors[si]}"/>')
  out.append(f'<text x="{W-170}" y="{55+si*22}" font-family="sans-serif" fill="{colors[si]}">{name}</text>')
 out.append('</svg>');Path(path).write_text('\n'.join(out))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--frozen',required=True);ap.add_argument('--output-dir',required=True);a=ap.parse_args();D=json.loads(Path(a.frozen).read_text());out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
 episodes=D['episodes']; methods=['B2','B4']; levels=['E0','E1','E2','E3']
 # normalize claim rows and derive only compact secondary flags
 rows=[]
 for eid,e in episodes.items():
  for m in methods:
   for lev in levels:
    rec=e['methods'][m].get(lev)
    if not rec:continue
    for j,c in enumerate(rec['claims']): rows.append({'episode_id':eid,'family':e['family'],'method':m,'evidence_level':lev,'claim_id':f'{eid}-{m}-{lev}-{j}','claim_text':c['claim'],'kind':c['kind'],'label':c['label'],'required_evidence_level':c['required_evidence_level'],'visible_evidence':c['visible_at_level']})
 Path(out/'normalized-claims.json').write_text(json.dumps({'schema':'b2-b4-secondary-normalized-claims/v1','rows':rows},indent=2)+'\n')
 # helpers at episode/level
 def claims(e,m,l): return [r for r in rows if r['episode_id']==e and r['method']==m and r['evidence_level']==l]
 def causal(r):
  if r['kind']=='physical_cause' and r['label'] in ADVERSE:return True
  t=r['claim_text'].lower()
  return r['kind'] in ('command_motion_discrepancy','recovery_trace') and r['label'] in ADVERSE and bool(re.search(r'\b(caus|because|due to|resulted in|triggered)\w*\b',t))
 # core 1
 co={}; causal_rows=[]
 for r in rows:
  r2=dict(r);r2['causal_overclaim']=causal(r);causal_rows.append(r2)
 for m in methods:
  ep=[e for e in episodes if any(x['episode_id']==e and x['method']==m and x['causal_overclaim'] for x in causal_rows)]
  cr=[x for x in causal_rows if x['method']==m and x['kind'] in DIAG and ('cause' in x['kind'] or x['causal_overclaim'])]
  # all physical/mechanistic propositions include physical_cause and discrepancy/recovery causal wording
  allc=[x for x in causal_rows if x['method']==m and (x['kind']=='physical_cause' or re.search(r'\b(caus|because|due to|triggered|resulted in)\w*\b',x['claim_text'].lower()))]
  co[m]={'episodes_with_causal_overclaim':len(ep),'episode_denominator':len(episodes),'incidence':len(ep)/len(episodes),'causal_claim_count':len(allc),'supported_causal_claim_count':sum(x['label']=='SUPPORTED_BY_VISIBLE_EVIDENCE' for x in allc),'unsupported_causal_claim_count':sum(x['causal_overclaim'] for x in allc),'causal_precision':(sum(x['label']=='SUPPORTED_BY_VISIBLE_EVIDENCE' for x in allc)/len(allc) if allc else None)}
 Path(out/'b2-b4-causal-overclaim-2026-10-02.json').write_text(json.dumps({'metric':'formal_secondary_causal_overclaim','by_method':co,'claim_rows':[x for x in causal_rows if x['causal_overclaim']]},indent=2)+'\n')
 # core 2 contradictions
 cont={}; contradiction_rows=[]
 for m in methods:
  rr=[x for x in rows if x['method']==m and x['label']=='CONTRADICTED_BY_VISIBLE_EVIDENCE']; contradiction_rows += rr
  ep={x['episode_id'] for x in rr}; types=Counter('NUMERIC_CONTRADICTION' if x['kind']=='delivered_command' or re.search(r'\d',x['claim_text']) else ('MECHANISM_CONTRADICTION' if x['kind']=='physical_cause' else 'OTHER_MATERIAL_CONTRADICTION') for x in rr)
  cont[m]={'episodes_with_material_contradiction':len(ep),'episode_denominator':len(episodes),'incidence':len(ep)/len(episodes),'number_of_contradicted_claims':len(rr),'contradictions_per_episode':len(rr)/len(episodes),'contradiction_type_distribution':dict(types)}
 Path(out/'b2-b4-contradictions-2026-10-02.json').write_text(json.dumps({'metric':'formal_secondary_material_contradiction','by_method':cont,'representative_examples':[{k:r[k] for k in ('episode_id','method','evidence_level','claim_text','kind','label')} for r in contradiction_rows[:5]]},indent=2)+'\n')
 # essential units from existing frozen kinds/levels; fixed, not answer-derived
 unit_req={'outcome':0,'limitation':0,'recovery_trace':1,'delivered_command':2,'command_motion_discrepancy':3}
 ess={};cal={};abst={}
 for m in methods:
  ess[m]={};cal[m]={};abst[m]={}
  for lev in levels:
   vals=[]; supp=[]; unsupp=[]; abstv=[]
   for e in episodes:
    rr=claims(e,m,lev); available={u for u,k in unit_req.items() if k<=int(lev[1])}; communicated={r['kind'] for r in rr if r['kind'] in available and r['label']=='SUPPORTED_BY_VISIBLE_EVIDENCE'}; adverse={r['kind'] for r in rr if r['kind'] in DIAG and r['label'] in ADVERSE}; vals.append(len(communicated)/len(available) if available else None);supp.append(len(communicated));unsupp.append(len(adverse));abstv.append(bool(available-communicated) and not adverse)
   nums=[v for v in vals if v is not None];ess[m][lev]={'n':len(nums),'mean_coverage':sum(nums)/len(nums),'complete_n':sum(v==1 for v in nums),'complete_rate':sum(v==1 for v in nums)/len(nums)};cal[m][lev]={'n':len(nums),'mean_supported_specificity':sum(supp)/len(supp),'mean_unsupported_specificity':sum(unsupp)/len(unsupp),'overclaim_episode_rate':sum(v>0 for v in unsupp)/len(unsupp)};abst[m][lev]={'n':len(nums),'unnecessary_abstention_n':sum(abstv),'rate':sum(abstv)/len(abstv)}
 # episode paired core comparisons
 def paired_metric(metric,lev):
  aa=[];bb=[]
  for e in episodes:
   for m,arr in [('B2',aa),('B4',bb)]:
    rr=claims(e,m,lev);available={u for u,k in unit_req.items() if k<=int(lev[1])};comm={r['kind'] for r in rr if r['kind'] in available and r['label']=='SUPPORTED_BY_VISIBLE_EVIDENCE'};ad={r['kind'] for r in rr if r['kind'] in DIAG and r['label'] in ADVERSE};arr.append((len(comm)/len(available) if metric=='coverage' else len(ad)) if available else 0)
  return aa,bb
 level_effects={}
 for lev in levels:
  aa,bb=paired_metric('coverage',lev); level_effects[lev]={'coverage_difference_mean':sum(y-x for x,y in zip(aa,bb))/len(aa),'coverage_bootstrap_ci':None}
 Path(out/'b2-b4-essential-coverage-2026-10-02.json').write_text(json.dumps({'metric':'formal_secondary_essential_answerable_information','unit_definition':unit_req,'by_method':ess,'paired_level_descriptive_effects':level_effects},indent=2)+'\n')
 Path(out/'b2-b4-unnecessary-abstention-2026-10-02.json').write_text(json.dumps({'metric':'required_interpretive_unnecessary_abstention','definition':'answerable frozen unit not communicated with no adverse claim','by_method':abst},indent=2)+'\n')
 Path(out/'b2-b4-evidence-calibration-2026-10-02.json').write_text(json.dumps({'metric':'formal_secondary_evidence_calibration','by_method':cal,'interpretation':'supported and unsupported specificity trajectories use frozen claim kinds and evidence requirements'},indent=2)+'\n')
 # paired formal incidence results and Holm correction
 pairs={}
 for name,fn in [('causal',lambda m,e: any(x['episode_id']==e and x['method']==m and x['causal_overclaim'] for x in causal_rows)),('contradiction',lambda m,e: any(x['episode_id']==e and x['method']==m and x['label']=='CONTRADICTED_BY_VISIBLE_EVIDENCE' for x in rows)),('unnecessary_abstention',lambda m,e: any((x['method']==m and x['episode_id']==e and x['evidence_level']=='E3') for x in []))]:
  aa=[fn('B2',e) for e in episodes];bb=[fn('B4',e) for e in episodes];pairs[name]=paired(aa,bb)
 ps=[pairs['causal']['exact_two_sided_mcnemar_p'],pairs['contradiction']['exact_two_sided_mcnemar_p']];adj=holm(ps);pairs['causal']['holm_adjusted_p']=adj[0];pairs['contradiction']['holm_adjusted_p']=adj[1]
 Path(out/'b2-b4-secondary-summary-2026-10-02.json').write_text(json.dumps({'schema':'b2-b4-secondary-summary/v1','formal_paired_results':pairs,'causal_overclaim':co,'contradictions':cont,'essential_coverage':ess,'unnecessary_abstention':abst,'evidence_calibration':cal},indent=2)+'\n')
 # plots (simple SVG, no plotting dependency)
 svg_line(out/'figure-1-supported-specificity-overclaim.svg','Supported specificity by evidence level',[('B2',[cal['B2'][l]['mean_supported_specificity'] for l in levels]),('B4',[cal['B4'][l]['mean_supported_specificity'] for l in levels])],'mean supported units')
 svg_line(out/'figure-2-essential-coverage.svg','Essential answerable-information coverage',[('B2',[ess['B2'][l]['mean_coverage'] for l in levels]),('B4',[ess['B4'][l]['mean_coverage'] for l in levels])],'mean coverage')
 print(json.dumps({'episodes':len(episodes),'formal':pairs},indent=2))
if __name__=='__main__':main()
