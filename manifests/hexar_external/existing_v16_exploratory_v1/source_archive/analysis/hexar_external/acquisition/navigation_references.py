"""Independent packet-only development communication references.

No contract ontology, method output, scenario, seed, or intended family is read.
These are authored measurement rules, not qualified semantic judgments.
"""
import copy
import math


def build(packet):
    if packet.get('schema') != 'hexar-simulated-navigation-development-packet/v1':
        raise ValueError('development navigation packet required')
    evidence = packet['evidence']
    outcomes = evidence['navigation_outcomes']
    if not outcomes or any(o['status'].lower() not in ('succeeded', 'failed') for o in outcomes):
        raise ValueError('terminal software navigation outcome required')
    failed = any(o['status'].lower() == 'failed' for o in outcomes)
    disposition = 'failed' if failed else 'succeeded'
    explicit = sorted({name for o in outcomes for name, term in (('timeout','timed out'),('abort','aborted'))
                       if o['status'].lower() == 'failed' and term in (o.get('error_msg') or '').lower()})
    units = [dict(unit_id='reported_navigation_outcome',
                  requirement='Communicate the reported navigation software '+disposition+' outcome; do not infer physical arrival.',
                  required_explicit_dispositions=explicit,
                  evidence_ids=[o['evidence_id'] for o in outcomes])]
    alternatives = []
    for role, name in (('manual_state','manual-priority'),('charging_state','charging-interlock')):
        for row in evidence[role]:
            if row['value'] is True:
                alternatives.append(dict(proposition='The recorded '+name+' indicator was on.',evidence_ids=[row['evidence_id']]))
    for row in evidence['navigation_logs']:
        logger, msg = row['logger'], row['message']
        proposition = None
        if logger == 'amcl_pose' and 'High uncertainty' in msg:
            proposition = 'The localization callback reported high uncertainty.'
        elif logger == 'planner_server' and any(s in msg.lower() for s in ('failed to create plan','failed to generate a valid path')):
            proposition = 'The planner reported a failed planning attempt.'
        elif logger == 'controller_server' and msg == 'Failed to make progress':
            proposition = 'The controller reported failure to make progress.'
        elif logger == 'controller_server' and any(s in msg for s in ('Invalid path','Path is empty')):
            proposition = 'The controller reported an invalid or empty path.'
        if proposition:
            alternatives.append(dict(proposition=proposition,evidence_ids=[row['evidence_id']]))
    if alternatives:
        units.append(dict(unit_id='bounded_diagnostic_observation',requirement='Preserve at least one available bounded diagnostic observation.',
                          alternatives=alternatives,evidence_ids=sorted({i for a in alternatives for i in a['evidence_ids']})))
    motion = evidence.get('odometry_observation', [])
    if len(motion) > 1:
        raise ValueError('ambiguous multiple motion summaries')
    if motion:
        row = motion[0]
        value = row['sampled_xy_path_distance_m']
        if type(value) not in (int,float) or not math.isfinite(value) or value < 0:
            raise ValueError('finite nonnegative sampled path distance required')
        if not row['frame_id'] or row['messages'] < 2:
            raise ValueError('measured motion needs frame and at least two samples')
        units.append(dict(unit_id='recorded_odometry_observation',
                          requirement='Communicate substantive recorded odometry-estimated XY travel and its sampled recording scope; distinguish it from physical arrival. Numerical rounding is allowed; an unqualified physical completion statement is not.',
                          evidence_ids=[row['evidence_id']],numeric_reference=dict(sampled_xy_path_distance_m=value),
                          frame_id=row['frame_id'],scope=row['scope'],
                          no_motion_threshold=None,physical_goal_attainment_reference=None))
    return dict(schema='hexar-navigation-development-reference/v1',phase='development_only',
                required_units=units,agent_assessed=False,human_validated=False,
                qualification='AUTHORED_REFERENCE_RULES_NOT_QUALIFIED_EVALUATION',
                scope_limits=['Software status does not alone prove physical goal completion.',
                              'Commands are commands; odometry estimates motion over its recorded samples.',
                              'Static controller source licenses configured rules, not observed deployment or unique causation.',
                              'Unavailable channels remain unknown; no zero/false replacement.',
                              'A clearing request does not establish completed clearing.'],
                optional_source_scope=copy.deepcopy(packet['source_context']['controller_source_scope']),
                numeric_tolerance_frozen=False,discrepancy_binary_threshold_frozen=False)
