import json
from pathlib import Path

import pytest
import run_roboboat_unpaired_b4_candidate_v2 as runner


def setup(tmp_path, monkeypatch, *, different_source=False, different_input=False):
    prior = tmp_path / 'prior'; prior.mkdir()
    old_snapshot = tmp_path / 'old.json'; old_snapshot.write_text('{}')
    snapshot = tmp_path / 'new.json'; snapshot.write_text('{}')
    private = [{'relative_path': 'analysis/candidate.py', 'original': {'sha256': 'same'}}]
    entry = {'row_id': 'row', 'cluster_id': 'geometry', 'level': 0,
             'common_file_hash_signature': 'public', 'B4_private_workspace': str(tmp_path / 'work')}
    old = {'entries': [entry], 'private_B4_sources': private}
    new = json.loads(json.dumps(old))
    if different_source: new['private_B4_sources'][0]['original']['sha256'] = 'changed'
    if different_input: new['entries'][0]['common_file_hash_signature'] = 'changed'
    monkeypatch.setattr(runner, 'verify', lambda path: old if Path(path) == old_snapshot else new)
    declaration = {'input_snapshot': runner.binding(old_snapshot), 'sources': [],
        'candidate_override': None,
        'B4': 'full shared CRANE development v3 candidate, default deterministic realization'}
    dp = prior / 'declaration.json'; dp.write_text(json.dumps(declaration))
    outcome = {'row_id': 'row', 'cluster_id': 'geometry', 'level': 0,
        'status': 'TECHNICAL_CANDIDATE_FAILURE', 'common_input_signature': 'public',
        'error_type': 'ExampleFailure', 'error': 'Retained failure'}
    folder = prior / 'conditions/row-L0'; folder.mkdir(parents=True)
    (folder / 'terminal.json').write_text(json.dumps(outcome))
    (prior / 'terminal.json').write_text(json.dumps({'declaration': runner.binding(dp), 'results': [outcome],
        'endpoint_scores_released': False, 'candidate_promoted': False, 'B2_calls': 0, 'model_calls': 0, 'judge_calls': 0}))
    return snapshot, prior


def test_matching_prior_failure_is_reused_and_never_retried(tmp_path, monkeypatch):
    snapshot, prior = setup(tmp_path, monkeypatch)
    root = tmp_path / 'run'
    d = runner.prepare(snapshot, root, prior)
    assert set(d['reuse']) == {'row-L0'}
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **k: pytest.fail('Matched failure retried'))
    terminal = runner.execute(root)
    assert terminal['new_executions'] == 0 and terminal['reused_outcomes'] == 1
    assert terminal['results'][0]['error'] == 'Retained failure'
    assert terminal['successful_generations'] == 0 and terminal['endpoint_scores_released'] is False


def test_changed_candidate_sources_cannot_reuse_prior_outcome(tmp_path, monkeypatch):
    snapshot, prior = setup(tmp_path, monkeypatch, different_source=True)
    with pytest.raises(ValueError, match='sources/settings differ'):
        runner.prepare(snapshot, tmp_path / 'run', prior)


def test_changed_common_inputs_require_fresh_execution(tmp_path, monkeypatch):
    snapshot, prior = setup(tmp_path, monkeypatch, different_input=True)
    d = runner.prepare(snapshot, tmp_path / 'run', prior)
    assert d['reuse'] == {}
