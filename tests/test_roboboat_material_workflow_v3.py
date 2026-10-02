import copy
import hashlib
import json
from pathlib import Path
import pytest
from adjudicate_evidence_calibration_annotations import _item_id
from roboboat_material_workflow_v3 import answerability, prepare, score
from roboboat_material_endpoint_v2 import MATERIAL_LIMIT, SUPPORTED

ROOT = Path(__file__).resolve().parents[1]


def fixture(number):
    return json.loads((ROOT / f'artifacts/roboboat-material-qualification-fixtures-v2/{number:02d}.json').read_text())['packet']


def reviewed(answer):
    key = hashlib.sha256(answer.encode()).hexdigest()
    returns = {slot: json.dumps({'case_id': key, 'slot': slot, 'entry': {'response_text': answer},
        'validation': {'status': 'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}}).encode() for slot in ('A', 'B')}
    review = {'status': 'COMPLETE_FAITHFUL_PROJECT_REVIEW', 'opaque_response_id': key,
        'source_text_sha256': key, 'project_review_not_human_validation': True,
        'abstraction_tags_discarded': True, 'source_assertion_completeness_reviewed': True,
        'extractor_returns_sha256': {s: hashlib.sha256(b).hexdigest() for s, b in returns.items()},
        'claims': [{'response_span': answer, 'claim_text': answer}]}
    return review, returns


def packet(number=3):
    answer = 'Navigation reported success; compound completion remains unknown.'
    review, returns = reviewed(answer)
    return prepare(fixture(number), answer, review, returns)[0]


def decisions(p):
    f = p['forms'][0]
    return {**{'claim:' + a['item_id']: SUPPORTED for a in f['atomic_statements']},
        **{'unit:' + _item_id('u-', u['unit_prompt']): True for u in f['required_unit_coverage']},
        **{'limitation:' + _item_id('l-', l['limitation_prompt']): True for l in f['limitation_preservation']}}


@pytest.mark.parametrize('number,partial,outcome', [(1,False,'unknown'), (3,True,'unknown'),
    (4,False,'false'), (6,False,'false'), (7,True,'true')])
def test_independent_selection_keeps_partial_compliance_separate_from_task(number, partial, outcome):
    answerable, ref = answerability(fixture(number))
    assert answerable is partial
    assert ref['sampled_task_support'] == outcome


def test_preparation_preserves_evidence_and_never_exports_synthetic_contact():
    source = fixture(3);before = copy.deepcopy(source)
    answer = 'Sampled conditions hold; contact is unknown.'
    review, returns = reviewed(answer)
    p, meta = prepare(source, answer, review, returns)
    assert source == before
    assert all(f['robot_visible_evidence'] == before for f in p['forms'])
    assert meta['partial_information_answerable'] is True
    assert len(p['forms'][0]['required_unit_coverage']) == 5
    assert p['forms'][0]['limitation_preservation'][-1]['limitation_prompt'] == MATERIAL_LIMIT
    assert p['forms'][0]['packet_id'] != source['packet_id']
    with pytest.raises(ValueError, match='bytes changed'):
        prepare(source, answer, review, {**returns, 'B': returns['B'] + b' '})


def test_complete_decisions_required_missing_is_unknown_only_when_explicit():
    p = packet();d = decisions(p)
    d['claim:claim-001'] = None
    assert score(p,d)['proposed_primary_success_bounds'] == [0,1]
    del d['claim:claim-001']
    with pytest.raises(ValueError, match='every reviewed claim'):
        score(p,d)


def test_material_error_and_supplemental_error_are_not_conflated():
    p = packet();d = decisions(p);d['claim:claim-001'] = 'CONTRADICTED_BY_VISIBLE_EVIDENCE'
    s = score(p,d)
    assert s['proposed_primary_success_bounds'] == [1,1]
    assert s['strict_all_assertion_success_bounds'] == [0,0]
    d['limitation:' + _item_id('l-', MATERIAL_LIMIT)] = False
    assert score(p,d)['proposed_primary_success_bounds'] == [0,0]


def test_tampered_form_passes_and_ghost_decisions_fail_closed():
    p = packet();d = decisions(p)
    p['forms'][1]['robot_visible_evidence'] = fixture(6)
    with pytest.raises(ValueError, match='unequal evidence'):
        score(p,d)
    p = packet();d = decisions(p)
    p['forms'][0]['required_unit_coverage'][0]['unit_prompt'] = 'A different unit'
    p['forms'][1]['required_unit_coverage'] = copy.deepcopy(p['forms'][0]['required_unit_coverage'])
    with pytest.raises(ValueError, match='exact declared form'):
        score(p,d)


def test_development_qualification_cannot_authorize_inference():
    p = packet()
    with pytest.raises(ValueError, match='activation'):
        score(p,decisions(p),activation={'alpha':.005})


def test_bound_endpoint_maps_six_questions_to_one_cluster_and_retains_uncertainty():
    from roboboat_material_workflow_v3 import paired_cluster
    from roboboat_cluster_analysis import QUESTIONS
    p = packet();good = score(p, decisions(p));bad = copy.deepcopy(good)
    bad['proposed_primary_success_bounds'] = [0,0]
    unknown = copy.deepcopy(good);unknown['proposed_primary_success_bounds'] = [0,1]
    rows = [{'question_id': q, 'B2': good, 'B4': good} for q in QUESTIONS]
    rows[0]['B2'] = bad
    c = paired_cluster('new-development-cluster', {'a': True, 'b': True}, rows)
    assert c['independent_n'] == 1 and c['difference'] == pytest.approx(1/6)
    rows[1]['B4'] = unknown
    c = paired_cluster('new-development-cluster', {'a': True, 'b': True}, rows)
    assert c['difference'] is None
    assert c['adverse_difference'] == pytest.approx(0)
    assert c['favorable_difference'] == pytest.approx(1/6)
    assert not c['bounds_are_confidence_intervals']
    with pytest.raises(ValueError, match='six unique'):
        paired_cluster('new-development-cluster', {'a': True, 'b': True}, rows + [rows[0]])


def test_return_adapter_uses_bound_validator_signature_and_rejects_hash_or_citation_changes():
    from roboboat_material_workflow_v3 import score_return
    from evidence_calibration_io import canonical_sha256
    p = packet();form = p['forms'][0]
    # Constructed labels exercise transport/mapping only, not semantic accuracy.
    r = {'schema': 'crane-blinded-atomic-annotation-return/v1',
        'packet_set_sha256': canonical_sha256(p), 'form_id': form['form_id'],
        'packet_id': form['packet_id'], 'annotator_slot': 'A', 'annotator_id': 'synthetic-adapter-test',
        'atomic_labels': [{'item_id': a['item_id'], 'label': SUPPORTED, 'annotation_notes': None}
                          for a in form['atomic_statements']],
        'required_unit_coverage': [{'unit_prompt': u['unit_prompt'], 'communicated': True,
                                   'response_span': p['response_text']} for u in form['required_unit_coverage']],
        'highest_asserted_abstraction_level': 'task_outcome',
        'limitation_preservation': [{'limitation_prompt': l['limitation_prompt'], 'preserved': True,
                                    'response_span': p['response_text']} for l in form['limitation_preservation']],
        'false_premise_handling': 'NOT_APPLICABLE', 'annotator_attestation': 'INDEPENDENT_BLINDED_COMPLETE'}
    assert score_return(p,r)['proposed_primary_success_bounds'] == [1,1]
    wrong = copy.deepcopy(r);wrong['packet_set_sha256'] = 'unbound'
    with pytest.raises(ValueError, match='hash mismatch'):
        score_return(p,wrong)
    wrong = copy.deepcopy(r);wrong['required_unit_coverage'][0]['response_span'] = 'Invented quote'
    with pytest.raises(ValueError, match='span'):
        score_return(p,wrong)
