"""Development judge projection of real packets, without method/admin labels.

All legitimate packet evidence remains visible. This is projection engineering,
not a qualified scoring instrument or provider executor.
"""
import copy

from .development_rich_evaluator_bank import UNITS
from .blind_bank import FORBIDDEN_METADATA

PACKET_KEYS={'schema','question','task_window','evidence','availability','diagnostic_channels',
             'source_context','public_communication_requirements'}
ROLES={'navigation_logs','navigation_outcomes','manual_state','charging_state','recorded_task',
       'odometry_observation','command_observation','requested_goal','action_status_observation','observed_action_window'}
SOURCE_KEYS={'indicator_semantics','localization_semantics','event_scope','timing_scope','missingness',
             'controller_configuration','controller_runtime_observations','controller_source_scope','navigation_task_scope','outcome_measurement_scope','motion_window_scope'}
ADMIN_KEYS={'method','method_identity','family','family_hidden','seed','seed_hidden','expected','expected_winner',
            'prior_label','prior_labels','development_result','alpha_outcome','gold','sampling_hidden','eligible_for_confirmation'} | FORBIDDEN_METADATA


def reject_administrative(value):
    if isinstance(value,dict):
        if set(value)&ADMIN_KEYS:raise ValueError('nested administrative metadata in blind evidence')
        for child in value.values():reject_administrative(child)
    elif isinstance(value,list):
        for child in value:reject_administrative(child)


def project(packet,reference,answer):
    if set(packet)!=PACKET_KEYS or packet['schema']!='hexar-simulated-navigation-development-packet/v1':
        raise ValueError('known real development packet required')
    if set(packet['evidence'])!=ROLES or not set(packet['source_context'])<=SOURCE_KEYS:
        raise ValueError('unknown evidence role or source scope')
    reject_administrative(packet)
    if type(answer) is not str or not answer.strip():
        raise ValueError('raw nonempty answer required')
    units=[];seen=set()
    for row in reference['required_units']:
        uid=row['unit_id']
        if uid not in UNITS or uid in seen:raise ValueError('unknown or duplicate useful unit')
        seen.add(uid);requirement=row['requirement']
        if type(requirement) is not str:raise ValueError('textual requirement required')
        dispositions=row.get('required_explicit_dispositions',[])
        if any(x not in ('timeout','abort') for x in dispositions):raise ValueError('unknown required disposition')
        if dispositions:requirement+=' Preserve explicitly recorded '+', '.join(dispositions)+'.'
        units.append(dict(unit_id=uid,requirement=requirement))
    # Retain actual queried evidence/context verbatim, including possible
    # untrusted log text. Do not include a method's trace, author labels or the
    # reference inventory's proposed numeric/cause conclusions.
    evidence=copy.deepcopy({k:packet[k] for k in ('task_window','evidence','availability','diagnostic_channels',
                                                'source_context','public_communication_requirements')})
    return dict(question=packet['question'],visible_evidence=evidence,required_units=units,answer=answer)
