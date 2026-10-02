#!/usr/bin/env python3
"""Read-only frozen-code review; entirely invented data, no provider calls."""
import contextlib, hashlib, io, json, math, sys, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
REPO=HERE.parents[3]
sys.path.insert(0,str(REPO/'analysis'))
import analyze_handoff_frozen_confirmation as frozen
from summarize_handoff_response_development import paired_interval
DECL=REPO/'manifests/study/evidence-calibration-handoff-confirmation-freeze-v1.json'

def fixture(n,b,c,both=0,look='FINAL',missing=0,invalid=0,missing_score=False,coverage_loss=False):
    with tempfile.TemporaryDirectory(prefix='synthetic-',dir=HERE) as tmp:
        root=Path(tmp); design=json.loads(DECL.read_text()); design['study_id']='SYNTHETIC_ONLY'
        fp=root/'freeze.json';fp.write_text(json.dumps(design))
        base=root/'analysis/results/confirmation/SYNTHETIC_ONLY';out=base/f'look-{n}';out.mkdir(parents=True)
        records=[{'complete_pair':True} for _ in range(n)]+[{'complete_pair':False,'b2_calls':4} for _ in range(missing)]+[{'complete_pair':False,'disposition':'PHYSICAL_TECHNICAL_INVALID'} for _ in range(invalid)]
        (base/f'execution-accounting-{look}.json').write_text(json.dumps({'complete':True,'complete_paired_episode_n':n,'records':records}))
        cases=[];joins=[];passes={'A':[],'B':[]}
        for i in range(n):
            for method in ['B2','B4v7']:
                failure=(i<b if method=='B2' else b<=i<b+c) or b+c<=i<b+c+both
                for level in range(4):
                    identity=f'synthetic-{i}-{method}-{level}';cases.append({'case_id':identity})
                    joins.append({'response_id':identity,'configuration_id':f'synthetic-{i}','method_id':method,'realized_family':'synthetic','condition_id':f'synthetic-{i}-E{level}'})
                    for slot in passes:
                        # Split failure across passes verifies primary union. Split unit
                        # communication verifies intersection, without extra independent N.
                        fail=failure and level==0 and slot=='B'
                        communicated=not(coverage_loss and method=='B4v7' and slot=='B')
                        passes[slot].append({'case_id':identity,'primary_failure':fail,'required_units':[{'unit_id':'u0','communicated':communicated}], 'primary_violations':[{'kind':'unsupported_mechanism','quote':'invented'}] if fail else [],'factual_numeric_errors':[]})
        (out/'blind-cases-v1.json').write_text(json.dumps({'cases':cases}));(out/'join-key-v1.json').write_text(json.dumps({'entries':joins}))
        anns=root/'annotations';anns.mkdir()
        for slot,rows in passes.items():
            if missing_score and slot=='B':rows.pop()
            (anns/f'{slot}-batch-000.json').write_text(json.dumps({'status':'STRUCTURALLY_VALID_SUPPORT_RETURN','parsed_final':{'annotations':rows}}))
        original_root=frozen.ROOT;original_argv=sys.argv[:]
        frozen.ROOT=root;sys.argv=['synthetic-review','--freeze',str(fp),'--annotations',str(anns),'--look',look]
        try:
            with contextlib.redirect_stdout(io.StringIO()):frozen.main()
            result=json.loads((out/'primary-analysis-v1.json').read_text())
        finally:frozen.ROOT=original_root;sys.argv=original_argv
        return result

def main():
    checks=[]
    def ok(name,test):
        assert test,name;checks.append(name)
    r=fixture(600,0,0,both=9,look='FIRST',missing=3,invalid=2)
    ok('N600 ties terminate at p1',r['terminal_analysis'] and r['stopped_for_zero_discordance_futility'] and r['exact_one_sided_confirmatory_p']==1)
    ok('concordant failures retained',r['primary']['methods']['B2']['failures']==9 and r['primary']['methods']['B4v7']['failures']==9)
    ok('missingness worst-case bounds',r['missingness']['method_incomplete_pairs']==3 and r['missingness']['full_eligible_population_worst_case_risk_difference_bounds']==[-3/603,3/603])
    z=1-.00625**(1/600)
    ok('zero-discordance interval agrees closed form',max(abs(x-y) for x,y in zip(r['primary']['conservative_whole_episode_95_ci'],[-z,z]))<1e-11)
    r=fixture(600,20,2,look='FIRST')
    ok('N600 discordance is continuation only',r['continuation_required'] and not r['terminal_analysis'] and 'primary' not in r and 'exact_one_sided_confirmatory_p' not in r)
    r=fixture(1200,30,5,both=10,missing=2)
    p=sum(math.comb(35,k) for k in range(30,36))/2**35
    ok('N1200 one-sided exact McNemar',r['exact_one_sided_confirmatory_p']==p)
    ok('two-sided descriptive p retained',r['primary']['descriptive_exact_two_sided_p']==min(1,2*p))
    ok('union across passes and four levels; N unchanged',r['primary']['independent_episode_n']==1200 and r['primary']['B2_fails_B4_passes']==30 and r['primary']['B4_fails_B2_passes']==5 and r['pass_sensitivity']['A']['B2_fails_B4_passes']==0)
    ok('positive RD and coverage required for success',r['primary']['paired_risk_difference_B2_minus_B4']==25/1200 and r['primary_scientific_success'])
    reverse=fixture(1200,5,30)
    ok('opposing discordance never superiority',not reverse['significant_superiority'] and reverse['primary']['paired_risk_difference_B2_minus_B4']==-25/1200)
    loss=fixture(1200,30,5,coverage_loss=True)
    ok('intersection coverage gates otherwise significant result',loss['significant_superiority'] and not loss['primary_scientific_success'] and loss['primary']['methods']['B4v7']['mean_episode_coverage']==0)
    try:fixture(600,0,0,look='FIRST',missing_score=True)
    except RuntimeError as e:ok('incomplete annotation rejected before join',str(e)=='Incomplete or extra blind scores')
    else:raise AssertionError('missing score accepted')
    for n in [600,1200]:
        for b,c in [(0,0),(n,0),(0,n),(n//2,n//2)]:
            lo,hi=paired_interval(b,c,n,tail_probability=.00625)
            ok(f'interval contains point and stays bounded n={n} b={b} c={c}',-1<=lo<=(b-c)/n<=hi<=1)
    report={'scope':'SYNTHETIC_ONLY_READ_ONLY_REVIEW','freeze_sha256':hashlib.sha256(DECL.read_bytes()).hexdigest(),'checks_passed':len(checks),'checks':checks,'provider_calls':0,'actual_confirmation_data_accessed':False}
    (HERE/'synthetic-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
