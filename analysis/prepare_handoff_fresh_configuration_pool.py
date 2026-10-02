#!/usr/bin/env python3
"""Create untouched candidate configurations; allocation is NOT a semantic freeze.

IID profile and geometry draws are made before any episode or method output. Every
configuration has a unique seed; ordered candidates permit technical-only attrition.
"""
import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'packages/crane_ml/Tools/ReferenceEnvironments'))
from generate_diagnostic_land_catalog import generate,generate_stratum,validate


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--confirmation-candidates',type=int,default=2000)
    parser.add_argument('--replication-candidates',type=int,default=1600)
    args=parser.parse_args()
    base=generate();catalog={k:base[k] for k in ['schema','dimensionsMeters','sharedBoxes']}
    catalog.update(environmentId='crane-land-proving-ground-v10',generatorVersion='handoff-independent-candidates-v1',
        generator=dict(algorithm='IID Python random.Random(2026093001) profile/geometry/response draws; unique geometry seeds',
            confirmationCandidates=args.confirmation_candidates,replicationCandidates=args.replication_candidates),layouts=[])
    rows=[];rng=random.Random(2026093001)
    for stage,count,seed_base in [('confirmation',args.confirmation_candidates,5100000),('replication',args.replication_candidates,5300000)]:
        for i in range(count):
            geometry=rng.choice(['connected-detour','nominal-clear-route'])
            profile=rng.choice(['persistent-low','persistent-intermittent','partial-recovery','full-recovery'])
            seed=seed_base+2*i
            # Random orientation too: selected seed remains unique across every candidate.
            orientation=rng.randrange(2)
            layout=generate_stratum('handoff-'+stage+'-candidate',geometry,2,seed)[orientation]
            identity=f'handoff-{stage}-candidate-{i+1:04d}'
            layout['id']=identity;catalog['layouts'].append(layout)
            onset=rng.randint(18,26);release=onset+rng.randint(10,18) if 'recovery' in profile else -1.
            response=dict(responseAfterSeconds=float(onset),responseReleaseAfterSeconds=float(release),
                responseGain=0. if profile=='persistent-intermittent' else round(rng.uniform(.05,.18),4),
                responseRecoveredGain=round(rng.uniform(.35,.85),4) if profile=='partial-recovery' else 1.,
                responsePeriodSeconds=round(rng.uniform(1.5,3.),4) if profile=='persistent-intermittent' else 0.,
                responseDuty=round(rng.uniform(.65,.85),4) if profile=='persistent-intermittent' else 1.)
            rows.append(dict(stage=stage,run_id=identity,cluster_id=identity+'-configuration',catalog_id='v10',
                layout_id=identity,layout_seed=layout['seed'],geometry_mechanism=geometry,response_profile=profile,
                evaluator_response=response))
    validate(catalog)
    destination=ROOT/'packages/crane_ml/Assets/Resources/ReferenceEnvironments/crane_land_proving_ground_v10.json'
    raw=json.dumps(catalog,indent=2)+'\n'
    if destination.exists() and destination.read_text()!=raw:raise RuntimeError('Existing pool differs; do not rewrite an observed allocation')
    destination.write_text(raw)
    allocation=dict(schema='crane-handoff-fresh-candidates/v1',status='UNOBSERVED_CANDIDATES_NOT_FROZEN',
        semantic_outputs_allowed=False,development_use=False,alpha_bound_or_spent=0.,independent_unit='configuration',
        selection='IID equal four-profile mixture; IID equal geometry mixture; timing and gain vary independently within profile. Ordered candidates, no method-performance selection.',
        limitation='Candidate population differs from old fixed 50/50 realized mechanism quotas; a prospective scientific revision is required before confirmation.',
        catalog_sha256=hashlib.sha256(raw.encode()).hexdigest(),configurations=rows)
    out=ROOT/'manifests/study/evidence-calibration-handoff-fresh-candidates-v1.json'
    if out.exists() and json.loads(out.read_text())!=allocation:raise RuntimeError('Existing allocation differs')
    out.write_text(json.dumps(allocation,indent=2)+'\n')
    print(json.dumps(dict(confirmation_candidates=args.confirmation_candidates,replication_candidates=args.replication_candidates,
        semantic_outputs=0,confirmatory_freeze=False)))

if __name__=='__main__':main()
