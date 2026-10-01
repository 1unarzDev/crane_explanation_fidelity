import json
import threading
import time

import pytest
import run_roboboat_population_inventory_v1 as runner


def fixture(tmp_path, statuses=('complete', 'failure', 'missing')):
    source = json.loads((runner.DOC/'contact_policy_response_declaration_v2.json').read_text())
    entries = []
    for index, original in enumerate(source['entries'][:len(statuses)]):
        entry = {'id': f'answer-{index}', 'row_id': 'row-1', 'cluster_id': 'cluster-1', 'level': index}
        for key in ('packet', 'candidate', 'effective_configuration'):
            path = runner.checked(original[key])
            entry[key] = runner.binding(path)
        entries.append(entry)
    d = {'schema': 'roboboat-population-response-declaration/v1',
         'disposition': 'DEVELOPMENT_ONLY_NO_CONFIRMATORY_INFERENCE',
         'entries': entries, 'capture_accounting': [{'id': 'pending', 'status': 'PENDING'}]}
    declaration = tmp_path/'response.json'
    declaration.write_text(json.dumps(d))
    responses = tmp_path/'responses'
    for entry, status in zip(entries, statuses):
        folder = responses/'responses'/entry['id']
        folder.mkdir(parents=True)
        if status == 'missing':
            continue
        terminal = {'status': 'COMPLETE_RESPONSE_SUPPORT_UNJUDGED' if status == 'complete' else 'TECHNICAL_RESPONSE_FAILURE',
                    'source_identity': {'declaration_sha256': runner.digest(declaration), 'entry': entry}, 'error': None if status == 'complete' else 'timeout'}
        runner.save(folder/'response-terminal.json', terminal)
        if status == 'complete':
            runner.save(folder/'B2.json', {'answer': 'Same supported answer.', 'model_calls': 1})
            candidate = json.loads(runner.checked(entry['candidate']).read_text())
            runner.save(folder/'B4.json', {'answer': candidate['answer'], 'model_calls': 0})
    return declaration, responses, tmp_path/'bank', tmp_path/'inventory.json'


def test_complete_snapshot_keeps_failures_missing_and_deterministic_b4(tmp_path):
    args = fixture(tmp_path)
    d = runner.prepare(*args)
    assert d['snapshot_entry_count'] == 3
    assert d['method_answer_counts'] == {'B2': 1, 'B4': 3}
    ledger = json.loads((args[2]/'response-accounting.json').read_text())
    assert [e['method_call_status'] for e in ledger['entries']] == [
        'COMPLETE_RESPONSE_SUPPORT_UNJUDGED', 'TECHNICAL_RESPONSE_FAILURE', 'MISSING_RESPONSE_TERMINAL']
    assert ledger['capture_accounting'][0]['status'] == 'PENDING'
    assert d['support_annotation_authorized'] is False
    assert d['new_independent_configuration_n'] == d['alpha_consumed'] == 0
    with pytest.raises(ValueError, match='one-shot'):
        runner.prepare(*args)


def test_deduplication_preserves_each_method_and_question_join(tmp_path):
    args = fixture(tmp_path, ('complete', 'complete', 'complete'))
    d = runner.prepare(*args)
    joins = json.loads((args[2]/'evaluator-join.json').read_text())['entries']
    assert len(joins) == 6
    baseline = [j for j in joins if j['method'] == 'B2']
    assert len({j['opaque_response_id'] for j in baseline}) == 1
    assert len({j['response_id'] for j in baseline}) == 3
    assert d['unique_answer_texts'] < d['original_answers']
    bank = json.loads((args[2]/'blind-bank.json').read_text())
    assert all(set(e) == {'opaque_response_id', 'response_text'} for e in bank['entries'])


def test_identity_and_deterministic_candidate_disagreement_rejected(tmp_path):
    args = fixture(tmp_path)
    path = args[1]/'responses/answer-0/response-terminal.json'
    data = json.loads(path.read_text())
    data['source_identity']['declaration_sha256'] = 'wrong'
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='source identity'):
        runner.prepare(*args)


def test_orphan_baseline_excluded_and_partial_valid_return_retained(tmp_path):
    args = fixture(tmp_path)
    runner.save(args[1]/'responses/answer-1/B2.json', {'answer': 'Valid return before downstream failure.'})
    runner.save(args[1]/'responses/answer-2/B2.json', {'answer': 'Unbound orphan.'})
    d = runner.prepare(*args)
    assert d['method_answer_counts']['B2'] == 2
    ledger = json.loads((args[2]/'response-accounting.json').read_text())['entries']
    assert ledger[2]['methods']['B2'] == 'ORPHAN_ANSWER_UNBOUND_TERMINAL_EXCLUDED'


def test_two_passes_at_most_two_calls_and_restart_no_retry(tmp_path):
    args = fixture(tmp_path, ('complete', 'complete', 'complete'))
    d = runner.prepare(*args)
    active = peak = 0
    lock = threading.Lock()
    seen = []
    def execute(case, slot, freeze, out):
        nonlocal active, peak
        assert set(case) == {'case_id', 'response_text'}
        with lock:
            active += 1
            peak = max(peak, active)
            seen.append((case['case_id'], slot))
        time.sleep(.002)
        with lock:
            active -= 1
        return {'validation': {'status': 'STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED'}}
    first = runner.run(args[3], args[2], executor=execute)
    assert len(seen) == 2*d['unique_answer_texts']
    assert peak <= 2
    assert {slot for _, slot in seen} == {'A', 'B'}
    assert runner.run(args[3], args[2], executor=execute) == first
    assert len(seen) == 2*d['unique_answer_texts']
    assert first['support_annotation_authorized'] is False


def test_preflight_modified_answer_blocks_all_calls(tmp_path):
    args = fixture(tmp_path)
    runner.prepare(*args)
    (args[1]/'responses/answer-0/B2.json').write_text('{}')
    with pytest.raises(ValueError, match='bound source changed'):
        runner.run(args[3], args[2], executor=lambda *a: pytest.fail('call before preflight'))


def test_missing_source_arrival_requires_new_snapshot(tmp_path):
    args = fixture(tmp_path)
    runner.prepare(*args)
    runner.save(args[1]/'responses/answer-1/B2.json', {'answer': 'late'})
    with pytest.raises(ValueError, match='fresh immutable bank'):
        runner.run(args[3], args[2], executor=lambda *a: pytest.fail('call before preflight'))


def test_extraction_failure_is_retained_without_retry(tmp_path):
    args = fixture(tmp_path)
    d = runner.prepare(*args)
    seen = []
    def fail(*a):
        seen.append(1)
        raise RuntimeError('provider timeout')
    result = runner.run(args[3], args[2], executor=fail)
    assert result['failed_extraction_attempts'] == d['unique_answer_texts']*2
    assert result['status'] == 'EXTRACTION_FAILURES_RETAINED_NO_RETRIES'
    runner.run(args[3], args[2], executor=fail)
    assert len(seen) == d['unique_answer_texts']*2


def test_unresolved_run_intent_refuses_restart(tmp_path):
    args = fixture(tmp_path)
    runner.prepare(*args)
    (args[2]/'extraction-run-intent.json').write_text('{}')
    with pytest.raises(FileExistsError):
        runner.run(args[3], args[2], executor=lambda *a: pytest.fail('retry'))


def test_source_bound_candidate_must_match_rendered_certificate(tmp_path):
    args = fixture(tmp_path, ('missing',))
    d = json.loads(args[0].read_text())
    original = json.loads(runner.checked(d['entries'][0]['candidate']).read_text())
    original['answer'] = 'Unbound changed explanation.'
    candidate = tmp_path/'bad-candidate.json'
    candidate.write_text(json.dumps(original))
    d['entries'][0]['candidate'] = runner.binding(candidate)
    args[0].write_text(json.dumps(d))
    with pytest.raises(ValueError, match='deterministic B4'):
        runner.prepare(*args)


def test_unresolved_method_intent_is_bound_and_identity_checked(tmp_path):
    args = fixture(tmp_path, ('missing',))
    d = json.loads(args[0].read_text())
    intent = args[1]/'intents/answer-0.json'
    runner.save(intent, {'declaration_sha256': runner.digest(args[0]), 'entry': d['entries'][0]})
    runner.prepare(*args)
    ledger = json.loads((args[2]/'response-accounting.json').read_text())['entries']
    assert ledger[0]['method_call_intent']['sha256'] == runner.digest(intent)
    assert ledger[0]['method_call_status'] == 'MISSING_RESPONSE_TERMINAL'
