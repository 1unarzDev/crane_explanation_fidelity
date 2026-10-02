"""Independent v2 contact reference; imports no production implementation.

Kinematics reuse the independent v1 evaluator, not the production certificate.
Inputs are validated separately by production; this reference evaluates valid
public evidence under the fixed v2 absence policy.
"""
import copy
from reference_roboboat_temporal import calculate as reference_v1


def calculate(packet):
    p = copy.deepcopy(packet)
    p.pop('contacts', None)
    kinematics = reference_v1(p)
    rows = packet.get('post_result', [])
    contact_state = 'unknown'
    if rows:
        lo = rows[0]['simSeconds']
        hi = lo + packet['task']['dwell_s']
        events = packet.get('contacts')
        if events is not None and events['clock'] == packet['task']['clock']:
            violations = [r for r in events['samples'] if lo <= r['time_s'] <= hi and r['count'] >= 1]
            if violations:
                contact_state = 'false'
            elif (events['complete'] is True
                  and events['completeness_basis'] == 'complete-prohibited-contact-event-stream'
                  and events['coverage'][0] <= lo and events['coverage'][1] >= hi):
                contact_state = 'true'
    # Independently determine whether every kinematic requirement is true by
    # supplying synthetic evaluator-only contact completeness to the independent
    # reference. This is not exported or presented as observed contact evidence.
    if rows:
        p['contacts'] = {'complete': True, 'clock': p['task']['clock'],
                         'coverage': [rows[0]['simSeconds'], rows[-1]['simSeconds']], 'samples': []}
    kinematic_state = reference_v1(p)['sampled_task_support']
    outcome = ('false' if kinematic_state == 'false' or contact_state == 'false'
               else 'true' if kinematic_state == 'true' and contact_state == 'true' else 'unknown')
    return {**kinematics, 'sampled_task_support': outcome, 'contact_support': contact_state}
