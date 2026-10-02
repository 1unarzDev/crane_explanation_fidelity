#!/usr/bin/env python3
"""Prospective sensitivity for the six-question paired configuration endpoint.

No study observations or provider calls are read. The moment calculation is a
large-N planning approximation, not the power of the retained e-process and not
an exact McNemar test: each configuration contributes one mean in [-1, 1].
The distribution-free calculation instead specifies a conservative fixed-N
Hoeffding test and a guaranteed lower bound on its power.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist

QUESTIONS_PER_CONFIGURATION = 6


def probability(value: float, name: str, *, open_interval: bool = False) -> None:
    if not math.isfinite(value) or not (0 < value < 1 if open_interval else 0 <= value <= 1):
        raise ValueError(f'{name} must be finite and in ' + ('(0, 1)' if open_interval else '[0, 1]'))


def cluster_variance(net_improvement: float, discordance: float, difference_icc: float) -> float:
    """Var(mean of 6 differences), assuming equal moments/exchangeable covariance.

    Each paired answer difference Y = B4_success - B2_success is -1, 0 or 1.
    E[Y]=delta, E[Y^2]=q, and Cov(Y_i,Y_j)=rho*(q-delta^2).
    Rho refers to paired DIFFERENCES, not marginal method-success ICC.
    """
    probability(net_improvement, 'net_improvement')
    probability(discordance, 'discordance')
    probability(difference_icc, 'difference_icc')
    if net_improvement > discordance:
        raise ValueError('net improvement cannot exceed total discordance')
    return (discordance - net_improvement**2) * (1 + 5 * difference_icc) / 6


def normal_planning_n(net_improvement: float, discordance: float, difference_icc: float,
                      target_power: float = .90, alpha: float = .025) -> int:
    probability(net_improvement, 'net_improvement', open_interval=True)
    probability(target_power, 'target_power', open_interval=True)
    probability(alpha, 'alpha', open_interval=True)
    if target_power <= alpha:
        raise ValueError('target power must exceed alpha')
    variance = cluster_variance(net_improvement, discordance, difference_icc)
    z = NormalDist().inv_cdf(1-alpha) + NormalDist().inv_cdf(target_power)
    return max(2, math.ceil(z*z * variance / net_improvement**2))


def normal_power(configurations: int, net_improvement: float, discordance: float,
                 difference_icc: float, alpha: float = .025) -> float:
    if type(configurations) is not int or configurations < 2:
        raise ValueError('configurations must be an integer at least 2')
    probability(alpha, 'alpha', open_interval=True)
    variance = cluster_variance(net_improvement, discordance, difference_icc)
    if variance == 0:
        raise ValueError('normal approximation requires positive variance')
    return NormalDist().cdf(net_improvement * math.sqrt(configurations/variance)
                            - NormalDist().inv_cdf(1-alpha))


def hoeffding_planning_n(net_improvement: float, target_power: float = .90,
                        alpha: float = .025) -> int:
    """Sufficient N for fixed-N bounded-mean superiority test with given power.

    Reject mean<=0 if observed configuration average exceeds sqrt(2 log(1/a)/N).
    For independent scores in [-1,1] with mean at least delta, power is at least
    1-exp(-N*(delta-threshold)^2/2). No ICC assumption is needed. This test is
    deliberately conservative and is separate from the asymptotic score test.
    """
    probability(net_improvement, 'net_improvement', open_interval=True)
    probability(target_power, 'target_power', open_interval=True)
    probability(alpha, 'alpha', open_interval=True)
    numerator = (math.sqrt(2*math.log(1/alpha)) + math.sqrt(2*math.log(1/(1-target_power))))**2
    return math.ceil(numerator / net_improvement**2)


def hoeffding_power_lower_bound(configurations: int, net_improvement: float,
                                alpha: float = .025) -> float:
    if type(configurations) is not int or configurations < 1:
        raise ValueError('configurations must be a positive integer')
    probability(net_improvement, 'net_improvement')
    probability(alpha, 'alpha', open_interval=True)
    gap = net_improvement - math.sqrt(2*math.log(1/alpha)/configurations)
    return 0.0 if gap <= 0 else -math.expm1(-configurations*gap*gap/2)


def binomial_at_least(total: int, needed: int, valid_probability: float) -> float:
    """P(at least needed technically valid clusters); stable log-PMF sum."""
    if type(total) is not int or type(needed) is not int or total < 0 or needed < 0:
        raise ValueError('counts must be nonnegative integers')
    probability(valid_probability, 'valid_probability')
    if needed == 0:
        return 1.0
    if total < needed or valid_probability == 0:
        return 0.0
    if valid_probability == 1:
        return 1.0
    logp, logq = math.log(valid_probability), math.log1p(-valid_probability)
    logs = [math.lgamma(total+1)-math.lgamma(k+1)-math.lgamma(total-k+1)
            + k*logp + (total-k)*logq for k in range(needed, total+1)]
    top = max(logs)
    return min(1.0, math.exp(top) * math.fsum(math.exp(x-top) for x in logs))


def collection_budget(valid_n: int, invalid_rate: float, assurance: float = .95) -> dict:
    """Both variants must be valid; invalid_rate is the whole-cluster rate."""
    if type(valid_n) is not int or valid_n < 1:
        raise ValueError('valid_n must be a positive integer')
    probability(invalid_rate, 'invalid_rate')
    probability(assurance, 'assurance', open_interval=True)
    if invalid_rate == 1:
        raise ValueError('cannot collect valid configurations at invalid_rate=1')
    expected = math.ceil(valid_n/(1-invalid_rate))
    low, high = valid_n-1, max(valid_n, expected)
    while binomial_at_least(high, valid_n, 1-invalid_rate) < assurance:
        high *= 2
    while high-low > 1:
        middle = (high+low)//2
        if binomial_at_least(middle, valid_n, 1-invalid_rate) >= assurance:
            high = middle
        else:
            low = middle
    return {'valid_configuration_target': valid_n, 'whole_configuration_invalid_rate': invalid_rate,
            'expected_attempted_configurations': expected, 'assurance': assurance,
            'attempted_configurations_for_assurance': high,
            'physical_variant_recordings_for_assurance': 2*high,
            'attainment_probability': binomial_at_least(high, valid_n, 1-invalid_rate)}


def build_plan() -> dict:
    rows = []
    for delta in (.05, .10, .15, .20):
        for discordance in (.20, .40, .60):
            for rho in (0., .25, .50, 1.):
                for alpha in (.025, .05):
                    ns = {str(power): normal_planning_n(delta, discordance, rho, power, alpha)
                          for power in (.80, .90)}
                    rows.append({'net_improvement_assumption': delta,
                        'question_total_discordance_assumption': discordance,
                        'question_B4_only_probability': (discordance+delta)/2,
                        'question_B2_only_probability': (discordance-delta)/2,
                        'within_configuration_difference_icc_assumption': rho,
                        'one_sided_alpha': alpha, 'cluster_score_variance': cluster_variance(delta, discordance, rho),
                        'normal_approximate_valid_configuration_n': ns,
                        'approximate_power_by_valid_configuration_n': {
                            str(n): normal_power(n, delta, discordance, rho, alpha)
                            for n in (40, 80, 100, 150, 250, 500, 1000)}})
    # This is a resource-planning example, deliberately pessimistic about
    # correlation; development must establish the final design assumptions.
    example_n = normal_planning_n(.10, .40, 1., .90, .025)
    return {
        'schema': 'roboboat-population-power-sensitivity/v1-development',
        'status': 'PROSPECTIVE_DESIGN_SENSITIVITY_NOT_OBSERVED_EFFECT',
        'inferential_activation_authorized': False,
        'alpha_consumed': 0,
        'source_endpoint': 'roboboat_material_workflow_v3.paired_cluster / roboboat_cluster_analysis.score_cluster',
        'independent_unit': 'one fresh sampled configuration, both physical variants, six fixed answers',
        'development_observations': {'valid_recordings': 7, 'approach_clusters': 3,
            'confirmatory_n': 0, 'current_comparison': 'tied; no positive effect estimate used'},
        'primary_estimand': 'population mean of configuration-average B4 minus B2 material-success differences',
        'planning_method': 'one-sided normal fixed-N cluster-mean approximation; no question-level pseudoreplication',
        'moment_equation': 'Var(configuration mean)=(q-delta^2)*(1+5*rho)/6',
        'minimum_meaningful_improvement_candidate': {'value': .10,
            'interpretation': 'ten percentage points more successful answers averaged equally across configurations',
            'status': 'scientific design candidate requiring pre-confirmation justification; not pilot-derived or frozen'},
        'sensitivity': rows,
        'distribution_free_fixed_n_alternative': {
            'test': 'reject nonpositive mean only when sample mean > sqrt(2*log(1/alpha)/N)',
            'scores': 'independent configuration scores in [-1,1]; adverse bounds permitted',
            'rows': [{'net_improvement_assumption': delta, 'one_sided_alpha': .025,
                      'sufficient_valid_configuration_n': {
                          str(p): hoeffding_planning_n(delta, p, .025) for p in (.80, .90)}}
                     for delta in (.05, .10, .15, .20)]},
        'resource_planning_example': {'delta': .10, 'discordance': .40, 'difference_icc': 1.,
            'one_sided_alpha': .025, 'target_power': .90, 'valid_n': example_n,
            'invalid_rate_sensitivity': [collection_budget(example_n, rate) for rate in (0., .05, .10, .20)],
            'recommendation': 'Plan capacity for hundreds of independent configurations, then refine N with a broader development pilot; do not stop at 40 or promote a tie.'},
        'annotation_uncertainty': {
            'separate_from_technical_invalidity': True,
            'bound': 'if u is the unresolved fraction across all 12 method-answer cells, true difference minus adverse difference <= 2*u',
            'effective_effect_lower_bound_examples': [
                {'true_delta_assumption': .10, 'unresolved_cell_fraction': u,
                 'adverse_mean_effect_lower_bound': round(.10-2*u, 12)} for u in (0., .01, .025, .05)],
            'rule': 'Do not drop unresolved judgments; model adverse-score moments separately or use the distribution-free alternative at a positive adverse mean.'},
        'limitations': [
            'All nonzero effects, discordances and correlations are hypothetical sensitivity assumptions; construction suites establish no effect or power.',
            'Normal N is approximate, not exact power, and does not apply to the retained sequential e-process. Freeze the final test before confirmation and validate its operating characteristics under appropriate score distributions.',
            'Equal question moments/exchangeable covariance are simplifications. Six questions and two variants add no independent N; use configuration score variance directly once development permits.',
            'Independence is across sampled configuration identities, not episode filenames, question variants or repeated runs. Related approaches/shared seeds may require grouping and alter N.',
            'Technical-invalid inflation assumes independent method-blind configuration validity and iid invalid rate. If per-variant invalid rates are used, whole-configuration invalid rate is 1-(1-r)^2 only under independent variant failures.',
            'Informative validity, family heterogeneity and judge errors require design or measurement checks; increasing N alone does not remove bias.',
            'Unresolved annotation bounds are not confidence intervals; normal planning for complete scores does not establish power of the adverse-bound analysis.',
            'No marginal B4/B2 success rates, annotation reliability or pilot variance have been invented. Replication requires additional fresh configuration identities.',
            'A fixed-N rule cannot be replaced by repeated unadjusted significance checks. Any sequential design needs its own prospective stopping rule and power calculation.'
        ]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(build_plan(), indent=2, allow_nan=False)+'\n')
    print(f'Wrote prospective sensitivity (no study inference): {args.output}')


if __name__ == '__main__':
    main()
