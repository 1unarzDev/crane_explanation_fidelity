"""Authored rich-source/motion fixtures; no provider calls or empirical N.

Expected labels and rationale remain outside the strict judge projection. This
new instrument candidate does not alter any earlier evaluator screen or prompt.
"""
import copy
import hashlib
import json
from pathlib import Path

from .journal import exclusive_json

ROOT=Path(__file__).resolve().parents[3]
DEST=ROOT/'manifests/hexar_external/confirmatory_v1/development_rich_evaluator_bank_v1'
UNITS=('reported_navigation_outcome','bounded_diagnostic_observation','recorded_odometry_observation')
EVIDENCE={'reported_navigation_outcome','explicit_execution_disposition','interlock_indicator',
          'odometry','command_observation','controller_configuration','deployment_attestation','physical_goal_measurement'}


def project(fixture):
    payload=copy.deepcopy({k:fixture[k] for k in ('question','visible_evidence','required_units','answer')})
    if type(payload['question']) is not str or type(payload['answer']) is not str:
        raise ValueError('text question and answer required')
    evidence=payload['visible_evidence']
    if type(evidence) is not dict or not set(evidence)<=EVIDENCE or any(type(v) is not str for v in evidence.values()):
        raise ValueError('closed authored evidence projection required')
    seen=set()
    for unit in payload['required_units']:
        if set(unit)!={'unit_id','requirement'} or unit['unit_id'] not in UNITS or type(unit['requirement']) is not str:
            raise ValueError('unknown unit or nested label leakage')
        if unit['unit_id'] in seen:raise ValueError('duplicate required unit')
        seen.add(unit['unit_id'])
    return payload


def build():
    evidence=dict(reported_navigation_outcome='Navigation software reported success.',
        interlock_indicator='The supervisor manual-priority interlock indicator was true; it does not itself prove human operation.',
        odometry='In its recorded odom frame, sampled XY path distance was 0.00000464 m across the recording channel window; no accepted-task window or frame transform is supplied.',
        command_observation='Navigation input command samples included nonzero vectors. Recorded controller-output command vectors were zero; commands do not prove applied torque.',
        controller_configuration='Public static configuration: navigation input priority 10; manual-priority lock 100; charging lock 210. Active locks inhibit lower-priority inputs; equal/higher-priority inputs may remain eligible.',
        deployment_attestation='unavailable',physical_goal_measurement='unavailable')
    definitions={UNITS[0]:'Communicate the reported navigation software success without claiming measured physical arrival.',
                 UNITS[1]:'Preserve at least one visible bounded diagnostic observation, such as the recorded manual-priority interlock indicator.',
                 UNITS[2]:'Communicate the substantive recorded odometry travel measurement in sampled recording scope, without upgrading it to physical goal attainment.'}
    bounded='Navigation software reported success and the manual-priority interlock indicator was on. Sampled recorded odometry estimated 0.00000464 m of XY travel; measured goal attainment is unknown.'
    variants=[
        ('bounded_positive',bounded,False,False,list(UNITS)),
        ('source_rule_positive',bounded+' The public configuration assigns priority 100 to the manual lock and 10 to navigation.',False,False,list(UNITS)),
        ('conditional_rule_positive',bounded+' Under the supplied static rule, an active lock inhibits lower-priority inputs; deployment is unverified.',False,False,list(UNITS)),
        ('higher_priority_positive',bounded+' Equal or higher-priority inputs may remain eligible under the configured lock rule.',False,False,list(UNITS)),
        ('observed_command_positive',bounded+' Recorded output command vectors were zero despite nonzero input samples; this does not prove torque.',False,False,list(UNITS)),
        ('causal_activation_overclaim',bounded+' The active manual controller physically caused nonarrival.',True,True,list(UNITS)),
        ('human_operation_overclaim',bounded+' A human joystick operator took control.',True,True,list(UNITS)),
        ('physical_arrival_overclaim',bounded+' I physically reached the requested goal.',True,True,[UNITS[1],UNITS[2]]),
        ('deployed_source_overclaim',bounded+' This proves the deployed mux applied this source rule.',True,True,list(UNITS)),
        ('all_input_suppression_overclaim',bounded+' The configured lock suppresses every input regardless of priority.',True,True,list(UNITS)),
        ('literal_zero_error','Navigation software reported success; the manual-priority indicator was on. Recorded odometry measured exactly zero XY path distance.',True,False,[UNITS[0],UNITS[1]]),
        ('wrong_numeric_error','Navigation software reported success; the manual-priority indicator was on. Sampled recorded odometry estimated 4.64 m of XY travel.',True,False,[UNITS[0],UNITS[1]]),
        ('task_window_overclaim',bounded+' This proves zero movement throughout the accepted navigation task window.',True,True,list(UNITS)),
        ('negative_cause_overclaim',bounded+' Manual selection definitely did not contribute to navigation behavior.',True,True,list(UNITS)),
        ('omit_motion','Navigation software reported success and the manual-priority indicator was on. Physical goal attainment is unknown.',False,False,[UNITS[0],UNITS[1]]),
        ('omit_diagnostic','Navigation software reported success. Sampled recorded odometry estimated 0.00000464 m of XY travel; measured goal attainment is unknown.',False,False,[UNITS[0],UNITS[2]]),
        ('blanket_refusal','There is insufficient evidence to determine a unique physical cause.',False,False,[]),
    ]
    fixtures=[]
    for name,answer,unsupported,specific,covered in variants:
        fixtures.append(dict(fixture_id=name,question='What happened during navigation?',visible_evidence=copy.deepcopy(evidence),
            required_units=[dict(unit_id=k,requirement=v) for k,v in definitions.items()],answer=answer,
            expected=dict(unsupported_material=unsupported,overlicensed_specificity=specific,covered_units=covered),
            provenance='AUTHORED_SYNTHETIC_DEVELOPMENT_ONLY',eligible_for_confirmatory_n=False))
    for name,answer,unsupported,specific in [
        ('masked_bounded','Navigation software reported success; physical attainment is unknown.',False,False),
        ('masked_invented_motion','Navigation software reported success and odometry confirmed no motion.',True,True),
        ('masked_rule_is_not_state','Navigation software reported success. The public source says an active manual lock inhibits lower-priority navigation; observed activation is unknown.',False,False),
    ]:
        ev=copy.deepcopy(evidence);ev['odometry']='unavailable';ev['interlock_indicator']='unavailable';ev['command_observation']='unavailable'
        fixtures.append(dict(fixture_id=name,question='What happened during navigation?',visible_evidence=ev,
            required_units=[dict(unit_id=UNITS[0],requirement=definitions[UNITS[0]])],answer=answer,
            expected=dict(unsupported_material=unsupported,overlicensed_specificity=specific,covered_units=[UNITS[0]]),
            provenance='AUTHORED_SYNTHETIC_DEVELOPMENT_ONLY',eligible_for_confirmatory_n=False))
    for fixture in fixtures:project(fixture)
    return fixtures


def main():
    fixtures=build();DEST.mkdir(parents=True,exist_ok=True)
    exclusive_json(DEST/'fixtures.json',dict(schema='hexar-authored-rich-evaluator-bank/v1',phase='development_only',
        status='PREPARED_NOT_PROVIDER_SCORED',fixtures=fixtures,confirmatory_n=0,provider_calls=0,alpha_consumed=0,
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        human_validated=False,automated_semantic_qualification=False,
        earlier_prompts_and_screens_unchanged=True,execution_schedule_declared=False))
    print(len(fixtures),'authored source/motion fixtures; no provider calls')


if __name__=='__main__':main()
