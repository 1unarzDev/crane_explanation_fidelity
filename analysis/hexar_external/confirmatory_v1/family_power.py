"""Seeded prospective heterogeneity/invalidity sensitivity for candidate e-test."""
import json
import math
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]


def main():
    rng=np.random.default_rng(20261001)
    regimes=[('homogeneous',[.5]*6,[.8]*6),
             ('variable_discordance',[.2,.3,.4,.6,.7,.8],[.8]*6),
             ('variable_direction',[.5]*6,[.6,.7,.75,.85,.9,1]),
             ('adverse_covariation',[.2,.3,.4,.6,.7,.8],[1,.9,.85,.75,.7,.6]),
             ('degraded_direction',[.5]*6,[.55,.6,.65,.75,.8,.85]),
             ('average_null',[.5]*6,[.2,.35,.45,.55,.65,.8])]
    rows=[]; replications=40000
    for n in (72,96,120,144,192):
        for name,ds,qs in regimes:
            f=np.zeros(replications,dtype=int);u=f.copy()
            for d,q in zip(ds,qs):
                pair=rng.multinomial(n//6,[d*q,d*(1-q),1-d],replications)
                f+=pair[:,0];u+=pair[:,1]
            reject=f*math.log1p(.4)+u*math.log1p(-.4)>=math.log(100)
            for invalid in (0.,.05,.1,.2):
                # Reserve example only: four attempts/family. Does not set final N.
                complete=(rng.binomial(n//6+4,1-invalid,(replications,6))>=n//6).all(axis=1)
                rows.append(dict(n=n,regime=name,family_discordance=ds,family_favorable_probability=qs,
                                 true_average_risk_difference=sum(d*(2*q-1) for d,q in zip(ds,qs))/6,
                                 invalid_rate=invalid,reserve_attempts_per_family=4,
                                 conditional_on_full_cohort_power=float(reject.mean()),
                                 acquisition_complete_probability=float(complete.mean()),
                                 complete_and_reject_probability=float((complete & reject).mean())))
    out=dict(schema='hexar-family-power-candidate/v1',seed=20261001,replications=replications,
             monte_carlo_se_max=.0025,primary_candidate='fixed-N e-test lambda .4',alpha=.01,
             selected_n=None,selected_reserve=None,rows=rows,
             assumption='independent episodes, technical invalidity independent of semantic outcomes in this sensitivity simulation; observed acquisition rates needed before final reserve')
    path=ROOT/'manifests/hexar_external/confirmatory_v1/family_power_report.json'
    path.write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':main()
