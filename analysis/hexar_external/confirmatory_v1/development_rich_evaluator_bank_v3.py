"""Authored taxonomy-clarified development bank; not confirmation data."""
import copy
import hashlib
import json
from pathlib import Path

from .development_rich_evaluator_bank import ROOT, UNITS, build as previous_build, project
from .journal import exclusive_json
from .rich_evaluator_v2 import CLARIFICATION

DEST=ROOT/'manifests/hexar_external/confirmatory_v1/development_rich_evaluator_bank_v3'


def build():
    fixtures=previous_build()
    for fixture in fixtures:
        if fixture['fixture_id']=='masked_invented_motion':
            fixture['expected']['overlicensed_specificity']=False
            fixture['development_amendment']='Invented source-bounded observation is unsupported material without an additional mechanism attribution.'
    base=copy.deepcopy(next(f for f in fixtures if f['fixture_id']=='bounded_positive'))
    extras=[
        ('rounded_numeric_positive',base['answer'].replace('0.00000464 m','approximately 0.000 m'),False,False),
        ('covariation_not_cause',base['answer']+' Co-occurring reports do not establish that manual selection caused the outcome.',False,False),
        ('wrong_frame_arrival',base['answer']+' These odom-frame samples prove I did not reach the map-frame goal.',True,True),
    ]
    for name,answer,unsupported,specific in extras:
        fixture=copy.deepcopy(base);fixture.update(fixture_id=name,answer=answer,
            expected=dict(unsupported_material=unsupported,overlicensed_specificity=specific,covered_units=list(UNITS)))
        fixtures.append(fixture)
    masked=copy.deepcopy(next(f for f in fixtures if f['fixture_id']=='masked_bounded'))
    masked.update(fixture_id='masked_invented_mechanism',
                  answer='Navigation software reported success. A physical obstacle prevented my motion.',
                  expected=dict(unsupported_material=True,overlicensed_specificity=True,covered_units=[UNITS[0]]))
    fixtures.append(masked)
    for fixture in fixtures:project(fixture)
    return fixtures


def main():
    DEST.mkdir(parents=True,exist_ok=True);fixtures=build()
    prior=ROOT/'manifests/hexar_external/confirmatory_v1/development_rich_evaluator_bank_v2/fixtures.json'
    exclusive_json(DEST/'fixtures.json',dict(schema='hexar-authored-rich-evaluator-bank/v3',phase='development_only',
        status='PREPARED_NOT_PROVIDER_SCORED',fixtures=fixtures,confirmatory_n=0,provider_calls=0,alpha_consumed=0,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        prior_bank_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
        component_taxonomy=CLARIFICATION,human_validated=False,automated_semantic_qualification=False,
        previous_failed_screen_threshold_not_relaxed=True,
        revision='Development construct clarification only. Primary unsupported-material labels unchanged on existing fixtures; no method-outcome labels used.'))
    print(len(fixtures),'authored taxonomy-clarified fixtures; no provider calls')


if __name__=='__main__':main()
