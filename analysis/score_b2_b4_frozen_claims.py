#!/usr/bin/env python3
"""Method-independent deterministic claim/evidence scoring for retained B2/B4 answers.

The rubric only sees answer text, the evaluator-independent reference's robot-visible
facts, and the declared ladder level. It never reads B4 clauses/metadata. It is a
transparent frozen comparison adapter, not a replacement for qualified blinded
agent annotation.
"""
import argparse,json,re,hashlib,math,random
from pathlib import Path
from collections import Counter,defaultdict
LEVEL={'E0':0,'E1':1,'E2':2,'E3':3}
CAUSE=re.compile(r'\b(motor|actuator|wheel slip|slip|collision|obstruction|blocked by|physical cause|hardware fault|mechanical|controller fault|encoder fault|sensor fault)\b',re.I)
DISCREP=re.compile(r'command.{0,35}(measured|motion|odometr)|(?:motion|odometr|measured).{0,35}command|command[–-]motion|discrepancy|reflected in measured',re.I)
CMD=re.compile(r'\b(command|delivered|velocity|m/s)\b',re.I)
RECOV=re.compile(r'\b(recover|recovery|wait|retry|followpath|re-?plan)\b',re.I)
OUTCOME=re.compile(r'\b(goal|task|action|navigation|run|episode).{0,20}\b(success|succeed|failed|failure|aborted|active|completed|result)\b|\b(success|succeed|failed|failure|aborted|active|completed)\b',re.I)
NEG=re.compile(r'\b(no|lack|lacks|not|never|cannot|can\s+not|does\s+not|did\s+not|without|unresolved|unknown|unable)\b',re.I)
NUM=re.compile(r'(?<!\w)(\d+(?:\.\d+)?)(?:\s*(m/s|s))?',re.I)

def split_claims(text):
    # Preserve clause-level atomicity around semicolons and sentence boundaries.
    return [x.strip(' -*') for x in re.split(r'(?<=[.!?])\s+|\s*;\s*',text) if x.strip(' -*')]

def classify(clause,level,ref):
    low=clause.lower(); neg=bool(NEG.search(clause)); req=None; kind='UNINTERPRETABLE'
    # Explicit epistemic limitations are claims about unavailable support, not
    # assertions of the unavailable mechanism itself.
    limitation = neg and (any(x in low for x in ('lack', 'lacks', 'does not establish', 'not establish', 'does not identify', 'cannot establish', 'unresolved', 'not observed', 'without separate')) or low.startswith('no '))
    if limitation:
        req='E0'; kind='limitation'
    elif CAUSE.search(clause) and not neg:
        req='E3';kind='physical_cause'
    elif DISCREP.search(clause):
        req='E3';kind='command_motion_discrepancy'
    elif CMD.search(clause) and (NUM.search(clause) or 'command' in low or 'delivered' in low):
        req='E2';kind='delivered_command'
    elif RECOV.search(clause):
        req='E1';kind='recovery_trace'
    elif OUTCOME.search(clause) or any(x in low for x in ('navigation progress','diagnosis is','strongest supported diagnosis')):
        req='E0';kind='outcome'
    else:
        req='E0';kind='other'
    if kind=='limitation': label='SUPPORTED_BY_VISIBLE_EVIDENCE'
    elif kind=='physical_cause':
        # Evaluator truth is not used to create support. No retained reference exposes a unique cause.
        label='INSUFFICIENT_VISIBLE_EVIDENCE' if LEVEL[level] < LEVEL[req] else 'PHYSICALLY_TRUE_BUT_UNSUPPORTED'
    elif LEVEL[level] < LEVEL[req]:
        label='INSUFFICIENT_VISIBLE_EVIDENCE'
    elif kind=='UNINTERPRETABLE': label='UNINTERPRETABLE'
    else: label='SUPPORTED_BY_VISIBLE_EVIDENCE'
    # Check explicit numerical claims against visible reference quantities when available.
    if label=='SUPPORTED_BY_VISIBLE_EVIDENCE' and kind in ('command_motion_discrepancy','delivered_command'):
        vals=[float(x[0]) for x in NUM.findall(clause)]
        expected=[]
        rr=ref.get('result',{})
        for key in ('discrepancy_commanded_planar_speed_mps','discrepancy_measured_planar_speed_mps','recovered_measured_planar_speed_mps','response_ratio'):
            if rr.get(key) is not None: expected.append(float(rr[key]))
        if vals and expected and all(min(abs(v-e) for e in expected)>max(.02,.15*abs(v)) for v in vals): label='CONTRADICTED_BY_VISIBLE_EVIDENCE'
    return {'claim':clause,'kind':kind,'required_evidence_level':req,'visible_at_level':LEVEL[level]>=LEVEL[req],'label':label}

def load_answers(base,method):
    out={}
    for p in (base/method).glob('*.json'):
        d=json.loads(p.read_text()); cid=d.get('condition_id',''); m=re.match(r'^(.*)-(E[0-3])$',cid)
        if m: out[(m.group(1),m.group(2))]=d
    return out

def exact_binom_two_sided(b,c):
    n=b+c
    if n==0:return 1.0
    k=min(b,c); s=sum(math.comb(n,i) for i in range(k+1)); return min(1,2*s/(2**n))

def wilson(x,n,z=1.95996398454):
    if not n:return [None,None]
    p=x/n; den=1+z*z/n; ctr=(p+z*z/(2*n))/den; half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den; return [ctr-half,ctr+half]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--worktree-root',required=True);ap.add_argument('--output',required=True);a=ap.parse_args();root=Path(a.worktree_root);base=root/'model_outputs/evidence-calibration-b4-b2-confirmation-2026-10-01'; b2=load_answers(base,'b2');b4=load_answers(base,'b4'); refs=root/'data/evaluator_only/final'
    common=sorted({e for e,l in b2}&{e for e,l in b4}); result={'schema':'crane-method-independent-frozen-claim-score/v1','rubric':'answer text + robot-visible ladder facts; B4 metadata/clauses excluded','episodes':{},'method_level':{},'warnings':[]}
    for e in common:
      rp=refs/e/'command-motion-independent-reference-v1.json'; ref=json.loads(rp.read_text()) if rp.exists() else {'result':{}}
      er={'family':b2[(e,next(l for l in ('E0','E1','E2','E3') if (e,l) in b2))].get('family'),'methods':{}}
      for method,src in [('B2',b2),('B4',b4)]:
       er['methods'][method]={}
       for level in ('E0','E1','E2','E3'):
        if (e,level) not in src:continue
        claims=[classify(c,level,ref) for c in split_claims(src[(e,level)].get('answer',''))]
        adverse=[c for c in claims if c['label'] in ('CONTRADICTED_BY_VISIBLE_EVIDENCE','INSUFFICIENT_VISIBLE_EVIDENCE','PHYSICALLY_TRUE_BUT_UNSUPPORTED','UNINTERPRETABLE') and c['kind']!='limitation']
        er['methods'][method][level]={'claims':claims,'failure':bool(adverse),'adverse_claim_count':len(adverse),'label_counts':dict(Counter(c['label'] for c in claims))}
       # fixed-ladder endpoint: failure anywhere on its ladder
       er['methods'][method]['episode_failure']=any(er['methods'][method].get(l,{}).get('failure',False) for l in ('E0','E1','E2','E3'))
      result['episodes'][e]=er
    for method in ('B2','B4'):
      for level in ('E0','E1','E2','E3'):
       vals=[x['methods'][method][level]['failure'] for x in result['episodes'].values() if level in x['methods'][method]]
       result['method_level'][f'{method}_{level}']={'n':len(vals),'failures':sum(vals),'failure_rate':sum(vals)/len(vals) if vals else None,'wilson_95ci':wilson(sum(vals),len(vals))}
      vals=[x['methods'][method]['episode_failure'] for x in result['episodes'].values()];result['method_level'][f'{method}_episode_any_ladder']={'n':len(vals),'failures':sum(vals),'failure_rate':sum(vals)/len(vals),'wilson_95ci':wilson(sum(vals),len(vals))}
    pairs=[x for x in result['episodes'].values() if 'episode_failure' in x['methods']['B2'] and 'episode_failure' in x['methods']['B4']]; b=sum(x['methods']['B2']['episode_failure'] and not x['methods']['B4']['episode_failure'] for x in pairs); c=sum((not x['methods']['B2']['episode_failure']) and x['methods']['B4']['episode_failure'] for x in pairs); d=len(pairs); result['paired_episode_comparison']={'n':d,'B2_failure':sum(x['methods']['B2']['episode_failure'] for x in pairs),'B4_failure':sum(x['methods']['B4']['episode_failure'] for x in pairs),'B2_only_failure_b':b,'B4_only_failure_c':c,'risk_difference_B4_minus_B2':sum(x['methods']['B4']['episode_failure']-x['methods']['B2']['episode_failure'] for x in pairs)/d,'exact_two_sided_mcnemar_p':exact_binom_two_sided(b,c),'discordance_wilson_95ci':wilson(b+c,d)}
    level_pairs={}
    for level in ('E0','E1','E2','E3'):
      pp=[x for x in result['episodes'].values() if level in x['methods']['B2'] and level in x['methods']['B4']]
      bb=sum(x['methods']['B2'][level]['failure'] and not x['methods']['B4'][level]['failure'] for x in pp); cc=sum((not x['methods']['B2'][level]['failure']) and x['methods']['B4'][level]['failure'] for x in pp); nn=len(pp)
      level_pairs[level]={'n':nn,'B2_failures':sum(x['methods']['B2'][level]['failure'] for x in pp),'B4_failures':sum(x['methods']['B4'][level]['failure'] for x in pp),'B2_only_failure_b':bb,'B4_only_failure_c':cc,'risk_difference_B4_minus_B2':sum(int(x['methods']['B4'][level]['failure'])-int(x['methods']['B2'][level]['failure']) for x in pp)/nn,'exact_two_sided_mcnemar_p':exact_binom_two_sided(bb,cc),'discordance_wilson_95ci':wilson(bb+cc,nn)}
    result['paired_level_comparisons']=level_pairs
    accounting_path=root/'analysis/results/confirmation/evidence-calibration-b4-b2-confirmation-2026-10-01/execution-accounting-FIRST.json'
    if accounting_path.exists():
      complete_ids={r['run_id'] for r in json.loads(accounting_path.read_text()).get('records',[]) if r.get('complete_pair') is True}
      cp=[(e,x) for e,x in result['episodes'].items() if e in complete_ids and 'episode_failure' in x['methods']['B2'] and 'episode_failure' in x['methods']['B4']]
      bb=sum(x['methods']['B2']['episode_failure'] and not x['methods']['B4']['episode_failure'] for _,x in cp); cc=sum((not x['methods']['B2']['episode_failure']) and x['methods']['B4']['episode_failure'] for _,x in cp); nn=len(cp)
      result['accounting_complete_sensitivity']={'n':nn,'B2_failures':sum(x['methods']['B2']['episode_failure'] for _,x in cp),'B4_failures':sum(x['methods']['B4']['episode_failure'] for _,x in cp),'B2_only_failure_b':bb,'B4_only_failure_c':cc,'risk_difference_B4_minus_B2':sum(int(x['methods']['B4']['episode_failure'])-int(x['methods']['B2']['episode_failure']) for _,x in cp)/nn if nn else None,'exact_two_sided_mcnemar_p':exact_binom_two_sided(bb,cc),'discordance_wilson_95ci':wilson(bb+cc,nn)}
    result['label_totals']={m:Counter(c['label'] for e in result['episodes'].values() for l in e['methods'][m] if l in ('E0','E1','E2','E3') for c in e['methods'][m][l]['claims']) for m in ('B2','B4')}
    result['label_totals']={m:dict(v) for m,v in result['label_totals'].items()};Path(a.output).parent.mkdir(parents=True,exist_ok=True);Path(a.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['paired_episode_comparison'],indent=2));print(json.dumps(result['method_level'],indent=2))
if __name__=='__main__':main()
