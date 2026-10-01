"""SIMULATED-only power sensitivity for prospectively fixed tests; no study data."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from simulate_roboboat_fixed_n_power_v1 import SCORES, LAMBDAS, N_GRID, ALPHA, score_distribution, log_e_value, wilson, hypothetical_families

FIXED_BETS=(.05,.10,.15,.20,.25,.30,.40)


def results(counts, *, origin='SIMULATED'):
    if origin!='SIMULATED':raise ValueError('only hypothetical simulated counts accepted')
    counts=np.asarray(counts);repetitions=counts.shape[0];rows=[]
    for label,lambdas in [('existing_equal_mixture',LAMBDAS)]+[(f'fixed_lambda_{value:g}',np.array([value])) for value in FIXED_BETS]:
        # Each row is a separate candidate fixed before confirmation. This is
        # never a maximum over observed candidates or an empirical selection.
        successes=int(np.count_nonzero(log_e_value(counts,lambdas)>=np.log(1/ALPHA)))
        rows.append({'candidate':label,'prospectively_fixed_lambdas':lambdas.tolist(),'power_or_null_rejection_probability':successes/repetitions,'wilson_95_mc_interval':wilson(successes,repetitions),'rejections':successes})
    return rows


def build(seed=43103,repetitions=10000):
    if type(repetitions)is not int or repetitions<1:raise ValueError('positive integer repetitions required')
    rng=np.random.default_rng(seed);alternatives=[]
    for delta in (.05,.10,.15,.20):
        for discordance in (.2,.4,.6):
            for rho in (.25,1.):
                pmf=score_distribution(delta,discordance,rho);panels=[]
                for n in N_GRID:
                    counts=rng.multinomial(n,pmf,size=repetitions)
                    panels.append({'independent_geometry_n':n,'results':results(counts)})
                alternatives.append({'delta':delta,'discordance':discordance,'paired_difference_icc':rho,'origin':'SIMULATED','score_pmf':pmf.tolist(),'panels':panels})
    stresses=[]
    for scenario in hypothetical_families():
        if scenario['kind']!='NULL_STRESS':continue
        panels=[];pmfs=scenario['pmfs'];k=len(pmfs)
        for n in N_GRID:
            counts=np.zeros((repetitions,13),dtype=np.int64);allocations=[n//k+int(i<n%k) for i in range(k)]
            for pmf,size in zip(pmfs,allocations):counts+=rng.multinomial(size,pmf,size=repetitions)
            panels.append({'independent_geometry_n':n,'fixed_family_allocations':allocations,'null_aggregate_mean':sum(size*float(pmf@SCORES) for size,pmf in zip(allocations,pmfs))/n,'results':results(counts)})
        stresses.append({'name':scenario['name'],'panels':panels})
    sources=[Path(__file__).resolve(),Path(log_e_value.__code__.co_filename).resolve()]
    return {'schema':'roboboat-fixed-bet-power-comparison/v1','status':'HYPOTHETICAL_DEVELOPMENT_PLANNING_ONLY','seed':seed,'repetitions_per_panel':repetitions,'numpy_version':np.__version__,'bit_generator':type(rng.bit_generator).__name__,'alpha_per_separate_candidate':ALPHA,'n_grid':list(N_GRID),'source_bindings':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],'alternatives':alternatives,'null_stresses':stresses,'validity':'For any single lambda fixed from development before confirmation, independent bounded geometry scores and weak nonpositive mean expectation imply E[product(1+lambda*X_i)]<=1 by AM-GM. Markov bounds type-I at alpha. Fixed weighted mixtures also qualify. Different rows are alternative designs, not jointly tested hypotheses.','selection':'No test, lambda, N, endpoint or hypothesis is selected by this report. Pilot measurement/variance, scientific effect and operational feasibility are still required. The largest observed confirmation statistic must never choose the test.','common_random_numbers':'Each scenario/N uses identical simulated counts across candidates for an efficient power comparison; MC intervals are marginal, not joint guarantees.','limitations':['No study answers, recordings, labels or pilot effects read. All alternative distributions are hypothetical.','Efficiency is effect/variance dependent; a fixed bet can lose power at smaller effects or higher variance. Larger N does not rescue negative expected log growth for a poorly chosen fixed bet.','Fixed-N only; no optional stopping under a weak heterogeneous average null.','N is geometry draws, not questions, variants or calls. Missing annotation sensitivity and invalid-geometry inflation remain necessary; the existing separate simulation documents them.','Any chosen final analysis requires independent review before freeze.'],'confirmation_frozen':False,'confirmation_n':0,'replication_n':0,'land_n_added':0,'inference_activated':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--seed',type=int,default=43103);parser.add_argument('--repetitions',type=int,default=10000);a=parser.parse_args();report=build(a.seed,a.repetitions)
    with Path(a.output).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'alternative_panels':len(report['alternatives'])*len(N_GRID),'null_panels':len(report['null_stresses'])*len(N_GRID)}))
