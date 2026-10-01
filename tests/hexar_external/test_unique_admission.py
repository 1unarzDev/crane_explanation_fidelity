"""Confirmation admission must bind the actual alias adapter and its checks."""
import copy
import hashlib
import json

import pytest

from analysis.hexar_external.confirmatory_v1.unique_admission import (
    MANIFESTS, SCENARIOS, admission_errors,
)


def fixture(tmp_path):
    def pin(name, value):
        path = tmp_path / name
        path.write_text(value)
        return {'path': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    bindings = {key: pin(key, key) for key in
                ('implementation', 'scientific_source', 'expansion_implementation', 'execution_adapter')}
    report = dict(schema='hexar-unique-adapter-qualification/v1', status='QUALIFIED',
                  bindings=bindings, scenarios=dict.fromkeys(SCENARIOS, True),
                  confirmatory_outputs_generated=0)
    policy = dict(status='READY_FOR_FREEZE', execution_adapter_qualified=True,
                  expected_unique_requests_per_episode_per_method=6,
                  battery_cells_per_episode_per_method=9,
                  qualification=pin('qualification.json', json.dumps(report)))
    for name, binding in bindings.items():
        if name != 'execution_adapter':
            policy[name] = binding['path']
            policy[name + '_sha256'] = binding['sha256']
    docs = {name: {'unique_request_policy': copy.deepcopy(policy)} for name in MANIFESTS}
    docs['comparator_freeze.json']['execution_adapter'] = bindings['execution_adapter']
    return docs, report


def test_bound_qualification_passes_and_changed_source_blocks(tmp_path):
    docs, _ = fixture(tmp_path)
    assert admission_errors(docs, tmp_path) == []
    (tmp_path / 'expansion_implementation').write_text('mutated')
    assert any('pinned bytes changed' in e for e in admission_errors(docs, tmp_path))


@pytest.mark.parametrize('mutation', ['missing_policy', 'disagree', 'unqualified', 'wrong_counts',
                                      'different_adapter', 'outside_root'])
def test_policy_or_binding_mutations_fail_closed(tmp_path, mutation):
    docs, _ = fixture(tmp_path)
    policy = docs['battery.json']['unique_request_policy']
    if mutation == 'missing_policy':
        del docs['endpoint.json']['unique_request_policy']
    elif mutation == 'disagree':
        policy['rule'] = 'retry alias'
    elif mutation == 'unqualified':
        for doc in docs.values():
            doc['unique_request_policy']['execution_adapter_qualified'] = False
    elif mutation == 'wrong_counts':
        policy['expected_unique_requests_per_episode_per_method'] = True
    elif mutation == 'different_adapter':
        path = tmp_path / 'other'; path.write_text('other')
        docs['comparator_freeze.json']['execution_adapter'] = dict(path='other', sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    else:
        policy['implementation'] = '../outside'
    assert admission_errors(docs, tmp_path)


@pytest.mark.parametrize('mutation', ['missing_check', 'failed_check', 'not_boolean',
                                      'wrong_binding', 'prior_confirmation', 'nonterminal'])
def test_report_cannot_qualify_incomplete_or_other_adapter(tmp_path, mutation):
    docs, report = fixture(tmp_path)
    if mutation == 'missing_check':
        report['scenarios'].pop(SCENARIOS[0])
    elif mutation == 'failed_check':
        report['scenarios'][SCENARIOS[0]] = False
    elif mutation == 'not_boolean':
        report['scenarios'][SCENARIOS[0]] = 1
    elif mutation == 'wrong_binding':
        report['bindings']['execution_adapter']['sha256'] = 'a' * 64
    elif mutation == 'prior_confirmation':
        report['confirmatory_outputs_generated'] = 1
    else:
        report['status'] = 'RUNNING'
    path = tmp_path / 'qualification.json'; path.write_text(json.dumps(report))
    for doc in docs.values():
        doc['unique_request_policy']['qualification']['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert admission_errors(docs, tmp_path)
