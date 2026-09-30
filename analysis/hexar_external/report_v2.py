#!/usr/bin/env python3
"""Single descriptive paired report; no p-values or alpha allocation."""
import argparse,csv,json,math,statistics,sys
from collections import defaultdict
from audit_release import ROOT,sha,write
from study_v2 import V2,CONDITIONS
sys.path.insert(0,str(ROOT/'analysis'))
from adjudicate_evidence_calibration_annotations import _values
from scipy.stats import t
METHODS=('HX-ORIGINAL','HX-PROMPT','HX-CONTRACT')
def score(values,atoms):
 claims=[values['claim:'+a['item_id']] for a in atoms]
 units=[v for k,v in values.items() if k.startswith('unit:')];limits=[v for k,v in values.items() if k.startswith('limitation:')]
 unresolved=any(c=='UNINTERPRETABLE' for c in claims)
 unsupported=any(c not in ('SUPPORTED_BY_VISIBLE_EVIDENCE','UNINTERPRETABLE') for c in claims)
 causal=[values['claim:'+a['item_id']] for a in atoms if a['asserted_abstraction_level']=='specific_physical_cause']
 return {'success':None if unresolved else all(units) and all(limits) and not unsupported,'coverage':sum(units)/len(units),'unsupported_material':unsupported,'unsupported_physical_cause':any(c!='SUPPORTED_BY_VISIBLE_EVIDENCE' for c in causal),'unnecessary_blanket_abstention':bool(atoms) and all(a['asserted_abstraction_level']=='limitation' for a in atoms) and not all(units),'scope_preserved':all(limits),'units':units,'unresolved':unresolved}
def interval(values):
 if len(values)<2:return None
 mean=statistics.mean(values);half=float(t.ppf(.975,len(values)-1))*statistics.stdev(values)/math.sqrt(len(values))
 return [max(-1,mean-half),min(1,mean+half)]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--cohort',choices=['development','reserved'],required=True);a=ap.parse_args()
 base=V2/a.cohort;ann=base/'annotation';key=json.loads((ann/'join_key.evaluator-only.json').read_text())['key'];inv={x['response_id']:x['atoms'] for x in json.loads((ann/'atomic_inventory.json').read_text())['items']}
 rows=[];disagreements=decisions=claims=agreed_claims=0
 for k in key:
  d=ann/'judgments'/k['response_id'];record={**k,'success':None,'technical_failure':False}
  disposition=json.loads((d/'external-summary.json').read_text()) if (d/'external-summary.json').exists() else {}
  if k['status']!='VALID' or not (d/'final.json').exists() or disposition.get('status')!='EXTERNAL_V2_AGENT_ASSESSED_QUALIFIED':record['technical_failure']=True;rows.append(record);continue
  final=json.loads((d/'final.json').read_text());record.update(score(final['final_decisions'],inv[k['response_id']]))
  for slot in ('A','B'):record['success_'+slot]=score(_values(json.loads((d/f'annotation-{slot}.json').read_text())),inv[k['response_id']])['success']
  agreement=json.loads((d/'agreement.json').read_text());disagreements+=agreement['disagreement_count'];decisions+=agreement['decision_count'];cl=agreement['claim_label_agreement'];claims+=cl['claim_count'];agreed_claims+=round(cl['claim_count']*cl['observed_agreement'])
  rows.append(record)
 families={r['recording_id']:r['situation_family'] for r in json.loads((base/'accounting.evaluator-only.json').read_text())['records']};recordings=sorted(families);scores=[]
 for rid in recordings:
  r={'recording_id':rid,'family':families[rid]}
  for m in METHODS:
   jobs=[x for x in rows if x['recording_id']==rid and x['method']==m];assert len(jobs)==9
   known=[x['success'] for x in jobs if x['success'] is not None];r[m]=None if len(known)!=9 else sum(known)/9;r[m+'_bounds']=[sum(known)/9,(sum(known)+9-len(known))/9]
   for slot in ('A','B'):
    vals=[x.get('success_'+slot) for x in jobs];r[m+'_'+slot]=None if any(v is None for v in vals) else sum(vals)/9
  scores.append(r)
 delta=[r['HX-CONTRACT']-r['HX-PROMPT'] for r in scores if r['HX-CONTRACT'] is not None and r['HX-PROMPT'] is not None]
 family_d=defaultdict(list)
 for r in scores:
  if r['HX-CONTRACT'] is not None and r['HX-PROMPT'] is not None:family_d[r['family']].append(r['HX-CONTRACT']-r['HX-PROMPT'])
 fd=[statistics.mean(v) for v in family_d.values()]
 summary={}
 for m in METHODS:
  jobs=[r for r in rows if r['method']==m];known=[r for r in jobs if r['success'] is not None];annotated=[r for r in jobs if 'coverage' in r];responses=[json.loads(p.read_text()) for p in (base/'responses').glob('*-'+m+'.json')]
  consistency=[]
  for rid in recordings:
   for q in ('q1','q2','q3'):
    pair=[r for r in jobs if r['recording_id']==rid and r['question_id']==q and r['condition'] in ('intact','irrelevant_removal')]
    if all(r['success'] is not None for r in pair):consistency.append(pair[0]['success']==pair[1]['success'] and pair[0]['units']==pair[1]['units'])
  summary[m]={'success':sum(r['success'] for r in known)/len(known) if known else None,'fixed_denominator_bounds':[sum(r['success'] for r in known)/len(jobs),(sum(r['success'] for r in known)+len(jobs)-len(known))/len(jobs)],'n_jobs':len(jobs),'unresolved_or_technical':len(jobs)-len(known),'unsupported_material_fixed_denominator_bounds':[sum(r['unsupported_material'] for r in annotated)/len(jobs),(sum(r['unsupported_material'] for r in annotated)+sum(r['unresolved'] and not r['unsupported_material'] for r in annotated)+len(jobs)-len(annotated))/len(jobs)],'unsupported_material_rate':statistics.mean(r['unsupported_material'] for r in annotated) if annotated else None,'unsupported_physical_cause_rate':statistics.mean(r['unsupported_physical_cause'] for r in annotated) if annotated else None,'coverage':statistics.mean(r['coverage'] for r in annotated) if annotated else None,'unnecessary_blanket_abstention_rate':statistics.mean(r['unnecessary_blanket_abstention'] for r in annotated) if annotated else None,'median_answer_words':statistics.median(len(r.get('answer','').split()) for r in responses),'intact_success':statistics.mean(r['success'] for r in known if r['condition']=='intact') if known else None,'evidence_success_bounds':{c:[sum(r['success'] for r in jobs if r['condition']==c and r['success'] is not None)/sum(r['condition']==c for r in jobs),(sum(r['success'] for r in jobs if r['condition']==c and r['success'] is not None)+sum(r['condition']==c and r['success'] is None for r in jobs))/sum(r['condition']==c for r in jobs)] for c in CONDITIONS},'evidence_success':{c:statistics.mean(r['success'] for r in known if r['condition']==c) if any(r['condition']==c for r in known) else None for c in CONDITIONS},'irrelevant_required_semantic_consistency':statistics.mean(consistency) if consistency else None,'template_rate':statistics.mean(r.get('template',False) for r in responses),'fallback_rate':statistics.mean(r.get('fallback',False) for r in responses),'median_runtime_ms':statistics.median(r['end_to_end_ms'] for r in responses),'cost_usd':None,'cost_status':'not reported by hosted transport'}
 pass_effect={};pass_bounds={};common_pass=[r for r in scores if all(r[m+'_'+slot] is not None for m in ('HX-CONTRACT','HX-PROMPT') for slot in ('A','B')) and r['HX-CONTRACT'] is not None and r['HX-PROMPT'] is not None]
 for slot in ('A','B'):
  ds=[r['HX-CONTRACT_'+slot]-r['HX-PROMPT_'+slot] for r in common_pass];pass_effect[slot]=statistics.mean(ds) if ds else None
  limits={}
  for m in ('HX-CONTRACT','HX-PROMPT'):
   jobs=[r for r in rows if r['method']==m];vals=[r.get('success_'+slot) for r in jobs];known=[v for v in vals if v is not None];limits[m]=[sum(known)/len(vals),(sum(known)+len(vals)-len(known))/len(vals)]
  pass_bounds[slot]=[limits['HX-CONTRACT'][0]-limits['HX-PROMPT'][1],limits['HX-CONTRACT'][1]-limits['HX-PROMPT'][0]]
 result={'schema':'hexar-descriptive-paired-results/v2','cohort':a.cohort,'primary_endpoint':'recording mean useful supported-answer success, nine fixed jobs','independent_recordings':len(recordings),'paired_complete_recordings':len(delta),'physical_families':len(set(families.values())),'family_clusters':len(family_d),'methods':summary,'primary_full_cohort_effect_bounds':[statistics.mean(r['HX-CONTRACT_bounds'][0]-r['HX-PROMPT_bounds'][1] for r in scores),statistics.mean(r['HX-CONTRACT_bounds'][1]-r['HX-PROMPT_bounds'][0] for r in scores)],'primary_effect':statistics.mean(delta) if delta else None,'descriptive_recording_t95':interval(delta),'descriptive_family_t95':interval(fd) if len(delta)==len(recordings) and len(family_d)==len(set(families.values())) else None,'family_interval_requires_complete_declared_cohort':True,'paired_recording_differences':delta,'favorable_recordings':sum(d>0 for d in delta),'unfavorable_recordings':sum(d<0 for d in delta),'tied_recordings':sum(d==0 for d in delta),'alpha_allocated':0,'alpha_consumed':0,'confirmatory':False,'p_value':None,'statistically_supported_improvement_claim':False,'annotation':{'agent_assessed':True,'human_validated':False,'decision_disagreements':disagreements,'decisions':decisions,'claim_agreement':agreed_claims/claims if claims else None,'pass_effects':pass_effect,'pass_common_complete_recordings':len(common_pass),'pass_full_cohort_effect_bounds':pass_bounds,'inventory_qualified':False},'population':'declared released navigation situations; known-family bag split','uncertainty_limits':'Descriptive conditional t intervals; finite non-random public sample, hosted model immutability unknown, shared family mechanisms. No confirmatory inference.'}
 write(base/'results.json',result);write(base/'scored_jobs.evaluator-only.json',{'rows':rows});write(base/'recording_scores.json',{'recordings':scores})
 lines=['| Method | Useful supported success bounds | Unsupported material | Coverage | Intact success |','|---|---:|---:|---:|---:|']
 def fmt(v):return 'pending' if v is None else f'{100*v:.1f}%'
 for m,s in summary.items():
  bounds=s['fixed_denominator_bounds'];success=fmt(bounds[0]) if bounds[0]==bounds[1] else fmt(bounds[0])+'–'+fmt(bounds[1])
  lines.append(f"| {m} | {success} | {fmt(s['unsupported_material_rate'])} | {fmt(s['coverage'])} | {fmt(s['intact_success'])} |")
 (base/'result_table.md').write_text('\n'.join(lines)+'\n')
 import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
 fig,ax=plt.subplots(figsize=(6.7,3));colors=['#818896','#dc9b35','#277d86'];width=.24
 for i,m in enumerate(METHODS):
  bounds=[summary[m]['evidence_success_bounds'][c] for c in CONDITIONS];vals=[b[0] for b in bounds]
  ax.bar([j+(i-1)*width for j in range(3)],vals,width,label=m,color=colors[i],yerr=[[0]*3,[b[1]-b[0] for b in bounds]],capsize=2)
 ax.set(ylim=(0,1.08),ylabel='Useful supported answers',xticks=range(3),xticklabels=['Intact','Irrelevant removal','Diagnostic removal']);ax.legend(loc='upper center',ncol=3,fontsize=8);fig.tight_layout()
 for ext in ('svg','png'):fig.savefig(base/f'evidence_results.{ext}',dpi=180)
 print(json.dumps(result),flush=True)
if __name__=='__main__':main()
