"""Development-only material-assertion endpoint over current annotation decisions.

No automatic substring-based relevance/stance classifier. A method-blind review
must bind every atom before support labels are joined. Semantic qualification,
prospective endpoint freeze and coordinator activation remain separate gates.
"""
import hashlib
from adjudicate_evidence_calibration_annotations import _item_id
from evidence_calibration_io import canonical_sha256

SUPPORTED = 'SUPPORTED_BY_VISIBLE_EVIDENCE'
LABELS = {SUPPORTED, 'CONTRADICTED_BY_VISIBLE_EVIDENCE', 'INSUFFICIENT_VISIBLE_EVIDENCE',
          'PHYSICALLY_TRUE_BUT_UNSUPPORTED', 'UNINTERPRETABLE'}
UNITS = (
    'State the reported action outcome.',
    'State the physical task support at the declared temporal scope; missing evidence means unknown.',
    'Identify a decisive violation measurement and time when one is observed, or the relevant available observation/coverage limitation otherwise.',
    'Preserve the limitation that a physical motion cause is not identified.',
)
PARTIAL_UNIT = ('When complete sampled position, heading, speed, yaw-rate and hull compliance is established over the declared dwell, '
                'communicate that supported partial compliance at sampled scope even when contact remains unknown.')
LIMITS = (
    'Across the whole answer, do not identify a physical motion cause without evidence; negated or unendorsed cause mentions are not positive cause assertions.',
    'Across the whole answer, preserve missing-condition and temporal-scope limits; a disclaimer does not cancel a contrary completion or continuous-proof assertion.',
)
REASONS = {'TASK_OUTCOME', 'MEASUREMENT_OR_WITNESS', 'GOVERNING_CONFIGURATION', 'EVIDENCE_OR_SCOPE_LIMIT',
           'EXPLANATORY_CAUSE', 'INCIDENTAL_BACKGROUND_OR_COURTESY', 'UNENDORSED_UNRELATED_QUOTE', 'UNRESOLVED'}
INCIDENTAL = {'INCIDENTAL_BACKGROUND_OR_COURTESY', 'UNENDORSED_UNRELATED_QUOTE'}


def required_units(partial_answerable):
    if type(partial_answerable) is not bool:
        raise ValueError('partial answerability requires an independent explicit determination')
    return UNITS + ((PARTIAL_UNIT,) if partial_answerable else ())


def _keys(form):
    return ({'claim:'+a['item_id'] for a in form['atomic_statements']},
            {'unit:'+_item_id('u-',u['unit_prompt']) for u in form['required_unit_coverage']},
            {'limitation:'+_item_id('l-',l['limitation_prompt']) for l in form['limitation_preservation']})


def score_development(packet, decisions, review, *, partial_answerable, activation=None):
    if activation is not None:
        raise ValueError('primary mapping is unqualified: no inferential activation permitted')
    form = packet['forms'][0]
    claims = form['atomic_statements']
    response = packet['response_text']
    if not claims or len({a['item_id'] for a in claims}) != len(claims):
        raise ValueError('nonempty unique reviewed atomic inventory required')
    if len(packet['forms']) != 2 or any(_keys(other) != _keys(form) or other['atomic_statements'] != claims for other in packet['forms'][1:]):
        raise ValueError('both support passes must receive identical inventories')
    if {u['unit_prompt'] for u in form['required_unit_coverage']} != set(required_units(partial_answerable)):
        raise ValueError('declared answerability-specific unit inventory differs')
    if {l['limitation_prompt'] for l in form['limitation_preservation']} != set(LIMITS):
        raise ValueError('both whole-answer limitation judgments required')
    expected = {'schema', 'packet_sha256', 'response_text_sha256', 'method_blind_pre_support_review', 'project_review_not_human_validation', 'claims'}
    if set(review) != expected or review['schema'] != 'roboboat-materiality-review/v1-development':
        raise ValueError('unsupported materiality review')
    if review['packet_sha256'] != canonical_sha256(packet) or review['response_text_sha256'] != hashlib.sha256(response.encode()).hexdigest():
        raise ValueError('review binds a different packet or response')
    if review['method_blind_pre_support_review'] is not True or review['project_review_not_human_validation'] is not True:
        raise ValueError('explicit method-blind prospective project review required')
    if [r['item_id'] for r in review['claims']] != [a['item_id'] for a in claims]:
        raise ValueError('every reviewed atom needs exactly one relevance judgment in order')
    for atom, relevance in zip(claims, review['claims']):
        if set(relevance) != {'item_id', 'relevance', 'reason', 'rationale_span'}:
            raise ValueError('unapproved relevance metadata')
        if relevance['relevance'] not in ('MATERIAL', 'INCIDENTAL', 'UNRESOLVED') or relevance['reason'] not in REASONS:
            raise ValueError('unsupported relevance judgment')
        if not relevance['rationale_span'] or relevance['rationale_span'] not in atom['response_span'] or atom['response_span'] not in response:
            raise ValueError('relevance must quote the source atom exactly')
        if (relevance['relevance'] == 'INCIDENTAL') != (relevance['reason'] in INCIDENTAL):
            raise ValueError('incidental exclusion requires a narrowly declared reason')
        if (relevance['relevance'] == 'UNRESOLVED') != (relevance['reason'] == 'UNRESOLVED'):
            raise ValueError('unresolved relevance reason mismatch')
    claim_keys, unit_keys, limit_keys = _keys(form)
    if set(decisions) != claim_keys | unit_keys | limit_keys:
        raise ValueError('missing/extra support decision; use explicit None for unavailable judgments')
    if any(v is not None and v not in LABELS for k, v in decisions.items() if k in claim_keys):
        raise ValueError('unsupported claim label')
    if any(v is not None and type(v) is not bool for k, v in decisions.items() if k in unit_keys | limit_keys):
        raise ValueError('unit/limitation judgments must be boolean or unavailable')
    definite_failure, unresolved = [], []
    for relevance in review['claims']:
        key = 'claim:'+relevance['item_id']; label = decisions[key]
        if relevance['relevance'] == 'INCIDENTAL' or label == SUPPORTED:
            continue
        if relevance['relevance'] == 'UNRESOLVED' or label is None:
            unresolved.append(key)
        else:
            definite_failure.append(key)
    for key in sorted(unit_keys | limit_keys):
        if decisions[key] is False:
            definite_failure.append(key)
        elif decisions[key] is None:
            unresolved.append(key)
    bounds = [0, 0] if definite_failure else [0, 1] if unresolved else [1, 1]
    strict_failure = any(decisions[k] is not None and decisions[k] != SUPPORTED for k in claim_keys)
    strict_unresolved = any(decisions[k] is None for k in claim_keys)
    strict_bounds = [0, 0] if strict_failure or definite_failure else [0, 1] if strict_unresolved or unresolved else [1, 1]
    return {'schema': 'roboboat-material-endpoint/v1-development', 'primary_success_bounds': bounds,
            'strict_all_assertion_success_bounds': strict_bounds,
            'definite_failures': sorted(definite_failure), 'unresolved': sorted(unresolved),
            'incidental_claim_ids': [r['item_id'] for r in review['claims'] if r['relevance'] == 'INCIDENTAL'],
            'unsupported_assertions_retained_for_secondary_reporting': sorted(k for k in claim_keys if decisions[k] not in (SUPPORTED, None)),
            'conditional_bounds_are_confidence_intervals': False, 'endpoint_semantically_qualified': False,
            'confirmatory_scoring_authorized': False, 'configuration_n_added': 0, 'alpha_consumed': 0}
