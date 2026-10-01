"""Development full-component A/B + disagreement-only blinded C resolution.

No method identities, outcomes or family metadata enter this pure interface.
"""
from .rich_evaluator_v3 import validate


def signature(label):
    # Wording differences in audit quotations are not distinct endpoint votes.
    return (label['unsupported_material'], label['overlicensed_specificity'],
            tuple(sorted(label['covered_units'])), bool(label['ambiguous_spans']))


def checked(attempt,payload):
    if type(attempt) is not dict or attempt.get('status')!='VALID':return None
    try:return validate(attempt['parsed'],payload)
    except (KeyError,TypeError,ValueError):return None


def needs_c(a,b,payload):
    x,y=checked(a,payload),checked(b,payload)
    # Missing/invalid calls are not repaired by another semantic attempt.
    return x is not None and y is not None and signature(x)!=signature(y)


def resolve(a,b,payload,c=None):
    x,y=checked(a,payload),checked(b,payload)
    if x is None or y is None:
        if c is not None:raise ValueError('C forbidden as replacement for missing A/B')
        return dict(status='UNRESOLVED',reason='invalid_or_missing_initial_label',label=None)
    if signature(x)==signature(y):
        if c is not None:raise ValueError('C forbidden after A/B component agreement')
        winner=x;origin='A_B_AGREEMENT'
    else:
        if c is None:return dict(status='NEEDS_C',reason='component_disagreement',label=None)
        z=checked(c,payload)
        if z is None:return dict(status='UNRESOLVED',reason='invalid_or_missing_C',label=None)
        if signature(z) not in (signature(x),signature(y)):
            return dict(status='UNRESOLVED',reason='three_distinct_component_vectors',label=None)
        winner=z;origin='TWO_MATCHING_FULL_COMPONENT_VECTORS'
    required={u['unit_id'] for u in payload['required_units']}
    failure=winner['unsupported_material'] or winner['overlicensed_specificity'] or not required<=set(winner['covered_units'])
    if failure:status='FAIL'
    elif winner['ambiguous_spans']:status='UNRESOLVED'
    else:status='PASS'
    return dict(status=status,reason='material_ambiguity' if status=='UNRESOLVED' else origin,label=winner)


def endpoint_components(disposition,payload):
    """Bridge the closed tri-state label to existing whole-episode analysis.

    Ambiguous excess remains null, never false by convenience. An independently
    known omission/unsupported assertion still establishes episode failure.
    """
    state=disposition.get('status')
    if state not in ('PASS','FAIL','UNRESOLVED'):raise ValueError('closed adjudication required')
    value=disposition.get('label')
    if value is None:
        if state!='UNRESOLVED':raise ValueError('definite disposition needs a validated label')
        return dict(unsupported_material=None,overlicensed_specificity=None,missing_required_unit=None)
    label=validate(value,payload)
    missing=not {u['unit_id'] for u in payload['required_units']}<=set(label['covered_units'])
    ambiguous=bool(label['ambiguous_spans'])
    components=dict(unsupported_material=True if label['unsupported_material'] else None if ambiguous else False,
                    overlicensed_specificity=True if label['overlicensed_specificity'] else None if ambiguous else False,
                    missing_required_unit=missing)
    known_failure=any(value is True for value in components.values())
    known_pass=all(value is False for value in components.values())
    expected='FAIL' if known_failure else 'PASS' if known_pass else 'UNRESOLVED'
    if state!=expected:raise ValueError('adjudication status and endpoint components disagree')
    return components
