"""Additive explicit-contact-policy successor; frozen v1 remains untouched.

Reuse checked v1 kinematics only. Contact support is computed here from an
aligned, declared prohibited-contact event stream, never from silence alone.
"""
import copy
import re
from roboboat_temporal_certificate import (
    audit_ladder as audit_v1, certificate as certificate_v1,
    validate_packet as validate_v1, number,
)
from roboboat_temporal_renderer_v4 import render_v4

POLICY = {
    'requirement': 'absence-of-prohibited-contact',
    'prohibited_contacts': 'any-hull-contact-with-external-objects',
    'interval': 'declared-dwell',
    'count_semantics': 'observed-prohibited-contact-events',
    'absence_support': 'aligned-complete-prohibited-contact-event-stream',
}


def _legacy(packet):
    p = copy.deepcopy(packet)
    p['schema'] = 'roboboat-evidence-packet/v1'
    p['task'].pop('contact_policy')
    p['task']['schema'] = 'roboboat-terminal-task/v1'
    p['task']['contact_required'] = True
    p.pop('contacts', None)
    return p


def validate_packet(packet):
    if packet.get('schema') != 'roboboat-evidence-packet/v2':
        raise ValueError('expected v2 packet identity')
    task = packet['task']
    if task.get('schema') != 'roboboat-terminal-task/v2' or 'contact_required' in task:
        raise ValueError('expected explicit v2 task')
    if task.get('contact_policy') != POLICY:
        raise ValueError('unsupported contact policy')
    validate_v1(_legacy(packet))
    contact = packet.get('contacts')
    if contact is None:
        return
    if set(contact) != {'clock', 'coverage', 'complete', 'sensor_identity', 'completeness_basis', 'samples'}:
        raise ValueError('contact fields incomplete or metadata leak')
    if type(contact['complete']) is not bool:
        raise ValueError('contact completeness must be boolean')
    if not isinstance(contact['clock'], str) or not contact['clock']:
        raise ValueError('missing contact clock')
    if not isinstance(contact['sensor_identity'], str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', contact['sensor_identity']):
        raise ValueError('expected opaque sensor identity')
    basis = contact['completeness_basis']
    if basis not in ('complete-prohibited-contact-event-stream', 'no-completeness-guarantee'):
        raise ValueError('unsupported completeness basis')
    if contact['complete'] and basis != 'complete-prohibited-contact-event-stream':
        raise ValueError('absence requires event-stream completeness guarantee')
    coverage = contact['coverage']
    if not isinstance(coverage, list) or len(coverage) != 2:
        raise ValueError('invalid contact coverage')
    lo, hi = map(number, coverage)
    if hi < lo:
        raise ValueError('reversed contact coverage')
    previous = None
    if not isinstance(contact['samples'], list):
        raise ValueError('invalid contact samples')
    for row in contact['samples']:
        if set(row) != {'time_s', 'count'}:
            raise ValueError('contact sample metadata leak')
        time = number(row['time_s'])
        if type(row['count']) is not int or row['count'] < 0:
            raise ValueError('invalid prohibited-contact count')
        if not lo <= time <= hi or (previous is not None and time <= previous):
            raise ValueError('contact observation outside coverage or nonmonotone')
        previous = time


def upgrade_development_packet(packet, packet_id, task):
    """Explicitly reissue inspected evidence; never overwrite an old identity."""
    if packet_id == packet['packet_id'] or task['id'] == packet['task']['id']:
        raise ValueError('successor requires distinct packet/task identities')
    old_requirements = {k: v for k, v in packet['task'].items() if k not in ('schema', 'id', 'contact_required')}
    new_requirements = {k: v for k, v in task.items() if k not in ('schema', 'id', 'contact_policy')}
    if old_requirements != new_requirements:
        raise ValueError('contact repair must preserve all non-contact task requirements')
    if 'contacts' in packet:
        raise ValueError('legacy contact evidence requires explicit provenance conversion')
    p = copy.deepcopy(packet)
    p.update(schema='roboboat-evidence-packet/v2', packet_id=packet_id, task=copy.deepcopy(task))
    validate_packet(p)
    return p


def audit_ladder(levels):
    for packet in levels:
        validate_packet(packet)
    if any('contacts' in p for p in levels):
        raise ValueError('contact observations belong to separately declared L3, not L0–L2')
    return audit_v1(levels)


def certificate(packet):
    validate_packet(packet)
    cert = certificate_v1(_legacy(packet))
    cert['schema'] = 'roboboat-temporal-certificate/v2'
    cert['task_identity'] = packet['task']['id']
    start, end = cert['interval_s']
    contact = packet.get('contacts')
    state, reason, hits = 'unknown', 'contact-evidence-unavailable', []
    if contact is not None:
        if start is None:
            reason = 'declared-dwell-unanchored'
        elif contact['clock'] != packet['task']['clock']:
            reason = 'contact-clock-unaligned'
        else:
            hits = [r for r in contact['samples'] if start <= r['time_s'] <= end and r['count'] > 0]
            if hits:
                state, reason = 'false', 'observed-prohibited-contact-in-dwell'
                cert['witnesses']['contact'] = copy.deepcopy(hits[0])
            elif (contact['complete'] and contact['coverage'][0] <= start
                  and contact['coverage'][1] >= end):
                state, reason = 'true', 'aligned-complete-event-stream-covers-dwell'
            else:
                reason = 'contact-absence-not-established'
    cert['component_support']['contact'] = state
    cert['contact_evidence'] = {
        'support': state, 'reason': reason, 'interval_s': [start, end],
        'policy': copy.deepcopy(POLICY),
        'sensor_identity': contact['sensor_identity'] if contact else None,
        'coverage_s': contact['coverage'] if contact else None,
        'clock': contact['clock'] if contact else None,
        'completeness_basis': contact['completeness_basis'] if contact else None,
        'violation_events': copy.deepcopy(hits),
    }
    states = cert['component_support'].values()
    result = 'false' if 'false' in states else 'true' if all(s == 'true' for s in states) else 'unknown'
    cert['sampled_task_support'] = result
    cert['continuous_task_support'] = 'false' if result == 'false' else 'unknown'
    cert['unavailable'] = [k for k, v in cert['component_support'].items() if v == 'unknown']
    return cert


def render(packet, cert):
    answer = render_v4(packet, cert)
    state = cert['component_support']['contact']
    if state == 'unknown':
        answer += ' The task requires no prohibited hull contact during that dwell; the contact evidence does not establish whether this requirement held.'
    elif state == 'true':
        if cert['sampled_task_support'] == 'true':
            start, end = cert['interval_s']
            answer += (f" The {cert['coverage']['sample_count']} kinematic/hull samples span the declared "
                       f"{start:.6f}–{end:.6f} s dwell with maximum gap {cert['coverage']['max_gap_s']:.4f} s.")
        answer += ' An aligned complete prohibited-contact event stream covering the declared dwell establishes contact absence under the stated capture guarantee.'
    return answer
