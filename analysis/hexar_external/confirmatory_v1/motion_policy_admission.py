"""Fail-closed confirmation admission of equal numeric-usefulness requirements."""
import hashlib
import json
from .motion_usefulness import PUBLIC_REQUIREMENT
from .unique_admission import _pinned

MANIFESTS=('battery.json','endpoint.json','comparator_freeze.json')
BINDINGS=('implementation','public_reference_interface','evaluator','scientific_source')
CHECKS=('equal_public_reference_requirements','equal_method_packet_bytes',
        'baseline_explicit_public_requirements','masked_motion_not_required',
        'fine_approximation_and_narrow_bounds','supported_coarse_values_fail_coverage',
        'literal_exactness_distinguished','source_window_scope_preserved',
        'no_physical_no_motion_threshold','whole_episode_alias_and_missingness_policy')


def admission_errors(docs,root):
    policies=[docs.get(name,{}).get('motion_usefulness_policy') for name in MANIFESTS]
    if any(type(p) is not dict for p in policies):
        return ['motion usefulness: complete policy required in battery, endpoint and comparator']
    errors=[];policy=policies[0]
    if any(p!=policy for p in policies[1:]):
        errors.append('motion usefulness: public method and endpoint policies differ')
    if (policy.get('status')!='READY_FOR_FREEZE' or policy.get('whole_endpoint_qualified') is not True
            or policy.get('maximum_resolution_or_range_width_m')!='0.1'
            or policy.get('physical_no_motion_threshold') is not None
            or 'physical_no_motion_threshold' not in policy
            or policy.get('public_requirement_sha256')!=hashlib.sha256(PUBLIC_REQUIREMENT.encode()).hexdigest()):
        errors.append('motion usefulness: complete qualified prospective policy missing/changed')
    pins={}
    for name in BINDINGS:
        try:
            pins[name]=policy[name];_pinned(root,pins[name])
        except (OSError,KeyError,TypeError,ValueError) as exc:
            errors.append('motion usefulness: invalid '+name+': '+str(exc))
    try:
        value=json.loads(_pinned(root,policy['qualification']).read_text())
        if type(value) is not dict:
            raise ValueError('qualification object required')
        if (value.get('schema')!='hexar-motion-policy-qualification/v1'
                or value.get('status')!='QUALIFIED' or value.get('bindings')!=pins
                or type(value.get('confirmatory_outputs_generated')) is not int
                or value['confirmatory_outputs_generated']!=0):
            raise ValueError('terminal preconfirmation qualification must bind the adopted implementations')
        checks=value.get('checks',{})
        if set(checks)!=set(CHECKS) or any(checks[k] is not True for k in CHECKS):
            raise ValueError('all declared equal-interface and endpoint checks required')
        if not isinstance(value.get('evidence'),dict) or set(value['evidence'])!=set(CHECKS):
            raise ValueError('hash-bound evidence for each qualification check required')
        for evidence in value['evidence'].values():_pinned(root,evidence)
    except (OSError,KeyError,TypeError,ValueError) as exc:
        errors.append('motion usefulness: qualification missing/invalid: '+str(exc))
    return errors
