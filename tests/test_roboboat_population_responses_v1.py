import json
from pathlib import Path
import pytest
import run_roboboat_population_responses_v1 as runner


def fixture(tmp_path):
    source = json.loads((runner.DOC/'contact_policy_response_declaration_v2.json').read_text())
    registry = {'status': 'DEVELOPMENT_EXPLORATORY_NOT_CONFIRMATION',
                'rows': [{'id': 'new-1', 'cluster_id': 'cluster-1'}, {'id': 'bad-1', 'cluster_id': 'cluster-2'},
                         {'id': 'pending-1', 'cluster_id': 'cluster-3'}]}
    registry_path = tmp_path/'registry.json'
    registry_path.write_text(json.dumps(registry))
    captures = tmp_path/'captures'
    for i, row in enumerate(registry['rows'][:2]):
        capture = captures/row['id']; capture.mkdir(parents=True)
        (capture/'capture-attempt.json').write_text(json.dumps({'status': 'VALID_DEVELOPMENT' if i == 0 else 'TECHNICAL_FAILURE',
            'row': row, 'registry_sha256': runner.digest(registry_path), 'error': 'transport' if i else None}))
    for level, entry in enumerate(source['entries'][:3]):
        capture = captures/'new-1'
        for key, directory in [('packet', 'method_packets'), ('candidate', 'candidate_outputs')]:
            target = capture/directory/f'L{level}.json'; target.parent.mkdir(exist_ok=True)
            target.write_bytes((runner.ROOT/entry[key]['path']).read_bytes())
        (capture/'effective-configuration.yaml').write_bytes((runner.ROOT/entry['effective_configuration']['path']).read_bytes())
    return registry_path, captures, tmp_path/'declaration.json'


def test_prepare_all_valid_and_failure_accounting(tmp_path):
    registry, captures, path = fixture(tmp_path)
    with pytest.raises(ValueError, match='incomplete'):
        runner.prepare(registry, captures, path)
    d = runner.prepare(registry, captures, path, allow_completed_subset=True)
    assert len(d['entries']) == 3
    assert [a['status'] for a in d['capture_accounting']] == ['VALID_DEVELOPMENT', 'TECHNICAL_FAILURE', 'PENDING']
    assert d['confirmation_n'] == d['alpha_consumed'] == 0
    assert d['B2']['model'] == 'gpt-6-sol'
    assert len(d['method_sources']) == 5


def test_workspace_parity_isolation_and_one_shot(tmp_path):
    registry, captures, path = fixture(tmp_path)
    d = runner.prepare(registry, captures, path, allow_completed_subset=True)
    seen = []
    def caller(cache, role, work, prompt, model, effort, schema, **kwargs):
        files = {p.name for p in work.iterdir()}
        assert files == {'evidence.json', 'effective-configuration.yaml', 'configuration-basis.json',
                         *[Path(b['path']).name for b in d['method_sources']]}
        assert 'evaluator' not in files and 'B4.json' not in files
        assert model == 'gpt-6-sol' and effort == 'high'
        assert kwargs == {'allow_tools': True, 'timeout': 300}
        seen.append(role)
        return {'parsed_final': {'answer': 'Supported explanation.'}, 'cache_key': 'mock', 'latency_s': 0}
    runner.run(path, tmp_path/'outputs', caller=caller)
    runner.run(path, tmp_path/'outputs', caller=caller)
    assert len(seen) == 3
    terminal = json.loads((tmp_path/'outputs/responses/new-1-L0/response-terminal.json').read_text())
    assert terminal['status'] == 'COMPLETE_RESPONSE_SUPPORT_UNJUDGED'


def test_preflight_hash_failure_before_calls(tmp_path):
    registry, captures, path = fixture(tmp_path)
    runner.prepare(registry, captures, path, allow_completed_subset=True)
    (captures/'new-1/method_packets/L2.json').write_text('{}')
    def caller(*args, **kwargs):
        pytest.fail('provider called before integrity check')
    with pytest.raises(ValueError, match='bound input'):
        runner.run(path, tmp_path/'outputs', caller=caller)


def test_failure_retained_and_unresolved_intent_blocks_restart(tmp_path):
    registry, captures, path = fixture(tmp_path)
    d = runner.prepare(registry, captures, path, allow_completed_subset=True)
    count = []
    def caller(*args, **kwargs):
        count.append(1)
        raise RuntimeError('transport timeout')
    output = tmp_path/'outputs'
    first = runner.execute(d['entries'][0], d, path, output, caller=caller)
    assert first['status'] == 'TECHNICAL_RESPONSE_FAILURE'
    assert runner.execute(d['entries'][0], d, path, output, caller=caller) == first
    assert len(count) == 1
    intent = output/'intents/new-1-L1.json'; intent.write_text('{}')
    with pytest.raises(FileExistsError):
        runner.execute(d['entries'][1], d, path, output, caller=caller)
