"""Exact power and seeded recording-level design sensitivities, no study calls."""
import json
from pathlib import Path
import numpy as np
try:
    from .statistics import exact_power, rejection_threshold
except ImportError:
    from statistics import exact_power, rejection_threshold

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / 'manifests/hexar_external/confirmatory_v1'
SEED = 20260930


def main():
    rows = []
    for d in (0.2, 0.35, 0.5, 0.65):
        for q in (0.65, 0.7, 0.75, 0.8, 0.85):
            required = next((n for n in range(6, 721, 6)
                             if exact_power(n, d, q) >= 0.9), None)
            rows.append(dict(discordance=d, favorable_given_discordance=q,
                             recording_risk_difference=d * (2*q-1),
                             power_at_72=exact_power(72, d, q),
                             required_valid_n_90_percent_balanced=required))
    rng = np.random.default_rng(SEED)
    thresholds = np.array([rejection_threshold(m) for m in range(73)])
    sims = []
    # Independent physical episodes; heterogeneity is across fixed families.
    regimes = [([.5]*6, [.8]*6, 'homogeneous'),
               ([.2,.3,.4,.6,.7,.8], [.8]*6, 'family_discordance'),
               ([.5]*6, [.6,.7,.75,.85,.9,1.0], 'family_direction'),
               ([.2,.3,.4,.6,.7,.8], [1,.9,.85,.75,.7,.6], 'adverse_covariation')]
    for ds, qs, name in regimes:
        for invalid in (0., .05, .1, .2):
            trials = 40000
            favorable = np.zeros(trials, dtype=int)
            unfavorable = np.zeros(trials, dtype=int)
            complete = np.ones(trials, dtype=bool)
            for d, q in zip(ds, qs):
                # Candidate reserve: 16 attempts/family, select first 12 valid
                # using technical criteria alone. Semantic failures never replace.
                available = rng.binomial(16, 1-invalid, trials)
                complete &= available >= 12
                outcomes = rng.multinomial(12, [d*q, d*(1-q), 1-d], trials)
                favorable += outcomes[:, 0]
                unfavorable += outcomes[:, 1]
            reject = favorable >= thresholds[favorable + unfavorable]
            sims.append(dict(regime=name, invalid_rate=invalid,
                             family_d=ds, family_q=qs, replications=trials,
                             full_cohort_available=float(complete.mean()),
                             semantic_power_if_complete=float(reject.mean()),
                             probability_complete_and_reject=float((complete & reject).mean()),
                             monte_carlo_se_max=0.0025))
    # A 9-answer battery changes whole-recording failure/disagreement, not N.
    battery = []
    for dependence in (0., .5, 1.):
        n = 40000
        shared = rng.random((n, 1))
        uniforms = rng.random((n, 9))
        use_shared = rng.random((n, 9)) < dependence
        u = np.where(use_shared, shared, uniforms)
        # Deliberately degraded answer-level advantage; nested errors are a
        # sensitivity scenario, never evidence of zero unfavorable recordings.
        cf = (u < .04).any(axis=1)
        pf = (u < .10).any(axis=1)
        d = float(np.mean(cf != pf))
        battery.append(dict(within_recording_common_shock_probability=dependence,
                            contract_failure=float(cf.mean()), prompt_failure=float(pf.mean()),
                            total_discordance=d, unfavorable=0,
                            interpretation='illustrative nested-error model only; broad two-direction grid above governs N'))
    result = dict(schema='hexar-confirmatory-power/v1', alpha=.01, target_power=.9,
                  seed=SEED, exact_enumeration=True, independent_unit='physical recording',
                  planning_point_power_72=exact_power(72,.5,.8), table=rows,
                  heterogeneity_and_invalid_sensitivity=sims, battery_dependence_sensitivity=battery,
                  n_decision='72 VALID RECORDINGS CANDIDATE ONLY; alpha/cohort/assumptions unresolved',
                  reserve_candidate='16 attempts per family, 96 total; first 12 technically valid per family; no expansion if exhausted')
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST/'power_report.json').write_text(json.dumps(result, indent=2)+'\n')
    lines = ['# Prospective power sensitivity', '',
             f'Exact one-sided alpha .01; at d=.50 and q=.80, N=72 power = {result["planning_point_power_72"]:.6f}.', '',
             'The recording-level effect at that point is **30 points**, not the development answer-level 9.3 points. These endpoints are different. N=72 is conditional planning, not general evidence of adequate power.', '',
             '| Discordance | Favorable conditional | Recording risk difference | Power N=72 | N for 90% (multiples of 6) |',
             '|---:|---:|---:|---:|---:|']
    for r in rows:
        lines.append(f'| {r["discordance"]:.2f} | {r["favorable_given_discordance"]:.2f} | {r["recording_risk_difference"]:.3f} | {r["power_at_72"]:.3f} | {r["required_valid_n_90_percent_balanced"] or ">720"} |')
    lines += ['', 'The JSON retains 40,000 seeded simulations per family/invalidity regime, with maximum Monte Carlo SE .0025. Reserve exhaustion leads to no confirmatory claim, never enlargement after semantic inspection. Within-battery common shocks illustrate how nine correlated answers affect the recording endpoint; answers never become independent N.', '',
              'Family scenarios include heterogeneous discordance and adverse covariation of discordance with effect direction. Exchangeability/IID assumptions of the proposed conditional test and interval remain an admission gate; sensitivity power is not a proof of type-I control under arbitrary heterogeneity.']
    (ROOT/'docs/hexar_external/confirmatory_v1/POWER.md').write_text('\n'.join(lines)+'\n')

if __name__ == '__main__':
    main()
