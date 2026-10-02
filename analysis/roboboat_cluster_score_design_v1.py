#!/usr/bin/env python3
"""Hypothetical balanced-stratum fixed-N test comparison; no study data read.

Conventional tests are asymptotic candidates, not finite-sample guarantees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
from simulate_roboboat_fixed_n_power_v1 import (
    SCORES, ALPHA, log_e_value, score_distribution, validate_distribution, wilson,
)

GRID = (60, 120, 150, 240, 420, 600, 840, 1200, 1800, 2400, 4020)


def welch_critical_cf3(df, alpha=ALPHA):
    """Third-order Cornish-Fisher approximation to upper Student-t quantile.

    This avoids a SciPy dependency. It is an approximation, not an exact t CDF.
    Even an exact t quantile would not make a bounded-score Welch test exact.
    """
    df = np.asarray(df, dtype=float)
    if np.any(~np.isfinite(df)) or np.any(df < 1) or not np.isfinite(alpha) or not 0 < alpha < .5:
        raise ValueError('finite df>=1 and alpha in (0,.5) required')
    z = NormalDist().inv_cdf(1-alpha)
    return z+(z**3+z)/(4*df)+(5*z**5+16*z**3+3*z)/(96*df**2)+(3*z**7+19*z**5+17*z**3-15*z)/(384*df**3)


def evaluate_simulated_counts(counts, *, origin='SIMULATED', alpha=ALPHA):
    if origin != 'SIMULATED':
        raise ValueError('SIMULATED counts only; no study inference authorized')
    counts = np.asarray(counts)
    if counts.ndim != 3 or counts.shape[1:] != (6,13) or not np.all(np.isfinite(counts)) or np.any(counts < 0) or np.any(counts != np.floor(counts)):
        raise ValueError('repetitions x six strata x 13 nonnegative integer counts required')
    if not 0 < alpha < .5:
        raise ValueError('alpha in (0,.5) required')
    ns = counts.sum(axis=2)
    if np.any(ns != ns[0,0]) or ns[0,0] < 2:
        raise ValueError('balanced fixed six-stratum allocation with at least two configurations each required')
    n = int(ns[0,0])
    sums = counts@SCORES
    means = sums/n
    sumsquares = counts@(SCORES**2)
    variances = np.maximum(0., (sumsquares-sums*sums/n)/(n-1))
    components = variances/(36*n)
    se2 = components.sum(axis=1)
    mean = means.mean(axis=1)
    nonzero = se2 > 1e-15
    statistic = np.divide(mean,np.sqrt(se2),out=np.zeros_like(mean),where=nonzero)
    denominator = (components**2/(n-1)).sum(axis=1)
    df = np.divide(se2**2,denominator,out=np.full_like(mean,6*(n-1)),where=denominator>0)
    df = np.maximum(df,1)
    z = NormalDist().inv_cdf(1-alpha)
    pooled = counts.sum(axis=1)
    # Equivalent to equal-family estimand only because allocations are balanced.
    return {'stratified_wald': nonzero & (statistic>=z),
            'stratified_welch_t_cf3': nonzero & (statistic>=welch_critical_cf3(df,alpha)),
            'fixed_lambda_mixture': log_e_value(pooled)>=np.log(1/alpha),
            'hoeffding_bounded_mean': mean>=np.sqrt(2*np.log(1/alpha)/(6*n)),
            'zero_estimated_variance': ~nonzero,
            'estimated_equal_family_mean': mean, 'estimated_variance_of_mean': se2,
            'welch_effective_df': df}


def simulate(families, total_n, repetitions=10000, seed=42002, *, rng=None, origin='SIMULATED'):
    if origin != 'SIMULATED':
        raise ValueError('SIMULATED families only; no study inference authorized')
    if len(families) != 6 or type(total_n) is not int or total_n < 12 or total_n%6:
        raise ValueError('six families and N divisible by six, at least 12, required')
    if type(repetitions) is not int or repetitions < 1:
        raise ValueError('positive integer repetitions required')
    families = [validate_distribution(p) for p in families]
    rng = np.random.default_rng(seed) if rng is None else rng
    counts = np.stack([rng.multinomial(total_n//6,p,size=repetitions) for p in families],axis=1)
    stats = evaluate_simulated_counts(counts)
    means = [float(p@SCORES) for p in families]
    variances = [float(p@(SCORES-mu)**2) for p,mu in zip(families,means)]
    methods = {}
    for method in ('stratified_wald','stratified_welch_t_cf3','fixed_lambda_mixture','hoeffding_bounded_mean'):
        rejected = int(stats[method].sum())
        methods[method] = {'rejections': rejected,'estimated_rejection_probability': rejected/repetitions,
                           'monte_carlo_wilson_95_interval': wilson(rejected,repetitions)}
    return {'valid_independent_geometry_n': total_n,'configurations_per_family': total_n//6,
            'family_means': means,'family_variances': variances,
            'equal_family_population_mean': sum(means)/6,
            'true_variance_of_equal_family_mean': sum(variances)/(6*total_n),
            'zero_estimated_variance_fraction': float(stats['zero_estimated_variance'].mean()),
            'welch_df_quantiles': np.quantile(stats['welch_effective_df'],[0,.5,1]).tolist(),
            'methods': methods}


def point_mass(index):
    pmf = np.zeros(13)
    pmf[index] = 1
    return pmf


def scenarios():
    rows = []
    for delta in (.05,.1,.15,.2):
        for q in (.2,.4,.6):
            for rho in (.25,1.):
                rows.append({'name': f'effect-{delta}-discordance-{q}-icc-{rho}',
                             'kind': 'HYPOTHETICAL_ALTERNATIVE', 'delta':delta,'discordance':q,'icc':rho,
                             'families': [score_distribution(delta,q,rho)]*6})
    rows.extend([
        {'name':'symmetric_null','kind':'NULL_STRESS','families':[score_distribution(0,.4,.25)]*6},
        {'name':'symmetric_sparse_discordance_null','kind':'NULL_STRESS','families':[score_distribution(0,.01,1)]*6},
        {'name':'heterogeneous_variance_balanced_weak_null','kind':'NULL_STRESS',
         'families':[score_distribution(d,q,rho) for d,q,rho in
                     ((.15,.2,.25),(.1,.4,1),(.05,.6,.25),(-.05,.2,1),(-.1,.4,.25),(-.15,.6,1))]},
        {'name':'between_family_mean_heterogeneity_alternative','kind':'HYPOTHETICAL_ALTERNATIVE',
         'families':[score_distribution(d,.6,.25) for d in (-.15,-.05,.05,.15,.25,.35)]},
    ])
    right_tail = np.zeros(13)
    right_tail[5],right_tail[12] = 6/7,1/7
    left_tail = right_tail[::-1]
    for name,pmf in (('right_skew_null',right_tail),('left_skew_null',left_tail)):
        rows.append({'name':name,'kind':'NULL_STRESS','families':[pmf]*6})
    rows.extend([
        {'name':'variance_concentrated_in_one_family_left_skew_null','kind':'NULL_STRESS',
         'families':[point_mass(6)]*5+[left_tail]},
        {'name':'five_deterministic_positive_families_one_offsetting_family_null','kind':'NULL_STRESS',
         'families':[point_mass(7)]*5+[score_distribution(-5/6,1,1)]},
    ])
    for u in (.05,.1):
        rows.append({'name':f'ten_point_effect_unresolved_clusters-{u}',
                     'kind':'MISSING_ANNOTATION_SENSITIVITY',
                     'families':[(1-u)*score_distribution(.1,.4,.25)+u*point_mass(0)]*6})
    return rows


def build_report(seed=42002,repetitions=10000):
    rng = np.random.default_rng(seed)
    rows=[]
    for scenario in scenarios():
        rows.append({k:v for k,v in scenario.items() if k!='families'} | {
            'origin':'SIMULATED','family_score_pmfs':[p.tolist() for p in scenario['families']],
            'results':[simulate(scenario['families'],n,repetitions,rng=rng) for n in GRID]})
    return {'schema':'roboboat-cluster-score-design/v1-development',
            'status':'HYPOTHETICAL_FIXED_N_DESIGN_COMPARISON_NOT_STUDY_INFERENCE',
            'source_binding':{'path':'analysis/roboboat_cluster_score_design_v1.py',
                              'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'dependency_bindings':[{'path':str(Path(p).relative_to(Path(__file__).resolve().parents[1])),
                                     'sha256':hashlib.sha256(Path(p).read_bytes()).hexdigest()}
                                   for p in [Path(__file__).with_name('simulate_roboboat_fixed_n_power_v1.py')]],
            'seed':seed,'numpy_version':np.__version__,'repetitions_per_scenario_n':repetitions,
            'alpha':ALPHA,'n_grid':list(GRID),'family_weights':[1/6]*6,'scenarios':rows,
            'estimand':'Equal six-family average of independent geometry mean differences, each geometry the equally weighted mean of six paired binary answer-success differences.',
            'conventional_test_limits':'Stratified Wald and CF3 Welch-t candidates are asymptotic. Neither has general finite-sample size control for bounded skewed scores. Estimated variance zero means no conventional rejection.',
            'finite_sample_tests':'Fixed-lambda mixture and Hoeffding retain analytic fixed-N guarantees under independent bounded scores and nonpositive average expectation; no optional stopping.',
            'annotation_rule':'Unresolved whole-geometry annotation is assigned adverse score -1, retained in N; technical-invalid collection inflation is separate.',
            'null_stress_selection':'Null distributions are hypothesis-driven asymmetry/variance-concentration stress cases, independent of real outcome banks.',
            'confirmation_test_selected':None,'confirmation_n_selected':None,'alpha_consumed':0,
            'confirmation_n':0,'replication_n':0,'inferential_activation_authorized':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--seed',type=int,default=42002)
    parser.add_argument('--repetitions',type=int,default=10000)
    args=parser.parse_args()
    report=build_report(args.seed,args.repetitions)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print('Wrote hypothetical cluster-score design comparison:',args.output)


if __name__=='__main__':
    main()
