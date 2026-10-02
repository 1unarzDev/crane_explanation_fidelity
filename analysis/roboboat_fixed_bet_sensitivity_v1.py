#!/usr/bin/env python3
"""Prospective finite-sample fixed-bet sensitivity on hypothetical populations.

No observations, test selection, confirmation freeze or provider calls occur.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from roboboat_cluster_score_design_v1 import GRID, scenarios
from simulate_roboboat_fixed_n_power_v1 import SCORES, ALPHA, LAMBDAS, validate_distribution, wilson

CANDIDATES = {
    'single_fixed_lambda_025': {'lambdas': [.25], 'weights': [1.]},
    'narrow_four_equal_weight': {'lambdas': [.1,.2,.3,.4], 'weights': [.25]*4},
    'retained_eleven_equal_weight': {'lambdas': LAMBDAS.tolist(), 'weights': [1/11]*11},
}


def checked_bets(lambdas, weights):
    lambdas, weights = np.asarray(lambdas,dtype=float), np.asarray(weights,dtype=float)
    if lambdas.ndim != 1 or not len(lambdas) or weights.shape != lambdas.shape or not np.all(np.isfinite(lambdas)) or not np.all(np.isfinite(weights)):
        raise ValueError('finite nonempty lambda and weight vectors of equal shape required')
    if np.any(lambdas<=0) or np.any(lambdas>=1) or np.any(weights<=0) or not np.isclose(weights.sum(),1,atol=1e-12):
        raise ValueError('lambdas in (0,1), positive weights summing to one required')
    return lambdas, weights/weights.sum()


def log_weighted_sum(logs, weights):
    maximum=np.max(logs,axis=-1,keepdims=True)
    return maximum[...,0]+np.log((np.exp(logs-maximum)*weights).sum(axis=-1))


def log_bet_e_value(counts, lambdas, weights, *, origin='SIMULATED'):
    if origin != 'SIMULATED':
        raise ValueError('SIMULATED only; no real-study inference authorized')
    counts=np.asarray(counts)
    if counts.ndim not in (1,2) or counts.shape[-1]!=13 or not np.all(np.isfinite(counts)) or np.any(counts<0) or np.any(counts!=np.floor(counts)):
        raise ValueError('nonnegative integer simulated 13-score counts required')
    lambdas,weights=checked_bets(lambdas,weights)
    return log_weighted_sum(counts@np.log1p(SCORES[:,None]*lambdas[None,:]),weights)


def log_expected_e_value(family_means, allocations, lambdas, weights):
    """Exact fixed-N expectation using independent possibly heterogeneous draws.

    AM-GM establishes expectation <=1 if the allocation-weighted average mean
    is nonpositive. This is not an anytime-valid weak-null e-process argument.
    """
    means=np.asarray(family_means,dtype=float)
    allocations=np.asarray(allocations)
    if means.ndim!=1 or not len(means) or allocations.shape!=means.shape or not np.all(np.isfinite(means)) or np.any(np.abs(means)>1):
        raise ValueError('finite bounded family means and matching allocations required')
    if not np.all(np.isfinite(allocations)) or np.any(allocations<0) or np.any(allocations!=np.floor(allocations)) or allocations.sum()<1:
        raise ValueError('nonnegative integer allocations with positive total required')
    lambdas,weights=checked_bets(lambdas,weights)
    logs=allocations@np.log1p(means[:,None]*lambdas[None,:])
    return float(log_weighted_sum(logs,weights))


def simulate(families, total_n, repetitions=10000, seed=42003, *, rng=None, origin='SIMULATED'):
    if origin!='SIMULATED':
        raise ValueError('SIMULATED only; no real-study inference authorized')
    if len(families)!=6 or type(total_n) is not int or total_n<12 or total_n%6:
        raise ValueError('six balanced families and integer N divisible by six, N>=12 required')
    if type(repetitions) is not int or repetitions<1:
        raise ValueError('positive integer repetitions required')
    families=[validate_distribution(p) for p in families]
    rng=np.random.default_rng(seed) if rng is None else rng
    counts=sum(rng.multinomial(total_n//6,p,size=repetitions) for p in families)
    means=[float(p@SCORES) for p in families]
    results={}
    for name,b in CANDIDATES.items():
        rejected=int(np.count_nonzero(log_bet_e_value(counts,**b)>=np.log(1/ALPHA)))
        lambdas=np.asarray(b['lambdas'])
        growth=np.mean([p@np.log1p(SCORES[:,None]*lambdas[None,:]) for p in families],axis=0)
        results[name]={'rejections':rejected,'estimated_rejection_probability':rejected/repetitions,
                      'monte_carlo_wilson_95_interval':wilson(rejected,repetitions),
                      'exact_log_expected_e_value':log_expected_e_value(means,[total_n//6]*6,**b),
                      'expected_log_growth_per_configuration_by_lambda':growth.tolist()}
    return {'valid_independent_geometry_n':total_n,'configurations_per_family':total_n//6,
            'family_means':means,'equal_family_population_mean':sum(means)/6,
            'candidates':results}


def build_report(seed=42003,repetitions=10000):
    rng=np.random.default_rng(seed)
    rows=[]
    for scenario in scenarios():
        rows.append({k:v for k,v in scenario.items() if k!='families'} | {
            'origin':'SIMULATED','family_score_pmfs':[p.tolist() for p in scenario['families']],
            'results':[simulate(scenario['families'],n,repetitions,rng=rng) for n in GRID]})
    sources=[Path(__file__),Path(__file__).with_name('roboboat_cluster_score_design_v1.py'),
             Path(__file__).with_name('simulate_roboboat_fixed_n_power_v1.py')]
    root=Path(__file__).resolve().parents[1]
    return {'schema':'roboboat-fixed-bet-sensitivity/v1-development',
            'status':'HYPOTHETICAL_FINITE_SAMPLE_FIXED_N_DESIGN_SENSITIVITY',
            'source_bindings':[{'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],
            'seed':seed,'numpy_version':np.__version__,'bit_generator':type(rng.bit_generator).__name__,
            'repetitions_per_scenario_n':repetitions,'alpha':ALPHA,'n_grid':list(GRID),
            'all_registered_candidates':CANDIDATES,'family_weights':[1/6]*6,'scenarios':rows,
            'single_lambda_design_basis':'Provisional meaningful effect delta=.10 and hypothetical worst-dependence score second moment .4 suggest approximate growth-optimal lambda=delta/E[X^2]=.25 via quadratic log expansion. This is a design assumption, not an observed effect estimate or an exact optimum.',
            'narrow_mixture_design_basis':'Equal fixed weights on .1,.2,.3,.4 reduce the eleven-component weight penalty while allowing a range of plausible growth rates; no simulated or observed winner is silently substituted.',
            'validity':'Independent bounded scores: E[product(1+lambda*X_i)]=product(1+lambda*E[X_i])<= (1+lambda*mean(E[X_i]))^N<=1 under the fixed-N average null. Fixed positive-weight averaging and Markov give type-I<=alpha.',
            'sequential_validity_claimed':False,
            'prospective_selection_rules':[
                'Before confirmation, justify the minimum meaningful effect independently of comparative p-values or the largest pilot effect.',
                'Collect an independent development population sufficient to estimate complete geometry-score moments, family heterogeneity, missing-judgment burden and invalidity, with uncertainty.',
                'Use conservative moment intervals and hypothesis-driven sensitivity scenarios including smaller-than-meaningful effects and all null stresses; assess robustness, not only the largest favorable power estimate.',
                'A single lambda may be prospectively selected from independently estimated development moments or their uncertainty envelope, using the scientifically justified effect and declared growth/power objective. Record the inputs, uncertainty and algorithm before confirmation.',
                'If moment uncertainty or smaller-effect robustness matters, freeze a specified mixture grid and weights before confirmation; no response-dependent maximization of bets is allowed.',
                'Validate the selected candidate and fixed N with fresh reproducible simulation over its declared population uncertainty envelope, then freeze the complete protocol. A poorly powered candidate is not rescued by unadjusted repeated tests.',
                'No candidate or N is selected in this report; simulation compares all registered alternatives and retains every stress case.'
            ],
            'limitations':[
                'All effects and populations are hypothetical; no real outcome banks or judges are inspected.',
                'Fixed lambda can have negative expected log growth despite a positive mean, making power shrink with N. Superiority-test validity does not imply consistency over every positive-mean alternative.',
                'Finite positive lambda mixtures can also miss sufficiently small effects if every component has nonpositive log growth. A prospectively specified meaningful effect motivates a power target, not redefining the superiority null.',
                'Equal family allocation is required here so the mean-null estimand matches pooled geometry factors. Unequal allocations require explicit estimand-compatible design rather than silent pooling.',
                'Null simulations are implementation checks; analytic fixed-N bounds establish validity. No weak-average-null optional stopping is authorized.',
                'Wilson intervals quantify per-row Monte Carlo uncertainty; they do not establish joint guarantees over all scenario choices.',
                'Whole-geometry adverse missing annotations remain in N and can erase a real effect. Technical-invalid inflation and fresh replication need separate configurations.'
            ],
            'confirmation_test_selected':None,'confirmation_n_selected':None,
            'confirmation_n':0,'replication_n':0,'alpha_consumed':0,'inferential_activation_authorized':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=42003)
    parser.add_argument('--repetitions',type=int,default=10000)
    args=parser.parse_args()
    report=build_report(args.seed,args.repetitions)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('Wrote hypothetical fixed-bet sensitivity:',args.output)


if __name__=='__main__':
    main()
