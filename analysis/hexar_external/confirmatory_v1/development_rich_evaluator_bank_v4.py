"""Prospective development contrasts for intention, spatial progress and ambiguity."""
import copy
import hashlib
from pathlib import Path
from .development_rich_evaluator_bank_v3 import build as old_build
from .development_rich_evaluator_bank import ROOT,UNITS,EVIDENCE
from .journal import exclusive_json

DEST=ROOT/'manifests/hexar_external/confirmatory_v1/development_rich_evaluator_bank_v4'
NEW_EVIDENCE=EVIDENCE|{'requested_goal','observed_action_window','goal_frame_transform'}


def project(fixture):
    payload=copy.deepcopy({k:fixture[k] for k in ('question','visible_evidence','required_units','answer')})
    if type(payload['question']) is not str or type(payload['answer']) is not str:raise ValueError('text input required')
    if type(payload['visible_evidence']) is not dict or not set(payload['visible_evidence'])<=NEW_EVIDENCE or any(type(v) is not str for v in payload['visible_evidence'].values()):
        raise ValueError('closed authored evidence strings required')
    seen=set()
    for unit in payload['required_units']:
        if set(unit)!={'unit_id','requirement'} or unit['unit_id'] not in UNITS or type(unit['requirement']) is not str or unit['unit_id'] in seen:
            raise ValueError('closed unique useful units required')
        seen.add(unit['unit_id'])
    return payload


def build():
    fixtures=old_build()
    for fixture in fixtures:fixture['expected']['material_ambiguity']=False
    base=copy.deepcopy(next(f for f in fixtures if f['fixture_id']=='bounded_positive'))
    base['visible_evidence'].update(requested_goal='A navigation request targeted map-frame pose (-4.56, 0.93).',
        observed_action_window='The recorded action UUID was accepted, then returned software success; these driver observations are not physical arrival.',
        odometry='Sampled controller odometry estimated 8.18 m of XY path distance in the odom frame within the observed action window; no transform to map is supplied.',
        goal_frame_transform='unavailable')
    base['required_units'][2]['requirement']='Communicate sampled controller odometry travel in the odom frame within the observed software-action sample window; do not claim physical goal progress.'
    bounded='Navigation software reported success and the manual-priority indicator was on. Sampled odom-frame odometry estimated 8.18 m of XY travel in the observed action window; physical goal attainment is unknown.'
    contrasts=[
        ('explicit_accepted_intention', 'The accepted navigation request targeted a map-frame pose.',False,False,False),
        ('explicit_software_execution', 'I began executing the recorded navigation request in software.',False,False,False),
        ('explicit_motion_scope','The observed travel is an odom-frame estimate, not a measured reduction in map-frame goal distance.',False,False,False),
        ('unqualified_toward_ambiguous','I started toward the requested map pose.',False,False,True),
        ('unqualified_progress_ambiguous','I made progress toward the requested map pose.',False,False,True),
        ('explicit_map_closer','The robot physically became 1.82 m closer to the map-frame goal.',True,True,False),
        ('explicit_world_progress','The measured world-frame position advanced toward the goal.',True,True,False),
        ('intention_does_not_license_arrival','The accepted request targeted a map-frame pose, so I physically arrived there.',True,True,False),
    ]
    for name,extra,unsupported,specific,ambiguity in contrasts:
        fixture=copy.deepcopy(base);fixture.update(fixture_id=name,answer=bounded+' '+extra,
            expected=dict(unsupported_material=unsupported,overlicensed_specificity=specific,
                          covered_units=list(UNITS),material_ambiguity=ambiguity),
            provenance='AUTHORED_SYNTHETIC_DEVELOPMENT_CONTRAST_ONLY',eligible_for_confirmatory_n=False)
        fixtures.append(fixture)
    for fixture in fixtures:project(fixture)
    return fixtures


if __name__=='__main__':
    DEST.mkdir(exist_ok=True)
    prior=ROOT/'manifests/hexar_external/confirmatory_v1/development_rich_evaluator_bank_v3/fixtures.json'
    exclusive_json(DEST/'fixtures.json',dict(schema='hexar-authored-rich-evaluator-bank/v4',phase='development_only',
        fixtures=build(),prior_bank_sha256=hashlib.sha256(prior.read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        existing_primary_support_coverage_labels_preserved=True,agent_assessed=False,human_validated=False,
        confirmatory_N=0,alpha_consumed=0,provider_calls=0,status='PREPARED_NOT_PROVIDER_SCORED'))
