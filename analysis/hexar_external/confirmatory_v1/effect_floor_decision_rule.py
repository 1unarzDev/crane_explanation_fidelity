"""Prospective effect-floor/reserve grid; no semantic reads or final N binding."""
import argparse
from fractions import Fraction
from functools import lru_cache
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import binom, beta

from .journal import exclusive_json
from .mixture_statistics import critical_count

ROOT = Path(__file__).resolve().parents[3]
NS = (72,114,768,1296,1920,3072)
EFFECT = .10
REPLICATIONS = 100000
SEED = 2026100112


def regimes():
    result = []
    for d in (.10,.25,.50,.75,1.):
        result.append(dict(name=f'homogeneous_d_{d}', discordance=[d]*6, effects=[EFFECT]*6, primary=True))
        for strength, name in ((.35,'mild'),(.80,'strong')):
            amplitude = strength*(d-EFFECT)
            effects = [EFFECT+amplitude*t for t in (-1.,-.6,-.2,.2,.6,1.)]
            result.append(dict(name=f'{name}_heterogeneity_d_{d}', discordance=[d]*6, effects=effects, primary=True))
    result.append(dict(name='unequal_discordance', discordance=[.10,.20,.40,.60,.80,1.], effects=[EFFECT]*6, primary=True))
    result.append(dict(name='adverse_alignment', discordance=[.20,.35,.50,.65,.80,.95],
                       effects=[-.15,-.10,-.05,.15,.25,.50], primary=True))
    result.append(dict(name='historical_planning_anchor_not_effect_floor', discordance=[.5]*6, effects=[.3]*6, primary=False))
    return result


def homogeneous_power(n, d, q, thresholds):
    m = np.arange(n+1)
    weights = binom.pmf(m,n,d)
    conditional = binom.sf(np.asarray(thresholds[:n+1])-1,m,q)
    value = float(np.dot(weights, conditional))
    if not math.isfinite(value) or not 0 <= value <= 1+1e-12 or abs(float(weights.sum())-1) > 1e-10:
        raise ValueError('binomial probability arithmetic failed')
    return min(1.,value)


def technical_failure_probability(valid_quota, total_attempts, invalid):
    if (type(valid_quota) is not int or type(total_attempts) is not int or
            not 1 <= valid_quota <= total_attempts or not isinstance(invalid,Fraction) or not 0 <= invalid < 1):
        raise ValueError('fixed valid quota, finite cap and exact invalidity probability required')
    if invalid == 0:
        return Fraction(0)
    bad, denominator = invalid.numerator, invalid.denominator
    good = denominator-bad
    term, numerator = bad**total_attempts, 0
    for i in range(valid_quota):
        numerator += term
        if i+1 < valid_quota:
            term = term*(total_attempts-i)*good//((i+1)*bad)
    return Fraction(numerator,denominator**total_attempts)


def reserve(valid_quota, invalid, target=Fraction(99,100)):
    if not isinstance(target,Fraction) or not 0 < target < 1:
        raise ValueError('exact target completion probability required')
    attempts = valid_quota
    while True:
        failure = technical_failure_probability(valid_quota, attempts, invalid)
        guaranteed = max(Fraction(0),1-6*failure)
        if guaranteed >= target:
            return dict(valid_per_family=valid_quota, maximum_attempts_per_family=attempts,
                reserve_per_family=attempts-valid_quota, invalidity_cap_exact=str(invalid),
                union_completion_lower=float(guaranteed),
                union_completion_lower_exact=str(guaranteed),
                independent_family_completion=float((1-failure)**6))
        attempts += 1


def report():
    threshold = [critical_count(m,.01) for m in range(max(NS)+1)]
    configurations = regimes()
    rng = np.random.default_rng(SEED)
    rows = []
    tail = .05/(len(NS)*len(configurations))
    for n in NS:
        for configuration in configurations:
            discordant = np.zeros(REPLICATIONS,dtype=int)
            favorable = np.zeros(REPLICATIONS,dtype=int)
            probabilities = []
            for d, effect in zip(configuration['discordance'],configuration['effects']):
                q = (1+effect/d)/2
                if not 0 <= q <= 1:
                    raise ValueError('invalid family paired regime')
                probabilities.append(q)
                m = rng.binomial(n//6,d,size=REPLICATIONS)
                discordant += m
                favorable += rng.binomial(m,q)
            count = int(np.sum(favorable >= np.asarray(threshold)[discordant]))
            lower = float(beta.ppf(tail,count,REPLICATIONS-count+1)) if count else 0.
            exact = None
            if len(set(configuration['discordance']))==1 and len(set(configuration['effects']))==1:
                exact = homogeneous_power(n,configuration['discordance'][0],probabilities[0],threshold)
            rows.append(dict(configuration,n=n,family_n=[n//6]*6,
                family_favorable_probabilities=probabilities,
                balanced_average_mapped_effect=sum(configuration['effects'])/6,
                simulated_rejections=count,replications=REPLICATIONS,simulated_power=count/REPLICATIONS,
                simultaneous_MC_lower=lower,enumerated_homogeneous_power=exact))
        print('Completed hypothetical N',n,flush=True)
    eligible = [n for n in NS if all(r['simultaneous_MC_lower'] >= .90 and
        (r['enumerated_homogeneous_power'] is None or r['enumerated_homogeneous_power'] >= .90)
        for r in rows if r['n']==n and r['primary'])]
    reserves = [dict(n=n,**reserve(n//6,p)) for n in NS for p in (Fraction(1,20),Fraction(1,10),Fraction(1,5))]
    sources = [Path(__file__),Path(__file__).with_name('mixture_statistics.py'),
               ROOT/'docs/hexar_external/confirmatory_v1/EFFECT_FLOOR_DECISION_RULE.md']
    return dict(schema='hexar-effect-floor-decision-rule-planning/v1',phase='prospective_design_only',
        final_n=None,candidate_mapped_effect_floor=EFFECT,accepted_effect_floor=None,
        target_power=.90,conditional_grid_recommendation=eligible[0] if eligible else None,
        primary_row_count=sum(r['primary'] for r in rows),rows=rows,reserves=reserves,
        thresholds_sha256=hashlib.sha256(json.dumps(threshold,separators=(',',':')).encode()).hexdigest(),
        monte_carlo_simultaneous_coverage=.95,per_row_MC_tail=tail,seed=SEED,
        software_versions={name:importlib.metadata.version(name) for name in ('numpy','scipy')},
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        no_semantic_inputs=True,confirmatory_N=0,alpha_consumed=0,confirmation_authorized=False,
        exactness='Primary rejection thresholds use exact rational arithmetic. Homogeneous probabilities use enumerated floating binomial tails; reserve probabilities are exact rational.',
        applicability='Sampled hypothetical regimes and explicit mapped-effect assumption only; no universal power guarantee or final N/invalidity-cap decision.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():
        raise SystemExit('planning report exists; no overwrite')
    value=report();exclusive_json(args.output,value)
    print('Conditional grid recommendation',value['conditional_grid_recommendation'],flush=True)
