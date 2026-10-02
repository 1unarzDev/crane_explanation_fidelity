#!/usr/bin/env python3
"""Exact development power: discordances, technical thinning, fixed terminal look.

Uses only Python's standard library. No semantic outputs are read.
"""
import json
import math
from functools import lru_cache
from pathlib import Path


def binomial_probabilities(n, p):
    if p == 0:
        return [1.] + [0.] * n
    if p == 1:
        return [0.] * n + [1.]
    mode = min(n, int((n + 1) * p))
    weights = [0.] * (n + 1)
    weights[mode] = 1.
    for k in range(mode, 0, -1):
        weights[k - 1] = weights[k] * k / (n - k + 1) * (1 - p) / p
    for k in range(mode, n):
        weights[k + 1] = weights[k] * (n - k) / (k + 1) * p / (1 - p)
    total = math.fsum(weights)
    return [v / total for v in weights]


@lru_cache(None)
def critical_b(m, sidedness, alpha=.01):
    # Directional rejection: B2-only failure count must be unusually large.
    threshold = alpha if sidedness == 'one-sided' else alpha / 2
    probs = binomial_probabilities(m, .5)
    tail = 0.
    for k in range(m, -1, -1):
        tail += probs[k]
        if tail > threshold * (1 + 1e-12):
            return k + 1
    return 0


@lru_cache(None)
def conditional_rejection(m, b, c, sidedness):
    cutoff = critical_b(m, sidedness)
    return math.fsum(binomial_probabilities(m, b / (b + c))[cutoff:])


def power(n, b, c, invalid, sidedness):
    # Invalidity is independent technical thinning, never performance dependent.
    # M~Bin(N,(1-invalid)*(b+c)); B|M~Bin(M,b/(b+c)).
    probabilities = binomial_probabilities(n, (1 - invalid) * (b + c))
    return math.fsum(prob * conditional_rejection(m, b, c, sidedness)
                     for m, prob in enumerate(probabilities) if prob > 1e-16)


def required_n(b, c, invalid, sidedness, target):
    low, high = 0, 100
    while power(high, b, c, invalid, sidedness) < target and high < 6400:
        high *= 2
    if power(high, b, c, invalid, sidedness) < target:
        return None
    while high - low > 1:
        mid = (high + low) // 2
        if power(mid, b, c, invalid, sidedness) >= target:
            high = mid
        else:
            low = mid
    return high


def main():
    scenarios = [( .05, .01), (.10, .02), (.15, .03), (.20, .05), (.25, .05)]
    rows = []
    for b, c in scenarios:
        for invalid in (0., .10, .20):
            for sidedness in ('one-sided', 'two-sided'):
                rows.append(dict(b2_only_failure_probability=b, b4_only_failure_probability=c,
                    paired_b2_minus_b4_risk_difference=b-c, discordance_probability=b+c,
                    invalid_episode_probability=invalid, test=sidedness,
                    power_by_acquired_primary_n={str(n): power(n,b,c,invalid,sidedness)
                        for n in (50,70,100,150,200,300,500,1000)},
                    minimum_acquired_primary_n_for_80pct_power=required_n(b,c,invalid,sidedness,.8),
                    minimum_acquired_primary_n_for_90pct_power=required_n(b,c,invalid,sidedness,.9)))
    result = dict(schema='crane-development-exact-paired-power/v1', alpha=.01,
        independent_unit='episode_configuration', development_only=True,
        confirmatory_freeze=False, method='Exact binomial marginalization over discordance counts; no Monte Carlo error',
        population='Equal persistent-discrepancy/measured-recovery target mixture; supplied b/c are mixture probabilities',
        stratum_caveat='Assumes independent sampling from equal target mixture (iid paired outcomes); exact fixed-quota heterogeneous strata need stratum-specific probabilities',
        invalidity_caveat='Technical invalidity independent of performance, modelled before complete-pair scoring',
        coverage_caveat='Power covers superiority only; satisfying useful coverage can further reduce scientific success probability',
        raw_failure_rate_caveat='Discordance probabilities identify risk difference but not absolute failure rates; common-failure probability remains unspecified',
        rows=rows)
    output=Path('manifests/analysis/evidence-calibration-handoff-exact-power-v1-development.json')
    output.write_text(json.dumps(result,indent=2)+'\n')
    lines=['# Development paired superiority power\n',
        'Exact paired binomial calculations at alpha 0.01. N counts independently acquired primary episode/configurations; masks and annotations add no N. This analysis spends no alpha and freezes no design.\n',
        'The ledger permits 0.01 candidate alpha, with 0.02 already consumed and 0.02 protected for replication. A prospectively directional B4 superiority test is compatible: the unfrozen redirect specifies exact McNemar without requiring a two-sided primary test, and the ledger allocates alpha without fixing sidedness. Both directions, absolute failure rates, paired risk difference and a two-sided episode interval must still be reported.\n',
        '| B2-only | B4-only | Reduction | Invalidity | Power N=100 one/two | N80 one/two | N90 one/two |\n|---:|---:|---:|---:|---:|---:|---:|']
    for b,c in scenarios:
        for inv in (0.,.1,.2):
            one,two=[r for r in rows if r['b2_only_failure_probability']==b and r['b4_only_failure_probability']==c and r['invalid_episode_probability']==inv]
            lines.append(f"| {b:.2f} | {c:.2f} | {b-c:.2f} | {inv:.0%} | {one['power_by_acquired_primary_n']['100']:.1%} / {two['power_by_acquired_primary_n']['100']:.1%} | {one['minimum_acquired_primary_n_for_80pct_power']} / {two['minimum_acquired_primary_n_for_80pct_power']} | {one['minimum_acquired_primary_n_for_90pct_power']} / {two['minimum_acquired_primary_n_for_90pct_power']} |")
    lines.extend(['\nThe available 100 unmaterialized v6 layouts would provide at most 100 acquired primary episodes if all are prospectively reassigned to the primary population. Including 30% controls reduces that to about 70 primary episodes. Thus the pool is inadequate for small effects and leaves no untouched v6 replication pool if fully consumed. Generate further independent configurations when needed; do not increase N using masks.\n',
        'Assumptions: independent episodes sampled from an equal mechanism mixture, with supplied probabilities applying to that mixture; independent technical invalidity. Fixed equal stratum quotas with heterogeneous discordances require a separate stratified calculation when development stratum estimates are available. Coverage success is additional to these superiority-only powers. Raw failure rates require the common-failure probability, which is not supplied here.\n',
        'Sources: `manifests/study/diagnostic-sequential-error-ledger-v2.json`, `manifests/study/evidence-calibration-error-budget-audit-v1.json`, `docs/EVIDENCE_CALIBRATION_PROTOCOL.md`, `manifests/study/command-motion-layout-freshness-audit-v1.json`.'])
    Path('docs/EVIDENCE_CALIBRATION_HANDOFF_POWER_DEVELOPMENT.md').write_text('\n'.join(lines)+'\n')
    print(output)

if __name__ == '__main__':
    main()
