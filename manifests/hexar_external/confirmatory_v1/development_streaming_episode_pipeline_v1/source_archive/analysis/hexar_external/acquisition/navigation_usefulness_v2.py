"""Equal public/reference candidate policy; preserves all earlier run sources."""
import copy
from .navigation_references import build as previous_reference
from ..confirmatory_v1.motion_usefulness import PUBLIC_REQUIREMENT


def public_packet(packet):
    if packet.get('schema')!='hexar-simulated-navigation-development-packet/v1':
        raise ValueError('development navigation packet required')
    result=copy.deepcopy(packet)
    result['public_communication_requirements']['useful_motion']=PUBLIC_REQUIREMENT
    return result


def reference(packet):
    result=previous_reference(packet)
    for unit in result['required_units']:
        if unit['unit_id']=='recorded_odometry_observation':
            unit['requirement']=PUBLIC_REQUIREMENT
            unit['numeric_usefulness_policy']='hexar-motion-usefulness-candidate/v1'
            unit['maximum_expressed_resolution_or_range_width_m']='0.1'
    result['schema']='hexar-navigation-development-reference/v2'
    result['numeric_tolerance_frozen']=False
    result['numeric_policy_candidate_bound']=True
    return result
