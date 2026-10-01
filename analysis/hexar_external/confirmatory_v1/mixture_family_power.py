"""Hypothetical family/missingness/reserve planning for the mixture candidate.

No acquired episodes, answers or labels are read. No test or N is selected.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from .journal import exclusive_json
from .mixture_statistics import critical_count
from .statistics import tail

ROOT = Path(__file__).resolve().parents[3]
REGIMES = (
    ('homogeneous', [.5]*6, [.8]*6),
    ('variable_discordance', [.2,.3,.4,.6,.7,.8], [.8]*6),
    ('variable_direction', [.5]*6, [.6,.7,.75,.85,.9,1]),
    ('adverse_covariation', [.2,.3,.4,.6,.7,.8], [1,.9,.85,.75,.7,.6]),
    ('degraded_direction', [.5]*6, [.55,.6,.65,.75,.8,.85]),
    ('opposing_family_average_null', [.5]*6, [.2,.35,.45,.55,.65,.8]),
)
NS = (72,96,114,144,192,288,384,576,768,1152)


def mapped_cells(d, q, tie_failure_share, contract_missing, prompt_missing):
    """Pair probabilities after least-favorable whole-episode unknown mapping.

    Missing flags are independent of statuses and each other for this planning
    sensitivity only. Known definite failure is never erased by missing labels.
    An unknown successful contract becomes failure; an unknown failing prompt
    becomes success. This deliberately pessimistic episode model is not a
    fitted answer-level error model or a complete adjudication simulation.
    """
    if any(not 0 <= p <= 1 for p in (d,q,tie_failure_share,contract_missing,prompt_missing)):
        raise ValueError('planning probabilities in [0,1] required')
    # Index order: favorable, reverse, both success, both failure.
    source = ((False,True,d*q), (True,False,d*(1-q)),
              (False,False,(1-d)*(1-tie_failure_share)),
              (True,True,(1-d)*tie_failure_share))
    cells = [0.]*4
    for cf,pf,prob in source:
        for cm,pc in ((False,1-contract_missing),(True,contract_missing)):
            for pm,pp in ((False,1-prompt_missing),(True,prompt_missing)):
                c = cf or cm
                p = pf and not pm
                index = 0 if not c and p else 1 if c and not p else 2 if not c and not p else 3
                cells[index] += prob*pc*pp
    return cells


def allocate(n, weights):
    if type(n) is not int or n < 6 or len(weights) != 6 or any(w <= 0 for w in weights):
        raise ValueError('positive six-family allocation required')
    expected = np.array(weights, dtype=float)*n/sum(weights)
    counts = np.floor(expected).astype(int)
    # Frozen deterministic largest-remainder allocation, family order breaks ties.
    for i in sorted(range(6), key=lambda i: (-float(expected[i]-counts[i]),i))[:n-int(counts.sum())]:
        counts[i] += 1
    if (counts < 1).any():
        raise ValueError('all six families must be retained')
    return counts.tolist()


def simulate(rng, counts, cells, replications):
    if len(counts) != len(cells) or type(replications) is not int or replications < 1:
        raise ValueError('matching families and positive simulation size required')
    f = np.zeros(replications, dtype=int); u = f.copy()
    for count, probs in zip(counts, cells):
        pair = rng.multinomial(count, probs, replications)
        f += pair[:,0]; u += pair[:,1]
    thresholds = np.array([critical_count(m) for m in range(sum(counts)+1)])
    return float((f >= thresholds[f+u]).mean())


def report(replications=40000, seed=2026100104, ns=NS):
    rng = np.random.default_rng(seed); rows = []
    for design, weights in (('balanced',[1]*6), ('weighted_sensitivity',[2,1,1,2,3,3])):
        for n in ns:
            counts = allocate(n,weights)
            for regime, ds, qs in REGIMES:
                for missing in (0.,.01,.05):
                    cells = [mapped_cells(d,q,.5,missing,missing) for d,q in zip(ds,qs)]
                    power = simulate(rng,counts,cells,replications)
                    rows.append(dict(n=n,design=design,family_valid_counts=counts,regime=regime,
                        family_discordance=ds,family_favorable_probability=qs,
                        per_method_episode_unknown_probability=missing,
                        complete_endpoint_average_effect=sum(k*d*(2*q-1) for k,d,q in zip(counts,ds,qs))/n,
                        conservative_mapped_average_effect=sum(k*(p[0]-p[1]) for k,p in zip(counts,cells))/n,
                        conditional_on_full_valid_cohort_power=power,
                        power_mc_standard_error=math.sqrt(power*(1-power)/replications)))
    reserves=[]
    for n in ns:
        counts=allocate(n,[1]*6)
        for name,rates in (('homogeneous_05',[.05]*6),('homogeneous_10',[.10]*6),
                           ('homogeneous_20',[.20]*6),('heterogeneous',[.05,.05,.10,.10,.20,.30])):
            for reserve in (4,8,12,24):
                complete=math.prod(tail(k+reserve,k,1-rate) for k,rate in zip(counts,rates))
                reserves.append(dict(n=n,family_valid_counts=counts,regime=name,family_invalid_rates=rates,
                    reserve_per_family=reserve,full_cohort_completion_probability=complete))
    sources=(Path(__file__),Path(__file__).with_name('mixture_statistics.py'),Path(__file__).with_name('statistics.py'))
    return dict(schema='hexar-mixture-family-power-candidate/v1',phase='prospective_design_only',
        seed=seed,replications=replications,maximum_mc_standard_error=.5/math.sqrt(replications),alpha=.01,
        selected_n=None,selected_reserve=None,selected_procedure=None,no_semantic_data_read=True,
        confirmatory_N=0,alpha_consumed=0,rows=rows,reserve_rows=reserves,
        assumptions=['Independent episodes with nonidentical family probabilities.',
            'Hypothetical tie failure share .5, not estimated from pilot results.',
            'Unknown events independent of outcomes in this pessimistic whole-episode sensitivity.',
            'Technical invalidity independent across attempts; semantic dependence not estimated.',
            'Reserve completion is separate from conditional power; no successful-acquisition selection of favorable semantic outcomes.',
            'Weighted rows change the target population and are sensitivity only; do not choose weights using outcomes.',
            'Six distinct requests affect actual episode rates; this is direct episode-level planning, not six independent statistical observations.'],
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'manifests/hexar_external/confirmatory_v1/mixture_family_power_sensitivity_v1.json')
    args=parser.parse_args();value=report();exclusive_json(args.output,value)
    print('PROSPECTIVE_DESIGN_ONLY',len(value['rows']),'power rows; N/test unselected')
