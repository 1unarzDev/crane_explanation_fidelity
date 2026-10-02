#!/usr/bin/env python3
"""Reproducible exploratory paired analysis of retained B2/B4 confirmation text.

This intentionally analyzes descriptive realization metrics only. Endpoint labels are
not present in the retained B4 records (UNSCORED_REQUIRES_METHOD_INDEPENDENT_SCORING).
Episodes, rather than conditions/evidence levels, are the resampling unit.
"""
import argparse, hashlib, json, math, re, random
from collections import defaultdict
from pathlib import Path

CAUSE = re.compile(r"\b(?:failure|fault|broken|blocked|obstruct|collision|slip|actuator|motor|wheel|encoder|odometry|localization|controller|recovery|discrepancy|cause|because|stuck|timeout)\b", re.I)
WORD = re.compile(r"\b[\w’'-]+\b", re.UNICODE)
NUM = re.compile(r"(?<!\w)(?:\d+(?:\.\d+)?%?)(?!\w)")

def sha(p):
    h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()

def load_dir(d, method):
    out={}
    for p in sorted(d.glob('*.json')):
        d0=json.loads(p.read_text())
        cid=d0.get('condition_id','')
        if not cid or d0.get('method') != method: continue
        m=re.match(r'^(.*)-(E[0-3])$',cid)
        if not m: continue
        eid,lev=m.groups(); answer=d0.get('answer','')
        out[(eid,lev)]={'answer':answer,'family':d0.get('family'),'file':str(p),'sha256':sha(p), 'endpoint_status':d0.get('endpoint_status')}
    return out

def metrics(s):
    return {'characters':len(s), 'words':len(WORD.findall(s)), 'sentences':len(re.findall(r'[.!?](?:\s|$)',s)), 'numeric_tokens':len(NUM.findall(s)), 'cause_terms':len(CAUSE.findall(s))}

def sign_p(diffs):
    nz=[x for x in diffs if x]
    n=len(nz); k=sum(x>0 for x in nz)
    if not n: return 1.0
    c=sum(math.comb(n,i) for i in range(min(k,n-k)+1))
    return min(1.0, 2*c/(2**n))

def bootstrap(diffs, seed=20261002, reps=10000):
    rng=random.Random(seed); n=len(diffs); vals=[]
    for _ in range(reps): vals.append(sum(diffs[rng.randrange(n)] for _ in range(n))/n)
    vals.sort(); return vals[int(.025*reps)], vals[int(.975*reps)]

def holm(items):
    # items list (name,p); return adjusted p preserving names
    order=sorted(range(len(items)), key=lambda i:items[i][1]); out=[None]*len(items); m=len(items)
    running=0
    for rank,i in enumerate(order):
        running=max(running,(m-rank)*items[i][1]); out[i]=min(1.0,running)
    return {items[i][0]:out[i] for i in range(len(items))}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--worktree-root',required=True); ap.add_argument('--output',required=True); args=ap.parse_args()
    root=Path(args.worktree_root); base=root/'model_outputs/evidence-calibration-b4-b2-confirmation-2026-10-01'; b2=load_dir(base/'b2','B2'); b4=load_dir(base/'b4','B4')
    common=sorted({e for e,l in b2}&{e for e,l in b4}); complete=sorted({e for e in common if all((e,l) in b2 and (e,l) in b4 for l in ('E0','E1','E2','E3'))})
    accounting_path=root/'analysis/results/confirmation/evidence-calibration-b4-b2-confirmation-2026-10-01/execution-accounting-FIRST.json'
    acc=json.loads(accounting_path.read_text()); complete_exec=sorted(r['run_id'] for r in acc.get('records',[]) if r.get('complete_pair') is True)
    complete_exec=[e for e in complete_exec if e in complete]
    result={'generated_utc':'2026-10-02','data_root':str(base),'file_counts':{'b2':len(b2),'b4':len(b4)},'episode_counts':{'common_any_level':len(common),'common_all_four_levels':len(complete),'accounting_complete_intersection':len(complete_exec)},'accounting_complete_pair_n':acc.get('complete_paired_episode_n'),'b4_endpoint_status_counts':{},'technical_note':'B4 records are unscored and contain no method-independent endpoint labels; p-values below test paired realization metrics only.'}
    for x in b4.values(): result['b4_endpoint_status_counts'][x.get('endpoint_status')]=result['b4_endpoint_status_counts'].get(x.get('endpoint_status'),0)+1
    def paired(episodes, level=None):
        rows=[]
        for e in episodes:
            levels=[level] if level else ['E0','E1','E2','E3']
            a=[metrics(b2[(e,l)]['answer']) for l in levels]; c=[metrics(b4[(e,l)]['answer']) for l in levels]
            rows.append({k:sum(z[k] for z in a)/len(a) for k in a[0]} | {'b4':{k:sum(z[k] for z in c)/len(c) for k in c[0]}})
        stats={}; raw=[]
        for k in ('characters','words','sentences','numeric_tokens','cause_terms'):
            diffs=[r['b4'][k]-r[k] for r in rows]; lo,hi=bootstrap(diffs); p=sign_p(diffs); raw.append((k,p)); stats[k]={'n':len(diffs),'mean_b4_minus_b2':sum(diffs)/len(diffs),'bootstrap_95ci':[lo,hi],'sign_test_p':p,'positive_n':sum(x>0 for x in diffs),'zero_n':sum(x==0 for x in diffs),'negative_n':sum(x<0 for x in diffs)}
        adj=holm(raw)
        for k in stats: stats[k]['holm_corrected_p_across_metrics']=adj[k]
        return stats
    result['episode_average_all_four_levels']=paired(complete)
    result['episode_average_accounting_complete']=paired(complete_exec)
    result['per_level']={l:paired(sorted({e for e in common if (e,l) in b2 and (e,l) in b4}),l) for l in ('E0','E1','E2','E3')}
    result['family_all_four_levels']={f:paired([e for e in complete if b2[(e,'E0')]['family']==f]) for f in sorted({b2[(e,'E0')]['family'] for e in complete})}
    Path(args.output).parent.mkdir(parents=True,exist_ok=True); Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['episode_counts'],indent=2))
    for k,v in result['episode_average_all_four_levels'].items(): print(k, v['mean_b4_minus_b2'],v['bootstrap_95ci'],v['sign_test_p'],v['holm_corrected_p_across_metrics'])
if __name__=='__main__': main()
