"""Offline development qualification of primitives, never provider evaluation."""
from concurrent.futures import ThreadPoolExecutor
import copy
import hashlib
import json
from pathlib import Path
import pytest
from analysis.hexar_external.confirmatory_v1 import journal, blind_bank

FREEZE = 'a' * 64
JOB = {'recording_id': 'dev-fixture-only', 'method': 'HX-PROMPT', 'question_id': 'q1'}
REQUEST = {'prompt_sha256': 'b' * 64, 'payload': {'evidence': 'development-only'}}


def entry(method='HX-PROMPT'):
    return dict(recording_id='dev-fixture-only', method=method, question_id='q1', condition='full',
                answer='  I failed.\nThe cause is unknown.\t\n',
                method_packet={key: {} for key in blind_bank.PACKET_KEYS},
                reference={key: [] for key in blind_bank.REFERENCE_KEYS})


def test_claim_persists_across_restart_without_reissue(tmp_path):
    first = journal.OneAttemptJournal(tmp_path, FREEZE)
    assert first.state(JOB) == 'UNCLAIMED'
    first.claim(JOB, REQUEST)
    restarted = journal.OneAttemptJournal(tmp_path, FREEZE)
    assert restarted.state(JOB) == 'CLAIMED_NO_REISSUE'
    with pytest.raises(FileExistsError):
        restarted.claim(JOB, REQUEST)
    restarted.finish(JOB, REQUEST, {'status': 'INDETERMINATE_AFTER_CRASH'})
    assert restarted.state(JOB) == 'CLOSED'
    with pytest.raises(FileExistsError):
        restarted.claim(JOB, REQUEST)


def test_atomic_claim_race_allows_exactly_one_caller(tmp_path):
    instance = journal.OneAttemptJournal(tmp_path, FREEZE)
    def claim(_):
        try:
            instance.claim(JOB, REQUEST)
            return True
        except FileExistsError:
            return False
    with ThreadPoolExecutor(max_workers=16) as pool:
        assert sum(pool.map(claim, range(64))) == 1
    claim_path, outcome_path = instance.paths(JOB)
    assert json.loads(claim_path.read_text())['attempt_count'] == 1
    assert not outcome_path.exists()
    assert claim_path.stat().st_mode & 0o777 == 0o600


def test_crash_partial_claim_retained_and_not_reissued(tmp_path, monkeypatch):
    instance = journal.OneAttemptJournal(tmp_path, FREEZE)
    def crash(_):
        raise OSError('simulated fsync failure after claim creation')
    monkeypatch.setattr(journal.os, 'fsync', crash)
    with pytest.raises(OSError):
        instance.claim(JOB, REQUEST)
    assert instance.state(JOB) == 'CLAIMED_NO_REISSUE'
    with pytest.raises(FileExistsError):
        instance.claim(JOB, REQUEST)


def test_malformed_partial_claim_fails_closed(tmp_path):
    instance = journal.OneAttemptJournal(tmp_path, FREEZE)
    claim_path, _ = instance.paths(JOB)
    claim_path.write_text('{partial')
    with pytest.raises(json.JSONDecodeError):
        instance.finish(JOB, REQUEST, {'status': 'VALID'})
    with pytest.raises(FileExistsError):
        instance.claim(JOB, REQUEST)


@pytest.mark.parametrize('change', ['request', 'claim'])
def test_identity_mutation_rejected_before_finish(tmp_path, change):
    instance = journal.OneAttemptJournal(tmp_path, FREEZE)
    instance.claim(JOB, REQUEST)
    request = copy.deepcopy(REQUEST)
    if change == 'request':
        request['payload']['evidence'] = 'different'
    else:
        claim_path, _ = instance.paths(JOB)
        claim = json.loads(claim_path.read_text())
        claim['freeze_sha256'] = 'c' * 64
        claim_path.write_text(json.dumps(claim))
    with pytest.raises(ValueError, match='identity changed'):
        instance.finish(JOB, request, {'status': 'VALID'})
    assert instance.state(JOB) == 'CLAIMED_NO_REISSUE'


@pytest.mark.parametrize('status', ['VALID', 'TECHNICAL_FAILURE', 'INDETERMINATE_AFTER_CRASH'])
def test_closed_outcome_is_immutable_and_race_safe(tmp_path, status):
    instance = journal.OneAttemptJournal(tmp_path, FREEZE)
    instance.claim(JOB, REQUEST)
    def finish(_):
        try:
            instance.finish(JOB, REQUEST, {'status': status, 'raw_text': ' \nanswer\t'})
            return True
        except FileExistsError:
            return False
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(finish, range(24))) == 1
    assert instance.state(JOB) == 'CLOSED'
    _, outcome_path = instance.paths(JOB)
    assert json.loads(outcome_path.read_text())['outcome']['raw_text'] == ' \nanswer\t'


def test_missing_claim_and_open_dispositions_cannot_finish(tmp_path):
    instance = journal.OneAttemptJournal(tmp_path, FREEZE)
    with pytest.raises(FileNotFoundError):
        instance.finish(JOB, REQUEST, {'status': 'VALID'})
    instance.claim(JOB, REQUEST)
    for outcome in ({}, {'status': 'RETRY'}, {'status': 'SEMANTIC_RETRY'}):
        with pytest.raises(ValueError, match='closed outcome'):
            instance.finish(JOB, REQUEST, outcome)
    assert instance.state(JOB) == 'CLAIMED_NO_REISSUE'


def test_blind_bank_preserves_exact_text_and_only_approved_fields():
    source = [entry(), entry('HX-CONTRACT')]
    bank, mapping = blind_bank.build(source, b'x' * 32, 97)
    assert len(bank['entries']) == 2
    assert {row['answer_id'] for row in bank['entries']} == {row['answer_id'] for row in mapping['entries']}
    for row in bank['entries']:
        assert set(row) == {'answer_id', 'answer', 'method_packet', 'reference'}
        assert row['answer'] == source[0]['answer']
        assert set(row['method_packet']) == set(blind_bank.PACKET_KEYS)
        assert set(row['reference']) == set(blind_bank.REFERENCE_KEYS)
    digest = hashlib.sha256(source[0]['answer'].encode()).hexdigest()
    assert all(row['raw_answer_sha256'] == digest for row in mapping['entries'])
    assert all(len(row['answer_id']) == 64 for row in bank['entries'])
    assert 'HX-' not in json.dumps(bank)


@pytest.mark.parametrize('location,key', [
    ('method_packet', 'method'), ('method_packet', 'development_result'),
    ('method_packet', 'family'), ('reference', 'alpha'), ('reference', 'previous_labels'),
])
def test_unapproved_top_level_metadata_fails_closed(location, key):
    source = entry()
    source[location][key] = 'must not reach judge'
    with pytest.raises(ValueError):
        blind_bank.build([source], b'x' * 32, 1)


@pytest.mark.parametrize('location', ['method_packet', 'reference'])
def test_missing_projection_field_fails_closed(location):
    source = entry()
    source[location].pop(next(iter(source[location])))
    with pytest.raises(ValueError):
        blind_bank.build([source], b'x' * 32, 1)


def test_duplicate_identity_nontext_and_weak_secret_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        blind_bank.build([entry(), entry()], b'x' * 32, 1)
    source = entry()
    source['answer'] = {'answer': 'not raw text'}
    with pytest.raises(ValueError, match='raw text'):
        blind_bank.build([source], b'x' * 32, 1)
    for key in (b'weak', 'x' * 32):
        with pytest.raises(ValueError, match='256-bit'):
            blind_bank.build([entry()], key, 1)


def test_handle_and_bank_order_do_not_inherit_input_method_order():
    source = [entry(), entry('HX-CONTRACT')]
    first, _ = blind_bank.build(source, b'x' * 32, 97)
    reversed_bank, _ = blind_bank.build(list(reversed(source)), b'x' * 32, 97)
    assert first == reversed_bank
    different_key, _ = blind_bank.build(source, b'y' * 32, 97)
    assert {r['answer_id'] for r in first['entries']}.isdisjoint(
        r['answer_id'] for r in different_key['entries'])
