#!/usr/bin/env python3
"""Hypothetical fixed-N marine cluster-score power; never reads study responses."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SCORES = np.arange(-6, 7, dtype=float)/6
LAMBDAS = np.array([.01, .025, .05, .075, .10, .15, .20, .30, .40, .60, .80])
N_GRID = (50, 100, 150, 250, 410, 620, 800, 1000, 1500, 2000, 4000)
ALPHA = .025


def score_distribution(delta: float, discordance: float, rho: float) -> np.ndarray:
    """Exact distribution of six-question mean with difference ICC rho.

    With probability rho all six differences share one draw; otherwise they are
    independent draws from {-1,0,1}. This is a hypothetical dependence model.
    """
    if not all(np.isfinite(x) for x in (delta, discordance, rho)) or not (
        abs(delta) <= discordance <= 1 and 0 <= rho <= 1):
        raise ValueError('require |delta| <= discordance <= 1 and 0 <= rho <= 1')
    primitive = np.array([(discordance-delta)/2, 1-discordance, (discordance+delta)/2])
    independent = np.array([1.])
    for _ in range(6):
        independent = np.convolve(independent, primitive)
    shared = np.zeros(13)
    shared[[0, 6, 12]] = primitive
    return rho*shared + (1-rho)*independent


def validate_distribution(pmf):
    pmf = np.asarray(pmf, dtype=float)
    if pmf.shape != (13,) or not np.all(np.isfinite(pmf)) or np.any(pmf < 0) or not np.isclose(pmf.sum(), 1, atol=1e-12):
        raise ValueError('13 nonnegative finite probabilities summing to one required')
    return pmf / pmf.sum()


def log_e_value(counts, lambdas=LAMBDAS):
    counts = np.asarray(counts)
    lambdas = np.asarray(lambdas, dtype=float)
    if counts.ndim not in (1, 2) or counts.shape[-1] != 13 or not np.all(np.isfinite(counts)) or np.any(counts < 0) or np.any(counts != np.floor(counts)):
        raise ValueError('nonnegative integer simulated score counts required')
    if lambdas.ndim != 1 or not len(lambdas) or not np.all(np.isfinite(lambdas)) or np.any(lambdas <= 0) or np.any(lambdas >= 1):
        raise ValueError('prospectively fixed lambdas must be in (0,1)')
    logs = counts @ np.log1p(SCORES[:, None]*lambdas[None, :])
    maximum = np.max(logs, axis=-1, keepdims=True)
    result = maximum[..., 0] + np.log(np.exp(logs-maximum).mean(axis=-1))
    return result


def wilson(successes: int, repetitions: int) -> list[float]:
    if type(repetitions) is not int or repetitions < 1 or type(successes) is not int or not 0 <= successes <= repetitions:
        raise ValueError('valid integer Monte Carlo counts required')
    z = 1.959963984540054
    p = successes/repetitions
    denominator = 1+z*z/repetitions
    center = (p+z*z/(2*repetitions))/denominator
    half = z*np.sqrt(p*(1-p)/repetitions+z*z/(4*repetitions**2))/denominator
    return [0. if successes == 0 else max(0., float(center-half)),
            1. if successes == repetitions else min(1., float(center+half))]


def simulate_families(families, allocations, repetitions, rng, *, origin='SIMULATED', alpha=ALPHA):
    """Independent family-specific multinomial counts; valid fixed-N design only."""
    if origin != 'SIMULATED':
        raise ValueError('only SIMULATED inputs accepted; no real-study inference')
    if type(repetitions) is not int or repetitions < 1 or not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError('positive repetitions and alpha in (0,1) required')
    if len(families) != len(allocations) or not len(families):
        raise ValueError('one allocation per hypothetical family required')
    pmfs = [validate_distribution(p) for p in families]
    counts = np.zeros((repetitions, 13), dtype=np.int64)
    for pmf, n in zip(pmfs, allocations):
        if type(n) is not int or n < 0:
            raise ValueError('integer nonnegative family allocations required')
        counts += rng.multinomial(n, pmf, size=repetitions)
    n = sum(allocations)
    if not n:
        raise ValueError('positive independent configuration count required')
    reject = int(np.count_nonzero(log_e_value(counts) >= np.log(1/alpha)))
    means = [float(p@SCORES) for p in pmfs]
    # Exact expectation, using independence; zero factors do not occur because lambda<1.
    expectation_logs = sum(n*np.log1p(LAMBDAS*mu) for n, mu in zip(allocations, means))
    maximum = float(np.max(expectation_logs))
    log_expected_e = maximum + float(np.log(np.exp(expectation_logs-maximum).mean()))
    expected_e = float(np.exp(log_expected_e)) if log_expected_e <= np.log(np.finfo(float).max) else None
    return {'valid_independent_configuration_n': n, 'rejections': reject, 'repetitions': repetitions,
            'estimated_rejection_probability': reject/repetitions,
            'monte_carlo_wilson_95_interval': wilson(reject, repetitions),
            'population_mean_score': sum(n*mu for n, mu in zip(allocations, means))/n,
            'exact_log_expected_e_value': log_expected_e,
            'exact_expected_e_value': expected_e}


def hypothetical_families():
    skew = np.zeros(13)
    skew[5], skew[12] = 6/7, 1/7  # X=-1/6 or +1, zero mean.
    return [
        {'name': 'symmetric_null_iid', 'pmfs': [score_distribution(0, .4, .25)], 'kind': 'NULL_STRESS'},
        {'name': 'symmetric_null_perfect_dependence', 'pmfs': [score_distribution(0, .6, 1)], 'kind': 'NULL_STRESS'},
        {'name': 'asymmetric_zero_mean_null', 'pmfs': [skew], 'kind': 'NULL_STRESS'},
        {'name': 'heterogeneous_balanced_family_weak_null',
         'pmfs': [score_distribution(-.10, .2, .25), score_distribution(-.10, .6, 1),
                  score_distribution(.05, .4, .25), score_distribution(.15, .2, 1)],
         'kind': 'NULL_STRESS', 'allocation': 'equal blocks; remainder assigned in declared order so total mean<=0'},
        # Unknown configuration annotation is mapped to the full adverse bound -1.
        # This model is purposely harsh and unrelated to technical invalidity.
        {'name': 'ten_point_effect_five_percent_unresolved_clusters',
         'pmfs': [.95*score_distribution(.1, .4, .25)+.05*np.eye(13)[0]], 'kind': 'MISSING_ANNOTATION_SENSITIVITY'},
        {'name': 'ten_point_effect_ten_percent_unresolved_clusters',
         'pmfs': [.90*score_distribution(.1, .4, .25)+.10*np.eye(13)[0]], 'kind': 'MISSING_ANNOTATION_SENSITIVITY'},
    ]


def build_report(seed=42001, repetitions=10000):
    rng = np.random.default_rng(seed)
    rows = []
    for delta in (.05, .10, .15):
        for q in (.2, .4, .6):
            for rho in (.25, 1.):
                pmf = score_distribution(delta, q, rho)
                rows.append({'origin': 'SIMULATED', 'delta': delta, 'discordance': q,
                             'paired_difference_icc': rho, 'score_pmf': pmf.tolist(),
                             'results': [simulate_families([pmf], [n], repetitions, rng) for n in N_GRID]})
    stresses = []
    for scenario in hypothetical_families():
        k = len(scenario['pmfs'])
        stresses.append({key: value for key, value in scenario.items() if key != 'pmfs'} | {
            'origin': 'SIMULATED', 'score_pmfs': [p.tolist() for p in scenario['pmfs']],
            'results': [simulate_families(scenario['pmfs'], [n//k+int(i < n%k) for i in range(k)], repetitions, rng)
                        for n in N_GRID]})
    return {'schema': 'roboboat-fixed-n-power-simulation/v1-development',
            'status': 'HYPOTHETICAL_POWER_SIMULATION_NO_STUDY_OBSERVATIONS',
            'seed': seed, 'repetitions_per_scenario_n': repetitions, 'numpy_version': np.__version__,
            'bit_generator': type(rng.bit_generator).__name__, 'alpha': ALPHA, 'target_power': .90,
            'n_grid': list(N_GRID), 'prospectively_fixed_equal_weight_lambdas': LAMBDAS.tolist(),
            'source_binding': {'path': 'analysis/simulate_roboboat_fixed_n_power_v1.py',
                               'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
            'score_values': SCORES.tolist(), 'alternative_scenarios': rows, 'stress_scenarios': stresses,
            'primary_test_candidate': 'At the single fixed N, reject only if equally weighted mixture product(1+lambda*X_i) >= 1/alpha.',
            'null': 'Independent possibly non-identical bounded configuration scores; average of their expected scores <=0.',
            'validity': 'For each fixed lambda, independence gives E[product]=product(1+lambda*E[X_i]); AM-GM bounds this by (1+lambda*mean(E[X_i]))^N<=1. Fixed mixture expectation<=1; Markov gives type-I<=alpha.',
            'sequential_validity_claimed': False,
            'missing_annotation_model': 'Independently unresolved whole-configuration judgments contribute adverse score -1 rather than being dropped. At true effect .1, 10% missing reduces mean to -.01; no advantage should be manufactured.',
            'uncertainty': 'Wilson 95% intervals measure finite Monte Carlo error for each row, not uncertainty about real effects or joint guarantees over all design scenarios.',
            'limitations': ['All effects and dependence models are hypothetical; no development recordings or response banks are read.',
                'N is independent sampled configurations, not six questions or repeated recordings. Valid sampling and measurement remain separate study requirements.',
                'This fixed-N e-value is valid for a weak average null. It is not asserted to be an e-process under ordered heterogeneous-family draws; optional stopping is not authorized.',
                'Mixture lambdas and sample size must be fixed before confirmation. Simulation-based planning does not freeze or activate inference.',
                'Fixed lambda mixture may be less powerful than an approximately normal score test; simulation must not be interpreted as validating the normal planner or retained sequential monitor.',
                'A proposed mixture-N grid has no sample ceiling. Lack of 90% power at 4000 calls for further planning or development rather than an automatic stop.',
                'Family mean differences, within-question dependence and missing annotation probabilities are assumed, not measured. Replication and technical-invalid inflation require separate additional configurations.'],
            'confirmation_n': 0, 'replication_n': 0, 'alpha_consumed': 0,
            'inferential_activation_authorized': False, 'confirmation_n_selected': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seed', type=int, default=42001)
    parser.add_argument('--repetitions', type=int, default=10000)
    args = parser.parse_args()
    report = build_report(args.seed, args.repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print('Wrote source-bound hypothetical fixed-N simulations:', args.output)


if __name__ == '__main__':
    main()
