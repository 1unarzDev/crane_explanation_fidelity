#!/usr/bin/env python3
"""Plan-bound development condition and response ownership for MCP v5; no provider/model execution."""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import os
from pathlib import Path
import re
import sys

from evidence_calibration_io import canonical_sha256
from evidence_calibration_mcp_stdio_v5 import Server, strict_json
from evidence_calibration_local_tool_sandbox_v2 import Limits
from evidence_calibration_local_tool_sandbox_v10 import TreeLimits, ScratchLimits, CpuBudget
from evidence_calibration_computation_cpu_ledger_v2 import ComputationCpuLimit
from observe_evidence_calibration_cgroup_limits import write_once

BASE_FIELDS = {'workspace', 'identity', 'records', 'limits', 'tree_limits', 'scratch_limits',
               'cpu_budget', 'computation_cpu_limit', 'max_calls', 'max_messages', 'max_request_bytes'}
FIELDS = BASE_FIELDS | {'scope_registry', 'execution_scope', 'plan_sha256', 'execution_plan', 'response_byte_limit'}


@dataclass(frozen=True)
class ExecutionScope:
    campaign_id: str
    episode_id: str
    condition_id: str
    method_id: str

    def __post_init__(self):
        for value in asdict(self).values():
            if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', value):
                raise ValueError('explicit registered scope identifiers required')
        if self.method_id not in {'B0', 'B1', 'B2', 'B3', 'B4'}:
            raise ValueError('unknown method')


def sha256(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('explicit plan SHA-256 required')
    return value


def sync_directory(path: Path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def source_hashes() -> dict:
    names = ['evidence_calibration_condition_session_v3.py', 'evidence_calibration_response_egress.py', 'evidence_calibration_mcp_stdio_v5.py',
        'evidence_calibration_tool_broker_v7.py', 'evidence_calibration_computation_cpu_ledger_v2.py',
        'evidence_calibration_local_tool_sandbox_v10.py']
    return {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in names}


def configuration_hash(configuration: dict) -> str:
    # Exclude only the raw plan digest to avoid a plan/configuration hash cycle.
    # Plan path, registry path, identity, limits and all other fields remain bound.
    return canonical_sha256({k: v for k, v in configuration.items() if k != 'plan_sha256'})


def build_plan(configurations: list[dict]) -> dict:
    if not isinstance(configurations, list) or not 1 <= len(configurations) <= 10000:
        raise ValueError('explicit bounded development configuration list required')
    entries = []
    campaign = registry = plan_path = None
    seen = set()
    for configuration in configurations:
        if not isinstance(configuration, dict) or set(configuration) != FIELDS:
            raise ValueError('exact plan-bound coordinator fields required')
        scope = ExecutionScope(**configuration['execution_scope'])
        if configuration['identity']['method_id'] != scope.method_id:
            raise ValueError('method differs from declared plan scope')
        current_registry = str(Path(configuration['scope_registry']).resolve())
        current_plan = str(Path(configuration['execution_plan']).resolve())
        if campaign is None:
            campaign, registry, plan_path = scope.campaign_id, current_registry, current_plan
        if (scope.campaign_id, current_registry, current_plan) != (campaign, registry, plan_path):
            raise ValueError('all entries must bind one campaign, registry and plan path')
        key = canonical_sha256(asdict(scope))
        if key in seen:
            raise ValueError('duplicate condition/method ownership scope in plan')
        seen.add(key)
        entries.append({'execution_scope': asdict(scope), 'configuration_sha256': configuration_hash(configuration)})
    return {'schema': 'crane-condition-session-plan/v1-development',
        'status': 'DEVELOPMENT_INFRASTRUCTURE_ONLY', 'model_execution_authorized': False,
        'campaign_id': campaign, 'scope_registry': registry, 'execution_plan': plan_path,
        'source_sha256': source_hashes(), 'entries': entries}


def read_plan(path: Path, expected_sha256: str) -> dict:
    from evidence_calibration_computation_cpu_ledger_v2 import bounded_json
    plan, actual_hash = bounded_json(path, 4 * 1024**2)
    expected = {'schema', 'status', 'model_execution_authorized', 'campaign_id',
                'scope_registry', 'execution_plan', 'source_sha256', 'entries'}
    if (actual_hash != sha256(expected_sha256) or set(plan) != expected
            or plan['schema'] != 'crane-condition-session-plan/v1-development'
            or plan['status'] != 'DEVELOPMENT_INFRASTRUCTURE_ONLY'
            or plan['model_execution_authorized'] is not False
            or plan['source_sha256'] != source_hashes()
            or plan['execution_plan'] != str(path.resolve())
            or not isinstance(plan['entries'], list) or not 1 <= len(plan['entries']) <= 10000):
        raise ValueError('development plan bytes/schema/source/authorization binding mismatch')
    registry = Path(plan['scope_registry'])
    if str(registry.resolve()) != plan['scope_registry']:
        raise ValueError('plan must bind an absolute canonical registry path')
    seen = set()
    for entry in plan['entries']:
        if not isinstance(entry, dict) or set(entry) != {'execution_scope', 'configuration_sha256'}:
            raise ValueError('exact plan entry fields required')
        scope = ExecutionScope(**entry['execution_scope'])
        if scope.campaign_id != plan['campaign_id']:
            raise ValueError('plan campaign differs from entry scope')
        sha256(entry['configuration_sha256'])
        key = canonical_sha256(asdict(scope))
        if key in seen:
            raise ValueError('duplicate condition/method ownership scope in plan')
        seen.add(key)
    return plan


def create_registry(path: Path, execution_plan: Path, plan_sha256: str):
    plan = read_plan(execution_plan, plan_sha256)
    if str(path.resolve()) != plan['scope_registry']:
        raise ValueError('registry path differs from bound development plan')
    path.mkdir(parents=True, exist_ok=False)
    sync_directory(path.parent)
    write_once(path / 'registry.intent.json', {'schema': 'crane-condition-session-registry/v2-development',
        'campaign_id': plan['campaign_id'], 'plan_sha256': plan_sha256,
        'execution_plan': str(execution_plan.resolve()),
        'scope': 'ONE_MCP_V5_SESSION_PER_PLANNED_CONDITION_METHOD',
        'model_execution_authorized': False})
    sync_directory(path)


def claim(configuration: dict) -> Path:
    if not isinstance(configuration, dict) or set(configuration) != FIELDS:
        raise ValueError('exact guarded coordinator fields required')
    scope = ExecutionScope(**configuration['execution_scope'])
    plan = sha256(configuration['plan_sha256'])
    execution_plan = Path(configuration['execution_plan'])
    declared = read_plan(execution_plan, plan)
    if (str(Path(configuration['scope_registry']).resolve()) != declared['scope_registry']
            or scope.campaign_id != declared['campaign_id']):
        raise ValueError('configuration campaign/registry differs from plan')
    matching = [row for row in declared['entries'] if row['execution_scope'] == asdict(scope)]
    if len(matching) != 1 or matching[0]['configuration_sha256'] != configuration_hash(configuration):
        raise ValueError('condition/configuration absent from bound development plan')
    if configuration['identity']['method_id'] != scope.method_id:
        raise ValueError('method differs from registered scope')
    registry = Path(configuration['scope_registry']).resolve(strict=True)
    workspace = Path(configuration['workspace']).resolve(strict=True)
    records = Path(configuration['records']).resolve()
    if registry == workspace or workspace in registry.parents:
        raise ValueError('scope registry must be outside method workspace')
    if records == registry or records in registry.parents or registry in records.parents:
        raise ValueError('scope registry and session records must be separate')
    expected = {'schema': 'crane-condition-session-registry/v2-development',
        'campaign_id': scope.campaign_id, 'plan_sha256': plan,
        'execution_plan': str(execution_plan.resolve()),
        'scope': 'ONE_MCP_V5_SESSION_PER_PLANNED_CONDITION_METHOD',
        'model_execution_authorized': False}
    if strict_json((registry / 'registry.intent.json').read_bytes()) != expected:
        raise ValueError('registry campaign/plan binding mismatch')
    # Config, budgets, source versions and record paths deliberately do not affect the key.
    # Changing any of them cannot acquire a second session for this registered identity.
    owner = registry / canonical_sha256(asdict(scope))
    try:
        owner.mkdir()
    except FileExistsError as error:
        raise ValueError('condition session already reserved; no restart, adoption or budget reset') from error
    sync_directory(registry)
    write_once(owner / 'session-owner.intent.json', {
        'schema': 'crane-condition-session-owner/v3-development', 'execution_scope': asdict(scope),
        'plan_sha256': plan, 'execution_plan': str(execution_plan.resolve()), 'planned_configuration_sha256': matching[0]['configuration_sha256'], 'configuration_sha256': canonical_sha256(configuration),
        'records': str(records), 'workspace_sha256': configuration['identity']['workspace_sha256'],
        'computation_cpu_limit': configuration['computation_cpu_limit'],
        'cpu_budget': configuration['cpu_budget'],
        'source_sha256': declared['source_sha256'],
        'terminal_record_pending': True, 'model_execution_authorized': False})
    sync_directory(owner)
    return owner


def serve(configuration: dict, source, sink) -> int:
    # Claim is before Server construction: a failed/unknown construction consumes ownership.
    owner = claim(configuration)
    server = None
    output = None
    try:
        from evidence_calibration_response_egress import BudgetedOutput, ResponseByteLimit
        output = BudgetedOutput(sink, owner / 'response-egress', limit=ResponseByteLimit(**configuration['response_byte_limit']))
        server = Server(Path(configuration['workspace']), configuration['identity'], Path(configuration['records']),
            limits=Limits(**configuration['limits']), tree_limits=TreeLimits(**configuration['tree_limits']),
            scratch_limits=ScratchLimits(**configuration['scratch_limits']), cpu_budget=CpuBudget(**configuration['cpu_budget']),
            computation_cpu_limit=ComputationCpuLimit(**configuration['computation_cpu_limit']),
            max_calls=configuration['max_calls'], max_messages=configuration['max_messages'],
            max_request_bytes=configuration['max_request_bytes'])
        server.serve(source, output)
    except BaseException as error:
        write_once(owner / 'session-owner.result.json', {'status': 'FAILED_RETAIN_NO_RESTART',
            'error_type': type(error).__name__, 'model_execution_authorized': False,
            'computation_cpu_ledger': server.broker.cpu_ledger.snapshot() if server is not None else None,
            'response_egress': output.snapshot() if output is not None else None})
        sync_directory(owner)
        raise
    # If terminal storage fails, intent remains pending; ownership cannot be reacquired.
    session_path = Path(configuration['records']) / 'session.result.json'
    write_once(owner / 'session-owner.result.json', {'status': 'SESSION_TERMINAL_RETAIN_NO_RESTART',
        'session_terminal_status': server.terminal_status,
        'session_terminal_sha256': hashlib.sha256(session_path.read_bytes()).hexdigest(),
        'computation_cpu_ledger': server.broker.cpu_ledger.snapshot(), 'response_egress': output.snapshot(), 'model_execution_authorized': False})
    sync_directory(owner)
    return 0 if server.terminal_status == 'STDIN_EOF' else 65


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    args = parser.parse_args()
    return serve(strict_json(args.configuration.read_bytes()), sys.stdin.buffer, sys.stdout.buffer)


if __name__ == '__main__':
    sys.exit(main())
