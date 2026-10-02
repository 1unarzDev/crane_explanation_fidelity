"""Unpromoted marine v2: direct whole-answer materiality plus required units.

Reuse current qualified annotation decision keys. No new atom classifier,
automatic textual relevance mask, or retrospective old-bank rescore.
"""
from adjudicate_evidence_calibration_annotations import _item_id
from roboboat_material_endpoint_v1 import UNITS,PARTIAL_UNIT,LIMITS,SUPPORTED,LABELS

MATERIAL_LIMIT = (
    'Across the whole answer, avoid material unsupported assertions. Material means an unsupported action/task outcome, '
    'a misleading decisive measurement or interval witness, a governing requirement/configuration error used to explain completion, '
    'an incorrect evidence/temporal/completeness limit, or an episode-specific physical cause offered as an explanation (including endorsed hedges). '
    'A disclaimer does not cancel a contrary assertion. A supported supplemental fact is allowed. '
    'An unendorsed hypothetical or a statement that causation is not established is not cause attribution. '
    'A minor supplemental numerical/reference discrepancy is not material only when it changes none of the supported outcome, '
    'decisive compliance/witness, governing requirements, required task interval/completeness interpretation or causal claim; '
    'it must remain in all-assertion and quantitative/temporal error reporting. '
    'Magnitude alone does not excuse a near-threshold error that changes a condition or witness. '
    'If material impact is unresolved, do not mark this limitation preserved.'
)


def score_development(decisions, *, partial_answerable, activation=None):
    if activation is not None:raise ValueError('material-primary qualification/activation is not established')
    if type(partial_answerable) is not bool:raise ValueError('independent partial-answerability required')
    claims={k:v for k,v in decisions.items() if k.startswith('claim:')}
    units={k:v for k,v in decisions.items() if k.startswith('unit:')}
    limits={k:v for k,v in decisions.items() if k.startswith('limitation:')}
    unit_keys={'unit:'+_item_id('u-',u) for u in UNITS+((PARTIAL_UNIT,) if partial_answerable else ())}
    limit_keys={'limitation:'+_item_id('l-',l) for l in LIMITS+(MATERIAL_LIMIT,)}
    if not claims or set(units)!=unit_keys or set(limits)!=limit_keys:raise ValueError('complete declared atom/unit/whole-answer judgment inventory required')
    if any(v is not None and v not in LABELS for v in claims.values()):raise ValueError('undeclared claim label')
    if any(v is not None and type(v) is not bool for v in [*units.values(),*limits.values()]):raise ValueError('explicit boolean or unavailable judgment required')
    necessary=[*units.values(),*limits.values()]
    primary_bounds=[0,0] if False in necessary else [0,1] if None in necessary else [1,1]
    strict_bad=any(v is not None and v!=SUPPORTED for v in claims.values())
    strict_unknown=any(v is None for v in claims.values())
    strict_bounds=[0,0] if strict_bad or False in necessary else [0,1] if strict_unknown or None in necessary else [1,1]
    # Missing atomic support cannot be discarded while claiming success even if
    # the whole-answer materiality field was supplied. Keep adverse bounds.
    if any(v is None for v in claims.values()) and primary_bounds==[1,1]:primary_bounds=[0,1]
    return {'schema':'roboboat-material-endpoint/v2-development','proposed_primary_success_bounds':primary_bounds,
            'strict_all_assertion_success_bounds':strict_bounds,
            'unsupported_atomic_decisions':{k:v for k,v in claims.items() if v not in (SUPPORTED,None)},
            'unavailable_atomic_decisions':[k for k,v in claims.items() if v is None],
            'materiality_field':limits['limitation:'+_item_id('l-',MATERIAL_LIMIT)],
            'endpoint_semantically_qualified':False,'inferential_activation_authorized':False,
            'bounds_are_confidence_intervals':False,'new_configuration_n':0,'alpha_consumed':0}
