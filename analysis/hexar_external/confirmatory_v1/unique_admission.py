"""Admission checks for one generation per identical within-episode request.

Pure validation: this neither qualifies an adapter nor authorizes dispatch.
"""
import hashlib
import json


MANIFESTS = ('battery.json', 'endpoint.json', 'comparator_freeze.json')
SCENARIOS = (
    'complete_request_identity', 'identical_alias_one_dispatch',
    'shared_technical_failure_no_retry', 'no_cross_episode_reuse',
    'no_cross_method_reuse', 'different_query_or_evidence_no_reuse',
    'closed_labels_reused', 'all_nine_cells_in_endpoint',
    'cost_counted_once', 'crash_claim_not_reissued',
)


def _pinned(root, pin):
    if not isinstance(pin, dict) or set(pin) != {'path', 'sha256'}:
        raise ValueError('path/sha256 pin required')
    path = root / pin['path']
    if path.resolve().is_relative_to(root.resolve()) is False:
        raise ValueError('pin outside repository')
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin['sha256']:
        raise ValueError('pinned bytes changed: ' + pin['path'])
    return path


def admission_errors(docs, root):
    errors = []
    policies = [docs.get(name, {}).get('unique_request_policy') for name in MANIFESTS]
    if any(not isinstance(p, dict) for p in policies):
        return ['unique requests: complete policy required in battery, endpoint and comparator']
    if any(p != policies[0] for p in policies[1:]):
        errors.append('unique requests: battery/endpoint/comparator policies disagree')
    policy = policies[0]
    if policy.get('status') != 'READY_FOR_FREEZE' or policy.get('execution_adapter_qualified') is not True:
        errors.append('unique requests: final adapter policy is not qualified and ready')
    if (type(policy.get('expected_unique_requests_per_episode_per_method')) is not int
            or policy['expected_unique_requests_per_episode_per_method'] != 6
            or type(policy.get('battery_cells_per_episode_per_method')) is not int
            or policy['battery_cells_per_episode_per_method'] != 9):
        errors.append('unique requests: expected six unique requests and nine battery cells')
    pins = {}
    for name in ('implementation', 'scientific_source', 'expansion_implementation'):
        try:
            pins[name] = {'path': policy[name], 'sha256': policy[name + '_sha256']}
            _pinned(root, pins[name])
        except (OSError, KeyError, TypeError, ValueError) as exc:
            errors.append('unique requests: missing/invalid ' + name + ': ' + str(exc))
    comparator = docs.get('comparator_freeze.json', {})
    try:
        adapter = comparator['execution_adapter']
        _pinned(root, adapter)
        qualification = json.loads(_pinned(root, policy['qualification']).read_text())
        if qualification.get('schema') != 'hexar-unique-adapter-qualification/v1' or qualification.get('status') != 'QUALIFIED':
            raise ValueError('terminal final-adapter qualification required')
        if qualification.get('bindings') != dict(pins, execution_adapter=adapter):
            raise ValueError('qualification binds another policy implementation/adapter')
        scenarios = qualification.get('scenarios', {})
        if set(scenarios) != set(SCENARIOS) or any(scenarios[k] is not True for k in SCENARIOS):
            raise ValueError('all specified alias/failure/crash/endpoint checks must pass')
        if qualification.get('confirmatory_outputs_generated') != 0:
            raise ValueError('qualification must precede confirmation')
    except (OSError, KeyError, TypeError, ValueError) as exc:
        errors.append('unique requests: qualification missing/invalid: ' + str(exc))
    return errors
