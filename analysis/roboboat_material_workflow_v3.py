"""Prospective development bridge; reuses capture, inventory and annotation contracts.

No provider calls, old-bank rescoring, population selection or inference activation.
"""
import copy
from adjudicate_evidence_calibration_annotations import _values, _item_id
from evidence_calibration_io import canonical_sha256
from roboboat_reviewed_annotation_packet import build_reviewed_packet, validate_review_provenance
from roboboat_material_endpoint_v1 import required_units, LIMITS
from roboboat_material_endpoint_v2 import MATERIAL_LIMIT, score_development
from roboboat_material_qualification_validation_v3 import validate
from roboboat_temporal_certificate_v2 import certificate
from reference_roboboat_temporal import calculate as independent_kinematics
from reference_roboboat_temporal_v2 import calculate as independent_reference


def answerability(evidence):
    """Independent sampled kinematic/hull answerability, never contact fabrication."""
    actual = certificate(evidence)
    reference = independent_reference(evidence)
    if actual['sampled_task_support'] != reference['sampled_task_support']:
        raise ValueError('independent task reference mismatch')
    rows = evidence.get('post_result', [])
    isolated = copy.deepcopy(evidence)
    # Evaluator-only synthetic completeness isolates kinematics in the existing
    # independent reference. It never replaces method/judge evidence or contact.
    if rows:
        isolated['contacts'] = {'complete': True, 'clock': evidence['task']['clock'],
            'coverage': [rows[0]['simSeconds'], rows[-1]['simSeconds']], 'samples': []}
    independent = bool(rows) and independent_kinematics(isolated)['sampled_task_support'] == 'true'
    production = actual['coverage']['complete_sampled_window'] and all(
        actual['component_support'][key] == 'true' for key in ('position', 'heading', 'speed', 'yaw_rate', 'hull'))
    if independent != production:
        raise ValueError('independent partial-answerability mismatch')
    return independent, reference


def prepare(evidence, answer, review, extraction_returns):
    """Require exact two-pass inventory provenance before building blind forms."""
    validate_review_provenance(answer, review, extraction_returns)
    partial, reference = answerability(evidence)
    packet = build_reviewed_packet(evidence, answer, reference, review)
    for form in packet['forms']:
        form['required_unit_coverage'] = [{'unit_prompt': unit, 'communicated': None, 'response_span': None}
                                        for unit in required_units(partial)]
        form['limitation_preservation'] = [{'limitation_prompt': limit, 'preserved': None, 'response_span': None}
                                          for limit in LIMITS + (MATERIAL_LIMIT,)]
    # Distinct identity for the new prompt/score inventory; primitive recording
    # identity and evidence remain unchanged, including genuinely missing contact.
    identity = canonical_sha256({'namespace': 'marine-material-workflow-v3',
                                 'packet': packet})[:24]
    for form in packet['forms']:
        form['packet_id'] = identity
        form['form_id'] = identity + '-' + form['annotator_slot']
    packet['endpoint_status'] = 'PROSPECTIVE_DEVELOPMENT_ONLY_NO_INFERENCE'
    return packet, {'partial_information_answerable': partial,
                    'independent_reference': reference, 'configuration_n_added': 0}


def score(packet, decisions, *, activation=None):
    if activation is not None:
        raise ValueError('coordinator activation and full protocol freeze remain absent')
    forms = packet['forms']
    if len(forms) != 2 or {f['annotator_slot'] for f in forms} != {'A', 'B'}:
        raise ValueError('two distinct registered passes required')
    first = forms[0]
    for form in forms[1:]:
        for key in ('robot_visible_evidence', 'atomic_statements', 'required_unit_coverage', 'limitation_preservation'):
            if form[key] != first[key]:
                raise ValueError('unequal evidence or decision inventories across passes')
    partial, _ = answerability(first['robot_visible_evidence'])
    expected_claims = {'claim:' + atom['item_id'] for atom in first['atomic_statements']}
    actual_claims = {key for key in decisions if key.startswith('claim:')}
    if not expected_claims or expected_claims != actual_claims:
        raise ValueError('every reviewed claim must have a decision or explicit unknown')
    expected = expected_claims | {'unit:' + _item_id('u-', row['unit_prompt']) for row in first['required_unit_coverage']} | {'limitation:' + _item_id('l-', row['limitation_prompt']) for row in first['limitation_preservation']}
    if set(decisions) != expected:
        raise ValueError('decisions must match the exact declared form inventory')
    return score_development(decisions, partial_answerable=partial)


def score_return(packet, returned):
    """Validate actual bound form/hash/source spans before mapping its decisions."""
    validate(packet, returned, packet['response_text'])
    values = {key: value for key, value in _values(returned).items()
              if key.startswith(('claim:', 'unit:', 'limitation:'))}
    return score(packet, values)


def paired_cluster(cluster_id, recording_valid, questions):
    """Fixed paired-variant/L0–L2 score; unresolved answers remain adverse bounds."""
    from roboboat_cluster_analysis import score_cluster
    rows = []
    for question in questions:
        row = {'question_id': question['question_id']}
        for method in ('B2', 'B4'):
            result = question[method]
            if result['schema'] != 'roboboat-material-endpoint/v2-development' or result['inferential_activation_authorized']:
                raise ValueError('bound development endpoint result required')
            bound = result['proposed_primary_success_bounds']
            if bound not in ([0, 0], [0, 1], [1, 1]):
                raise ValueError('invalid conditional answer bound')
            row[method] = bool(bound[0]) if bound[0] == bound[1] else None
        rows.append(row)
    result = score_cluster({'cluster_id': cluster_id, 'recording_valid': recording_valid, 'questions': rows})
    return {**result, 'inferential_activation_authorized': False,
            'bounds_are_confidence_intervals': False, 'alpha_consumed': 0}
