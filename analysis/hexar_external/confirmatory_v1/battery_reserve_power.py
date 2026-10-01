"""Development-only battery correlation and exact technical reserve sensitivity.

No semantic study artifacts are read. Each Monte Carlo row simulates independent
episodes, with nine dependent answers per method. Its paired episode probabilities
are hypothetical planning inputs, never an estimate from the old answer score.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

import numpy as np

from .heterogeneous_statistics import power
from .statistics import tail

ROOT = Path(__file__).resolve().parents[3]


def completion_probability(valid_per_family, reserve_per_family, invalid_rate, families=6):
    if type(valid_per_family) is not int or valid_per_family < 1:
        raise ValueError('positive valid family count required')
    if type(reserve_per_family) is not int or reserve_per_family < 0:
        raise ValueError('nonnegative integer reserve required')
    if type(families) is not int or families < 1 or not 0 <= invalid_rate <= 1:
        raise ValueError('invalid family count/rate')
    return tail(valid_per_family + reserve_per_family, valid_per_family, 1-invalid_rate)**families


def minimum_reserve(valid_per_family, invalid_rate, target=.99, maximum=200):
    if not 0 < target < 1:
        raise ValueError('completion target out of range')
    return next((r for r in range(maximum+1)
                 if completion_probability(valid_per_family,r,invalid_rate) >= target), None)


def battery_pairs(rng, episodes, contract_error, prompt_error, within_method, between_methods, jobs=9):
    """Gaussian copula; coefficients give the stated latent correlations.

    Shared episode G, method episode H_m, shared question J_j, and independent
    residual L_mj have independent standard normal distributions. Within-method
    correlation is rho_w; same-question cross-method correlation is rho_b;
    different-question cross-method correlation is rho_w*rho_b. Marginal error
    probabilities are fixed by the Gaussian quantile, with no nested-error rule.
    """
    if episodes < 1 or jobs < 1 or any(not 0 < p < 1 for p in (contract_error,prompt_error)):
        raise ValueError('positive simulation size and nondegenerate error rates required')
    if any(not 0 <= rho <= 1 for rho in (within_method,between_methods)):
        raise ValueError('correlation out of range')
    if type(jobs) is not int or jobs<1:raise ValueError('positive integer unique request count required')
    shared_episode=rng.standard_normal((episodes,1,1))
    method_episode=rng.standard_normal((episodes,2,1))
    shared_question=rng.standard_normal((episodes,1,jobs))
    residual=rng.standard_normal((episodes,2,jobs))
    latent=(math.sqrt(within_method*between_methods)*shared_episode
            +math.sqrt(within_method*(1-between_methods))*method_episode
            +math.sqrt((1-within_method)*between_methods)*shared_question
            +math.sqrt((1-within_method)*(1-between_methods))*residual)
    threshold=np.array([NormalDist().inv_cdf(contract_error),NormalDist().inv_cdf(prompt_error)])
    failure=(latent < threshold[None,:,None]).any(axis=2)
    cf,pf=failure[:,0],failure[:,1]
    cells=[int(((~cf)&pf).sum()),int((cf&(~pf)).sum()),int(((~cf)&(~pf)).sum()),int((cf&pf).sum())]
    return cells


def report(draws=80000, seed=2026100102, jobs=9):
    rng=np.random.default_rng(seed)
    rows=[]
    for contract_error in (.04,.06,.08,.10,.12):
        for within in (0.,.5,.9,1.):
            for between in (0.,.5,.9,1.):
                f,u,ss,ff=battery_pairs(rng,draws,contract_error,.10,within,between,jobs=jobs)
                d=(f+u)/draws
                q=f/(f+u) if f+u else None
                rows.append(dict(contract_answer_failure_probability=contract_error,
                                 prompt_answer_failure_probability=.10,
                                 within_method_latent_correlation=within,
                                 cross_method_same_question_latent_correlation=between,
                                 cells=dict(favorable=f,unfavorable=u,both_success=ss,both_failure=ff),
                                 contract_recording_failure=(u+ff)/draws,
                                 prompt_recording_failure=(f+ff)/draws,
                                 discordance=d,favorable_given_discordance=q,
                                 recording_risk_difference=(f-u)/draws,
                                 e_test_planning_power={str(n):power(n,d,q,fraction=.4) if q is not None else 0.
                                                        for n in (72,96,144,192)}))
    reserves=[]
    for valid in (12,16,24,32):
        for invalid in (0.,.05,.10,.20,.30):
            reserves.append(dict(valid_per_family=valid,invalid_rate=invalid,
                                 completion_with_four_reserves=completion_probability(valid,4,invalid),
                                 reserves_per_family_for_95=minimum_reserve(valid,invalid,.95),
                                 reserves_per_family_for_99=minimum_reserve(valid,invalid,.99)))
    return dict(schema='hexar-battery-reserve-power/v1',phase='development_design_only',seed=seed,
                draws_per_battery_regime=draws,maximum_mc_se=.5/math.sqrt(draws),alpha=.01,
                jobs_per_recording=jobs,independent_unit='simulated robot episode',
                model='Gaussian copula with independent episodes and correlated answer failures in both methods',
                not_empirical_estimates=True,selected_n=None,selected_reserve=None,
                power_note='Exact homogeneous paired e-test power at estimated hypothetical copula probabilities; Monte Carlo uncertainty in those probabilities remains. Heterogeneous power is in family_power_report.json.',
                reserve_note='Exact binomial completion for six independent families with a fixed invalid rate; observed rates, uncertainty, heterogeneity and outcome-blind technical predicates must be qualified before a decision.',
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                battery_rows=rows,reserve_rows=reserves)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'manifests/hexar_external/confirmatory_v1/battery_reserve_power_report.json')
    parser.add_argument('--unique-jobs',type=int,default=9)
    args=parser.parse_args()
    value=report(jobs=args.unique_jobs)
    with args.output.open('x') as stream:
        stream.write(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(status='DESIGN_ONLY',regimes=len(value['battery_rows']),selected_n=None)))


if __name__=='__main__':main()
