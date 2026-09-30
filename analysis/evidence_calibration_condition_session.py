#!/usr/bin/env python3
"""Development condition ownership for MCP v5; no provider/model execution."""
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
FIELDS = BASE_FIELDS | {'scope_registry', 'execution_scope', 'plan_sha256'}


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


def create_registry(path: Path, campaign_id: str, plan_sha256: str):
    ExecutionScope(campaign_id, 'registry', 'registry', 'B0')
    sha256(plan_sha256)
    path.mkdir(parents=True, exist_ok=False)
    # Interrupted initialization remains unusable; never fill in an existing registry.
    sync_directory(path.parent)
    write_once(path / 'registry.intent.json', {'schema': 'crane-condition-session-registry/v1-development',
        'campaign_id': campaign_id, 'plan_sha256': plan_sha256,
        'scope': 'ONE_MCP_V5_SESSION_PER_REGISTERED_CONDITION_METHOD',
        'model_execution_authorized': False})
    sync_directory(path)


def claim(configuration: dict) -> Path:
    if not isinstance(configuration, dict) or set(configuration) != FIELDS:
        raise ValueError('exact guarded coordinator fields required')
    scope = ExecutionScope(**configuration['execution_scope'])
    plan = sha256(configuration['plan_sha256'])
    if configuration['identity']['method_id'] != scope.method_id:
        raise ValueError('method differs from registered scope')
    registry = Path(configuration['scope_registry']).resolve(strict=True)
    workspace = Path(configuration['workspace']).resolve(strict=True)
    records = Path(configuration['records']).resolve()
    if registry == workspace or workspace in registry.parents:
        raise ValueError('scope registry must be outside method workspace')
    if records == registry or records in registry.parents or registry in records.parents:
        raise ValueError('scope registry and session records must be separate')
    expected = {'schema': 'crane-condition-session-registry/v1-development',
        'campaign_id': scope.campaign_id, 'plan_sha256': plan,
        'scope': 'ONE_MCP_V5_SESSION_PER_REGISTERED_CONDITION_METHOD',
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
    sources = [Path(__file__), Path(__file__).with_name('evidence_calibration_mcp_stdio_v5.py'),
        Path(__file__).with_name('evidence_calibration_tool_broker_v7.py'),
        Path(__file__).with_name('evidence_calibration_computation_cpu_ledger_v2.py'),
        Path(__file__).with_name('evidence_calibration_local_tool_sandbox_v10.py')]
    write_once(owner / 'session-owner.intent.json', {
        'schema': 'crane-condition-session-owner/v1-development', 'execution_scope': asdict(scope),
        'plan_sha256': plan, 'configuration_sha256': canonical_sha256(configuration),
        'records': str(records), 'workspace_sha256': configuration['identity']['workspace_sha256'],
        'computation_cpu_limit': configuration['computation_cpu_limit'],
        'cpu_budget': configuration['cpu_budget'],
        'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'terminal_record_pending': True, 'model_execution_authorized': False})
    sync_directory(owner)
    return owner


def serve(configuration: dict, source, sink) -> int:
    # Claim is before Server construction: a failed/unknown construction consumes ownership.
    owner = claim(configuration)
    server = None
    try:
        server = Server(Path(configuration['workspace']), configuration['identity'], Path(configuration['records']),
            limits=Limits(**configuration['limits']), tree_limits=TreeLimits(**configuration['tree_limits']),
            scratch_limits=ScratchLimits(**configuration['scratch_limits']), cpu_budget=CpuBudget(**configuration['cpu_budget']),
            computation_cpu_limit=ComputationCpuLimit(**configuration['computation_cpu_limit']),
            max_calls=configuration['max_calls'], max_messages=configuration['max_messages'],
            max_request_bytes=configuration['max_request_bytes'])
        server.serve(source, sink)
    except BaseException as error:
        write_once(owner / 'session-owner.result.json', {'status': 'FAILED_RETAIN_NO_RESTART',
            'error_type': type(error).__name__, 'model_execution_authorized': False,
            'computation_cpu_ledger': server.broker.cpu_ledger.snapshot() if server is not None else None})
        sync_directory(owner)
        raise
    # If terminal storage fails, intent remains pending; ownership cannot be reacquired.
    session_path = Path(configuration['records']) / 'session.result.json'
    write_once(owner / 'session-owner.result.json', {'status': 'SESSION_TERMINAL_RETAIN_NO_RESTART',
        'session_terminal_status': server.terminal_status,
        'session_terminal_sha256': hashlib.sha256(session_path.read_bytes()).hexdigest(),
        'computation_cpu_ledger': server.broker.cpu_ledger.snapshot(), 'model_execution_authorized': False})
    sync_directory(owner)
    return 0 if server.terminal_status == 'STDIN_EOF' else 65


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    args = parser.parse_args()
    return serve(strict_json(args.configuration.read_bytes()), sys.stdin.buffer, sys.stdout.buffer)


if __name__ == '__main__':
    sys.exit(main())
