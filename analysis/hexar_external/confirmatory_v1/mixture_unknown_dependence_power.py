"""Prospective outcome-dependent unknown sensitivity; no study artifacts read.

Unknown budgets are population probabilities, not a permission to remove data.
Each simulated pair is independent; flags within a pair may be correlated.
"""
import argparse
import hashlib
import math
from pathlib import Path

import numpy as np

from .journal import exclusive_json
from .mixture_family_power import REGIMES, ROOT, allocate, mapped_cells, simulate
from .mixture_statistics import power

NS = (72,114,192,384,576,768,1152,1296,1536,1920)


def dependent_cells(d, q, tie_failure_share, budget, mechanism):
    """Map a hypothetical complete endpoint under equal unknown budgets.

    Targeted flags share the same favorable pairs. Both flags turn favorable
    into reverse, decreasing the effect by two per affected pair. Remaining
    contract flags target both-success ties; prompt flags target both-failure
    ties. Budgets are upper bounds. This attains the minimum possible mean
    effect under the two budgets, but is NOT a universal worst-case power bound.
    Only a potentially successful contract / failing prompt can be unresolved
    here; this does not erase an independently established definite failure.
    """
    probabilities = (d,q,tie_failure_share,budget)
    if any(type(p) not in (float,int) or not math.isfinite(p) or not 0<=p<=1
           for p in probabilities):
        raise ValueError('finite planning probabilities in [0,1] required')
    if mechanism == 'independent':
        return mapped_cells(d,q,tie_failure_share,budget,budget)
    f,u,ss,ff = mapped_cells(d,q,tie_failure_share,0,0)
    if mechanism == 'shared_outcome_independent':
        # One shared Bernoulli flag: affected pairs map to reverse regardless
        # of original cell. Independent of their complete endpoint statuses.
        return [(1-budget)*f, (1-budget)*u+budget,
                (1-budget)*ss, (1-budget)*ff]
    if mechanism != 'favorable_targeted':
        raise ValueError('unknown planning mechanism')
    both = min(budget,f)
    contract_only = min(budget-both,ss)
    prompt_only = min(budget-both,ff)
    return [f-both,u+both+contract_only+prompt_only,
            ss-contract_only,ff-prompt_only]


def report(replications=40000, seed=2026100105, ns=NS):
    rng=np.random.default_rng(seed); rows=[]
    for design,weights in (('balanced',[1]*6),('weighted_sensitivity',[2,1,1,2,3,3])):
        for n in ns:
            counts=allocate(n,weights)
            for regime,ds,qs in REGIMES:
                for budget in (.01,.05):
                    for mechanism in ('independent','shared_outcome_independent','favorable_targeted'):
                        cells=[dependent_cells(d,q,.5,budget,mechanism) for d,q in zip(ds,qs)]
                        estimate=simulate(rng,counts,cells,replications)
                        row=dict(n=n,design=design,family_valid_counts=counts,regime=regime,
                            family_discordance=ds,family_favorable_probability=qs,
                            per_method_episode_unknown_budget=budget,unknown_mechanism=mechanism,
                            mapped_family_cells=cells,
                            complete_endpoint_average_effect=sum(k*d*(2*q-1) for k,d,q in zip(counts,ds,qs))/n,
                            mapped_average_effect=sum(k*(p[0]-p[1]) for k,p in zip(counts,cells))/n,
                            conditional_on_full_valid_cohort_power=estimate,
                            power_mc_standard_error=math.sqrt(estimate*(1-estimate)/replications))
                        if all(p==cells[0] for p in cells):
                            f,u,_,_=cells[0]; discordance=f+u
                            row['homogeneous_exact_power']=power(n,discordance,f/discordance if discordance else .5)
                        rows.append(row)
    sources=(Path(__file__),Path(__file__).with_name('mixture_family_power.py'),
             Path(__file__).with_name('mixture_statistics.py'),Path(__file__).with_name('statistics.py'))
    return dict(schema='hexar-mixture-unknown-dependence-power/v1',phase='prospective_design_only',
        seed=seed,replications=replications,alpha=.01,selected_n=None,
        no_semantic_data_read=True,confirmatory_N=0,alpha_consumed=0,rows=rows,
        assumptions=['Independent episode pairs; outcome-dependent unknown flags may be correlated within each pair.',
            'Hypothetical tie failure share .5; unknown budgets apply separately within every family.',
            'Targeted construction minimizes mean mapped effect under budgets, not guaranteed minimum power.',
            'No outcome-driven exclusion, replacement or retry: all unknown episodes remain in fixed N.',
            'No adjudication error-rate inference or bound is supplied by these hypothetical probabilities.',
            'Whole-episode unknown probability is not a per-request or per-judge-call rate.',
            'Power is conditional on complete technically valid acquisition; invalid reserve remains separate.',
            'Unequal weights change the target population and are sensitivity only.'],
        source_hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources})


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'manifests/hexar_external/confirmatory_v1/mixture_unknown_dependence_power_v1.json')
    args=parser.parse_args();value=report();exclusive_json(args.output,value)
    print('PROSPECTIVE_DESIGN_ONLY',len(value['rows']),'rows; N unselected')
