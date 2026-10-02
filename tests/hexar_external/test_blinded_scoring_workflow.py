import copy
import json
from pathlib import Path

import pytest

from analysis.hexar_external.confirmatory_v1.blinded_scoring_workflow import (
    reference_registry, prepare, select_C, finalize,
)
from analysis.hexar_external.confirmatory_v1.journal import fingerprint
from analysis.hexar_external.confirmatory_v1.development_unique_scoring_v2 import job as old_job
from analysis.hexar_external.acquisition.navigation_usefulness_v2 import public_packet, reference

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'manifests/hexar_external/confirmatory_v1'


def fixtures():
    plan = json.loads((BASE / 'development_unique_methods_v2/unique_request_plan.json').read_text())
    outputs = json.loads((BASE / 'development_unique_methods_v2/report.json').read_text())['answers']
    source = ROOT / 'manifests/hexar_external/acquisition/controller_boundary_qualification_v13.json'
    entries = []
    for row in json.loads(source.read_text())['packets']:
        packet = public_packet(row['method_packet'])
        entries.append(dict(episode_id=row['development_id'],
                            job_id=row['question_id'] + '-' + row['condition'],
                            packet=packet, reference=reference(packet)))
    registry = reference_registry(entries)
    public, private = prepare(plan, outputs, registry, b'qualification fixture key only!!' * 2, 701)
    old = json.loads((BASE / 'development_unique_scoring_v2/report.json').read_text())
    old_attempts = {r['opaque_job']: r for r in old['attempts']}
    attempts = {}
    for entry in private['entries']:
        for slot in ('A', 'B'):
            prior_id = old_job(dict(unique_request_id=entry['unique_request_id'], payload=None), slot)['opaque_job']
            attempts[entry['opaque_slots'][slot]] = copy.deepcopy(old_attempts[prior_id])
    return plan, outputs, registry, public, private, attempts


def test_replay_retained_real_labels_reproduces_six_ties_without_inference():
    plan, outputs, registry, public, private, attempts = fixtures()
    assert select_C(public, attempts) == []
    result = finalize(plan, outputs, registry, public, private, attempts, {})
    assert result['paired_counts'] == [0, 0, 6, 0]
    assert len(result['jobs']) == 108
    assert result['unique_scoring_outcomes'] == 72
    assert result['initial_judge_calls'] == 144
    assert result['adjudication_C_calls'] == 0
    assert result['agent_assessed'] is True and result['human_validated'] is False
    assert 'p_value' not in result


def test_judge_jobs_omit_method_and_registry_identities_and_C_sees_no_prior_labels():
    _, _, _, public, private, _ = fixtures()
    assert len(public['initial_jobs']) == 144 and len(public['reserved_C_jobs']) == 72
    for job in public['initial_jobs'] + public['reserved_C_jobs']:
        assert set(job) == {'opaque_job', 'answer_id', 'slot', 'payload'}
        assert set(job['payload']) == {'question', 'visible_evidence', 'required_units', 'answer'}
        assert 'HX-CONTRACT' not in json.dumps(job) and 'HX-PROMPT' not in json.dumps(job)
        assert 'hexar-tiago-dev-' not in json.dumps(job)
    assert set(private['entries'][0]) == {'unique_request_id', 'answer_id', 'method_status', 'opaque_slots'}


def test_missing_initial_label_cannot_be_repaired_and_omission_remains_known_failure():
    plan, outputs, registry, public, private, attempts = fixtures()
    entry = next(r for r in private['entries']
                 if next(x for x in plan['requests'] if x['unique_request_id'] == r['unique_request_id'])['method'] == 'HX-CONTRACT')
    attempts[entry['opaque_slots']['A']] = dict(status='TECHNICAL_FAILURE', parsed=None)
    assert select_C(public, attempts) == []
    result = finalize(plan, outputs, registry, public, private, attempts, {})
    assert result['paired_counts'] == [0, 1, 5, 0]
    with pytest.raises(ValueError, match='scheduled judge attempt'):
        finalize(plan, outputs, registry, public, private, attempts,
                 {entry['opaque_slots']['C']: dict(status='TECHNICAL_FAILURE')})


def test_disagreement_gets_one_isolated_C_and_failed_C_stays_unresolved():
    plan, outputs, registry, public, private, attempts = fixtures()
    entry = private['entries'][0]
    changed = attempts[entry['opaque_slots']['B']]['parsed']
    changed['covered_units'] = []
    selected = select_C(public, attempts)
    assert len(selected) == 1 and selected[0]['opaque_job'] == entry['opaque_slots']['C']
    result = finalize(plan, outputs, registry, public, private, attempts,
                      {entry['opaque_slots']['C']: dict(status='TECHNICAL_FAILURE', parsed=None)})
    assert result['labels'][entry['unique_request_id']]['status'] == 'UNRESOLVED'
    # A matching C keeps the full failure vector; it never chooses components
    # separately to manufacture a supported/covered label.
    result = finalize(plan, outputs, registry, public, private, attempts,
                      {entry['opaque_slots']['C']: attempts[entry['opaque_slots']['B']]})
    assert result['labels'][entry['unique_request_id']]['status'] == 'FAIL'


def test_changed_reference_or_private_linkage_fails_closed():
    plan, outputs, registry, public, private, attempts = fixtures()
    changed = copy.deepcopy(private)
    changed['entries'][0]['method_status'] = 'TECHNICAL_FAILURE'
    with pytest.raises(ValueError, match='hashes changed'):
        finalize(plan, outputs, registry, public, changed, attempts, {})
    changed = copy.deepcopy(registry)
    changed['entries'][0]['reference']['required_units'].clear()
    with pytest.raises(ValueError, match='reference changed'):
        prepare(plan, outputs, changed, b'fixture-only' * 3, 701)


def test_aliases_share_exact_dispositions_raw_hashes_and_scoring_hashes():
    plan, outputs, registry, public, private, attempts = fixtures()
    result = finalize(plan, outputs, registry, public, private, attempts, {})
    byuid = {}
    for row in result['jobs']:
        fields = {k: row[k] for k in ('response_sha256', 'scoring_artifact_sha256',
                  'unsupported_material', 'overlicensed_specificity', 'missing_required_unit')}
        uid = row['source_unique_request_id']
        assert uid not in byuid or byuid[uid] == fields
        byuid[uid] = fields
    assert len(byuid) == 72


def test_failed_method_receives_no_judge_calls_and_keeps_conservative_disposition():
    plan, outputs, registry, _, _, _ = fixtures()
    uid = next(r['unique_request_id'] for r in plan['requests'] if r['method'] == 'HX-PROMPT')
    failed = copy.deepcopy(outputs)
    failed_row = next(r for r in failed if r['unique_request_id'] == uid)
    failed_row.update(status='TECHNICAL_FAILURE', answer=None, answer_sha256=None)
    public, private = prepare(plan, failed, registry, b'qualification fixture key only!!' * 2, 701)
    entry = next(r for r in private['entries'] if r['unique_request_id'] == uid)
    assert entry['opaque_slots'] == {}
    assert len(public['initial_jobs']) == 142 and len(public['reserved_C_jobs']) == 71


def test_known_prompt_omission_dominates_another_unknown_cell():
    plan, outputs, registry, public, private, attempts = fixtures()
    prompt = [entry for entry in private['entries'] if next(
        x for x in plan['requests'] if x['unique_request_id'] == entry['unique_request_id'])['method'] == 'HX-PROMPT']
    first = prompt[0]
    episode = next(x['episode_id'] for x in plan['requests'] if x['unique_request_id'] == first['unique_request_id'])
    other = next(entry for entry in prompt[1:] if next(x['episode_id'] for x in plan['requests']
        if x['unique_request_id'] == entry['unique_request_id']) == episode)
    for slot in ('A', 'B'):
        attempts[first['opaque_slots'][slot]]['parsed']['covered_units'] = []
    attempts[other['opaque_slots']['A']] = dict(status='TECHNICAL_FAILURE', parsed=None)
    result = finalize(plan, outputs, registry, public, private, attempts, {})
    row = next(r for r in result['recording_endpoints'] if r['recording_id'] == episode)
    assert row['method_states']['HX-PROMPT'] == 'FAIL'
    assert row['failure_bounds']['HX-PROMPT'] == [True, True]
    assert result['paired_counts'] == [1, 0, 5, 0]


def test_third_component_vector_is_unresolved_without_component_voting():
    plan, outputs, registry, public, private, attempts = fixtures()
    entry = next(e for e in private['entries']
                 if len(attempts[e['opaque_slots']['A']]['parsed']['covered_units']) > 1)
    a = attempts[entry['opaque_slots']['A']]
    b = attempts[entry['opaque_slots']['B']]
    b['parsed']['covered_units'] = []
    c = copy.deepcopy(a)
    c['parsed']['covered_units'] = a['parsed']['covered_units'][:1]
    result = finalize(plan, outputs, registry, public, private, attempts,
                      {entry['opaque_slots']['C']: c})
    assert result['labels'][entry['unique_request_id']]['status'] == 'UNRESOLVED'
    assert result['labels'][entry['unique_request_id']]['reason'] == 'three_distinct_component_vectors'
