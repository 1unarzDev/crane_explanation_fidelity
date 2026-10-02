#!/usr/bin/env python3
"""Hypothetical clustered planning, never a study look or alpha allocation."""
import hashlib
import json
from pathlib import Path
import numpy as np
from simulate_sequential_diagnostic_design import _update_log_capital,_log_mixture,_wilson_interval
from build_roboboat_terminal_batch import save

ROOT=Path(__file__).resolve().parents[1]


def simulate(plus,minus,scope,seed,null):
    replicates=2000
    rng=np.random.default_rng(seed)
    protocol=ROOT/'research/explanation_fidelity/experiment_configs/prospective/diagnostic-sequential-protocol-v2.json'
    fractions=np.array(json.loads(protocol.read_text())['analysis']['betting_fractions'])
    capital=np.zeros((replicates,len(fractions)))
    crossed=np.zeros(replicates,dtype=bool)
    reviews=[]
    for count in range(1,101):
        shape=(replicates,2) if scope=='only_L2_independent_pair' else (replicates,)
        u=rng.random(shape)
        values=np.where(u<plus,1.,np.where(u<plus+minus,-1.,0.))
        if scope=='only_L2_independent_pair':values=values.sum(axis=1)/6
        elif scope=='only_L2_correlated_pair':values=values/3
        _update_log_capital(capital,values,null,fractions)
        if count in (24,48,100):
            crossed|=_log_mixture(capital)>=np.log(1/.005)
            successes=int(crossed.sum())
            reviews.append({'cluster_n':count,'crossing_rate':successes/replicates,
                            'monte_carlo_wilson95':_wilson_interval(successes,replicates)})
    return {'hypothetical_plus':plus,'hypothetical_minus':minus,'scope':scope,
            'true_cluster_mean':(plus-minus)/(3 if scope.startswith('only_L2') else 1),
            'null_mean':null,'hypothetical_alpha':.005,'seed':seed,
            'replicates':replicates,'reviews':reviews}


def main():
    scenarios=[]
    for index,(plus,minus) in enumerate(((.05,.05),(.25,.05),(.45,.05))):
        for scope in ('all_questions_correlated','only_L2_correlated_pair','only_L2_independent_pair'):
            for null in (0.,.1):
                scenarios.append(simulate(plus,minus,scope,97000+index,null))
    protocol=ROOT/'research/explanation_fidelity/experiment_configs/prospective/diagnostic-sequential-protocol-v2.json'
    result={'schema':'roboboat-hypothetical-cluster-planning/v1',
            'disposition':'SIMULATION_ONLY_NO_REAL_RESPONSES_NO_ALLOCATION',
            'source_protocol_sha256':hashlib.sha256(protocol.read_bytes()).hexdigest(),
            'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'pilot_effect_estimate_used':False,'agent_label_error_simulated':False,
            'limitation':'Hypothetical distributions and perfect semantic labels; not a power justification for the observed tie. Planning reviews/alpha are proposals, not approved boat stopping rules.',
            'scenarios':scenarios,'physical_n_added':0,'alpha_allocated_or_consumed':0}
    save(ROOT/'artifacts/roboboat-terminal-planning-v1/sequential-planning.json',result)
    for r in scenarios:
        print(r['scope'],'effect',round(r['true_cluster_mean'],4),'threshold',r['null_mean'],
              '100-cluster crossing',r['reviews'][-1]['crossing_rate'])


if __name__=='__main__':main()
