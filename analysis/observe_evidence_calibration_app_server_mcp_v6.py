#!/usr/bin/env python3
"""Synthetic offline installed-client MCP observation; never starts a model turn."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from evidence_calibration_io import canonical_sha256
from evidence_calibration_mcp_stdio_v5 import strict_json
from observe_evidence_calibration_cgroup_limits import write_once
from evidence_calibration_tool_broker_v7 import READ, COMPUTE, tool_definitions
from stage_evidence_calibration_workspace import inventory
from observe_evidence_calibration_tree_cpu_accounting_v3 import parse_properties

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_METHODS = frozenset({'initialize', 'thread/start', 'mcpServerStatus/list', 'mcpServer/tool/call'})
DISABLED_FEATURES = ('shell_tool', 'unified_exec', 'apps', 'plugins', 'remote_plugin', 'multi_agent',
                     'memories', 'hooks', 'skill_search', 'view_image', 'image_generation', 'code_mode')
SERVER = 'crane_offline'


def command(configuration: Path, workspace: Path, method: str) -> list[str]:
    if method not in {'B0', 'B1', 'B2', 'B3', 'B4'}:
        raise ValueError('unknown method')
    # This outer layer disables networking for inspection; it is NOT method confinement.
    # Private /dev is needed: a normal bind of / alone leaves /dev/null inaccessible.
    argv = ['/usr/bin/bwrap', '--unshare-net', '--die-with-parent', '--bind', '/', '/',
            '--dev', '/dev', '--', 'codex', 'app-server', '--listen', 'stdio://', '--strict-config']
    overrides = {**{f'features.{key}': False for key in DISABLED_FEATURES},
        'web_search': 'disabled', 'analytics.enabled': False,
        f'mcp_servers.{SERVER}.command': sys.executable,
        f'mcp_servers.{SERVER}.args': [str(ROOT / 'analysis/evidence_calibration_condition_session.py'),
                                      '--configuration', str(configuration)],
        f'mcp_servers.{SERVER}.env_vars': ['XDG_RUNTIME_DIR', 'DBUS_SESSION_BUS_ADDRESS'],
        f'mcp_servers.{SERVER}.cwd': str(workspace), f'mcp_servers.{SERVER}.required': True,
        f'mcp_servers.{SERVER}.startup_timeout_sec': 10, f'mcp_servers.{SERVER}.tool_timeout_sec': 5,
        f'mcp_servers.{SERVER}.enabled_tools': [row['name'] for row in tool_definitions(method)]}
    for key, value in overrides.items():
        argv.extend(['-c', key + '=' + json.dumps(value)])
    return argv


class OfflineClient:
    """Allowlist applies before writing any RPC. No turn, resume, steering or provider method."""
    def __init__(self, argv: list[str]):
        self.process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, start_new_session=True)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ, 'stdout')
        self.selector.register(self.process.stderr, selectors.EVENT_READ, 'stderr')
        self.raw = {'stdout': bytearray(), 'stderr': bytearray()}
        self.pending = bytearray()
        self.events, self.requests = [], []
        self.ordinal = 0
        self.cleanup = None

    def read(self, timeout: float):
        parsed = []
        for key, _ in self.selector.select(timeout):
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                self.selector.unregister(key.fileobj)
                continue
            if sum(map(len, self.raw.values())) + len(chunk) > 32 * 1024**2:
                raise RuntimeError('offline observer capture limit; stop without restart')
            self.raw[key.data].extend(chunk)
            if key.data == 'stdout':
                self.pending.extend(chunk)
                while b'\n' in self.pending:
                    line, _, remaining = self.pending.partition(b'\n')
                    self.pending = bytearray(remaining)
                    event = strict_json(line)
                    self.events.append(event)
                    parsed.append(event)
        return parsed

    def request(self, method: str, params: dict) -> dict:
        if method not in ALLOWED_METHODS:
            raise ValueError('offline observer forbids this RPC; no model turn is permitted')
        self.ordinal += 1
        obj = {'method': method, 'params': params, 'id': self.ordinal}
        self.requests.append(obj)
        self.process.stdin.write(json.dumps(obj).encode() + b'\n')
        self.process.stdin.flush()
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            for event in self.read(.05):
                if event.get('id') == self.ordinal:
                    if 'error' in event:
                        raise RuntimeError('offline app-server RPC error; inspect retained raw observation')
                    return event['result']
            if self.process.poll() is not None:
                raise RuntimeError('offline app-server exited; no restart')
        raise RuntimeError('offline observation timeout; no restart')

    def initialized(self):
        self.process.stdin.write(b'{"method":"initialized","params":{}}\n')
        self.process.stdin.flush()

    def close(self):
        self.process.stdin.close()
        # App-server can remain loaded after EOF. Stop this dedicated observation group;
        # no persistent daemon or study job is adopted/restarted.
        try:
            self.process.wait(timeout=.5)
            self.cleanup = 'STDIN_EOF_EXIT'
        except subprocess.TimeoutExpired:
            os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=1)
                self.cleanup = 'OBSERVATION_GROUP_SIGTERM'
            except subprocess.TimeoutExpired:
                os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait()
                self.cleanup = 'OBSERVATION_GROUP_SIGKILL'
        drain_deadline = time.monotonic() + 1
        while self.selector.get_map() and time.monotonic() < drain_deadline:
            self.read(.05)
        self.selector.close()
        self.process.stdout.close()
        self.process.stderr.close()



def verify_execution_records(events: Path, configuration: dict) -> list[dict]:
    """Check operator records without exposing payload audit bytes to the tool result."""
    terminals = sorted(events.glob('tool-*.execution/terminal.json'))
    if len(terminals) != 2:
        raise RuntimeError('expected exactly two computation terminals')
    records = []
    spent = 0
    for ordinal, path in enumerate(terminals):
        terminal = strict_json(path.read_bytes())
        intent_path = path.with_name('intent.json')
        intent = strict_json(intent_path.read_bytes())
        status_path = path.with_name('namespace-status.bin')
        status_hash = hashlib.sha256(status_path.read_bytes()).hexdigest()
        if (terminal['schema'] != 'crane-service-computation-terminal/v10-development'
                or terminal['unit'] != intent['unit']
                or terminal['namespace_status_sha256'] != status_hash
                or terminal['cleanup']['final_state']['return_code'] != 0
                or terminal['cleanup']['final_state']['stdout'].strip() != 'not-found'):
            raise RuntimeError('invalid lifecycle identity or computation cleanup')
        for key, config_key in [('local_limits', 'limits'), ('tree_limits', 'tree_limits'),
                                ('scratch_limits', 'scratch_limits')]:
            if intent[key] != configuration[config_key] or terminal['execution_audit'][key] != configuration[config_key]:
                raise RuntimeError('computation limits differ from coordinator configuration')
        accounting = terminal['cpu_accounting']
        budget = dict(configuration['cpu_budget'])
        budget['cumulative_nanoseconds'] = min(budget['cumulative_nanoseconds'], configuration['computation_cpu_limit']['total_nanoseconds'] - spent)
        final_cpu = accounting['final_cpu_nanoseconds']
        samples = sorted(path.parent.glob('cpu-sample-*.json'))
        if (intent['cpu_budget'] != budget or accounting['budget'] != budget
                or type(final_cpu) is not int or final_cpu <= 0
                or type(accounting['sample_count']) is not int
                or accounting['sample_count'] != len(samples) or not samples
                or accounting['last_observed_cpu_nanoseconds'] != final_cpu
                or accounting['observed_overshoot_nanoseconds'] != max(0, final_cpu-budget['cumulative_nanoseconds'])
                or accounting['hard_cpu_cap_verified'] is not False
                or accounting['whole_turn_cpu_accounting_verified'] is not False):
            raise RuntimeError('invalid or unbound retained CPU accounting')
        sample_rows = [strict_json(p.read_bytes()) for p in samples]
        if any(row['unit'] != terminal['unit'] or row['return_code'] != 0 for row in sample_rows):
            raise RuntimeError('CPU sample identity or query failed')
        try:
            final_properties = parse_properties(sample_rows[-1]['stdout'])
        except ValueError as error:
            raise RuntimeError('invalid final CPU sample') from error
        quiescent = (final_properties['TasksCurrent'] == '0' or
                     (final_properties['TasksCurrent'] == '[not set]' and final_properties['ControlGroup'] == ''))
        if (final_properties['CPUUsageNSec'] != final_cpu or not quiescent
                or not (final_properties['SubState'] == 'exited' or final_properties['ActiveState'] == 'failed')):
            raise RuntimeError('final CPU value lacks matching exited/quiescent service')
        if (ordinal == 0 and final_cpu >= budget['cumulative_nanoseconds']) or (ordinal == 1 and final_cpu < budget['cumulative_nanoseconds']):
            raise RuntimeError('CPU disposition differs from registered threshold')
        if ordinal == 0:
            if (terminal['status'] != 'RETURNED'
                    or terminal['namespace_lifecycle']['disposition'] != 'PAYLOAD_EXIT_VERIFIED'
                    or terminal['namespace_lifecycle']['payload_exit_verified'] is not True
                    or terminal['result'] != {'return_code': 0, 'stdout': '%n ${HOME} $$ αβ\n', 'stderr': ''}):
                raise RuntimeError('successful computation lacks exact result or verified lifecycle')
        elif (terminal['status'] != 'TECHNICAL_FAILURE' or terminal['result'] is not None
              or terminal['execution_audit']['reason'] != 'CUMULATIVE_CPU_LIMIT'):
            raise RuntimeError('CPU cutoff computation lacks null technical disposition')
        spent += final_cpu
        records.append({'terminal_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'intent_sha256': hashlib.sha256(intent_path.read_bytes()).hexdigest(),
                        'namespace_status_sha256': status_hash, 'status': terminal['status'],
                        'unit_absent': True, 'limits_match_configuration': True, 'cpu_accounting': accounting,
                        'cpu_sample_sha256': [hashlib.sha256(p.read_bytes()).hexdigest() for p in samples],
                        'payload_exit_verified': terminal.get('namespace_lifecycle', {}).get('payload_exit_verified', False)})
    return records


def verify_ledger_records(events: Path, configuration: dict, execution_records: list[dict]) -> dict:
    """Read-only audit of retained transactions; never instantiate/adopt a live ledger."""
    from types import SimpleNamespace
    from evidence_calibration_computation_cpu_ledger_v2 import ComputationCpuLedger
    try:
        identity = configuration['identity']['workspace_sha256']
        session = strict_json((events / 'session.intent.json').read_bytes())
        if (session['schema'] != 'crane-local-mcp-session/v5-development'
                or session['workspace_sha256'] != identity
                or session['method_id'] != configuration['identity']['method_id']
                or session['cpu_budget'] != configuration['cpu_budget']
                or session['computation_cpu_limit'] != configuration['computation_cpu_limit']):
            raise ValueError('session CPU binding mismatch')
        ledger = events / 'cpu-ledger'
        intent = strict_json((ledger / 'ledger.intent.json').read_bytes())
        source = ROOT / 'analysis/evidence_calibration_computation_cpu_ledger_v2.py'
        if (intent['schema'] != 'crane-computation-cpu-ledger-intent/v2-development'
                or intent['workspace_sha256'] != identity
                or intent['limit'] != configuration['computation_cpu_limit']
                or intent['per_call'] != configuration['cpu_budget']
                or intent['ledger_sha256'] != hashlib.sha256(source.read_bytes()).hexdigest()
                or intent['scope'] != 'COMPUTATION_SERVICE_TREES_ONLY'
                or intent['hard_cpu_cap_verified'] is not False
                or intent['whole_turn_cpu_accounting_verified'] is not False
                or intent['existing_ledgers_may_be_adopted'] is not False):
            raise ValueError('ledger source/configuration/scope mismatch')
        reservations = sorted(ledger.glob('reservation-*.intent.json'))
        settlements = sorted(ledger.glob('reservation-*.result.json'))
        tools = sorted(events.glob('tool-*.result.json'))
        if len(reservations) != 2 or len(settlements) != 2 or len(tools) != 5 or len(execution_records) != 2:
            raise ValueError('unexpected retained ledger or tool transaction count')
        spent = 0
        charged_events = []
        for ordinal, (reservation_path, settlement_path) in enumerate(zip(reservations, settlements), 1):
            if (reservation_path.name != f'reservation-{ordinal:08d}.intent.json'
                    or settlement_path.name != f'reservation-{ordinal:08d}.result.json'):
                raise ValueError('reservation sequence gap')
            reservation = strict_json(reservation_path.read_bytes())
            settlement = strict_json(settlement_path.read_bytes())
            event = reservation['event_id']
            tool_intent = strict_json((events / (event + '.intent.json')).read_bytes())
            tool_terminal = strict_json((events / (event + '.result.json')).read_bytes())
            request = tool_intent['request']
            remaining = configuration['computation_cpu_limit']['total_nanoseconds'] - spent
            budget = dict(configuration['cpu_budget'])
            budget['cumulative_nanoseconds'] = min(remaining, budget['cumulative_nanoseconds'])
            if (reservation['schema'] != 'crane-computation-cpu-reservation/v2-development'
                    or reservation['ordinal'] != ordinal
                    or reservation['workspace_sha256'] != identity
                    or reservation['execution_directory'] != str((events / (event + '.execution')).resolve())
                    or reservation['spent_before_nanoseconds'] != spent
                    or reservation['remaining_before_nanoseconds'] != remaining
                    or reservation['effective_cpu_budget'] != budget
                    or reservation['tool_request_sha256'] != canonical_sha256(request)
                    or tool_intent['request_sha256'] != canonical_sha256(request)
                    or tool_terminal['request'] != request
                    or request['workspace_sha256'] != identity or request['event_id'] != event
                    or request['name'] != COMPUTE or request['cpu_budget'] != configuration['cpu_budget']):
                raise ValueError('reservation does not match request or remaining total')
            # Reuse the strict raw-counter validator with only its immutable identity input.
            # It reads records; no admission, settlement, directory creation or adoption occurs.
            cpu, hashes = ComputationCpuLedger._verified_consumption(SimpleNamespace(workspace_sha256=identity), reservation)
            expected = {'schema': 'crane-computation-cpu-settlement/v2-development',
                'event_id': event, 'ordinal': ordinal, 'reservation': reservation,
                'status': 'CHARGED_ACTUAL_SERVICE_CPU', 'actual_cpu_nanoseconds': cpu,
                'spent_before_nanoseconds': spent, 'spent_after_nanoseconds': spent + cpu,
                'unclamped_overshoot_nanoseconds': max(0, cpu - budget['cumulative_nanoseconds']),
                'evidence_hashes': hashes, 'error': None}
            if (settlement != expected or tool_terminal['cpu_ledger_settlement'] != settlement
                    or cpu != execution_records[ordinal-1]['cpu_accounting']['final_cpu_nanoseconds']
                    or hashes['execution_terminal_sha256'] != execution_records[ordinal-1]['terminal_sha256']):
                raise ValueError('settlement does not match verified actual CPU or retained evidence')
            spent += cpu
            charged_events.append(event)
        if [p.stem.removesuffix('.result') for p in tools[1:3]] != charged_events:
            raise ValueError('fixed computation order mismatch')
        if spent < configuration['computation_cpu_limit']['total_nanoseconds']:
            raise ValueError('registered CPU total was not exhausted')
        denied = strict_json(tools[3].read_bytes())
        denied_event = denied['request']['event_id']
        read = strict_json(tools[4].read_bytes())
        snapshot = {'spent_nanoseconds': spent, 'settled_known_cpu_nanoseconds': spent,
            'remaining_nanoseconds': 0, 'unknown_accounting': False, 'pending_event': None,
            'limit': configuration['computation_cpu_limit'], 'scope': 'COMPUTATION_SERVICE_TREES_ONLY'}
        if (denied['status'] != 'TECHNICAL_FAILURE' or denied['result'] is not None
                or 'EXHAUSTED' not in denied['error'] or denied['cpu_ledger_settlement'] is not None
                or denied['request']['cpu_ledger_before'] != snapshot
                or (events / (denied_event + '.execution')).exists()
                or read['status'] != 'RETURNED' or read['request']['name'] != READ
                or read['request']['cpu_ledger_before'] != snapshot
                or read['result']['text'] != 'synthetic visible αβ'):
            raise ValueError('post-exhaustion admission/read records mismatch')
        return {'status': 'PASS_READ_ONLY_RETAINED_LEDGER_AUDIT', 'snapshot_after_fixed_calls': snapshot,
                'settlement_sha256': [hashlib.sha256(p.read_bytes()).hexdigest() for p in settlements],
                'session_intent_sha256': hashlib.sha256((events / 'session.intent.json').read_bytes()).hexdigest(),
                'ledger_intent_sha256': hashlib.sha256((ledger / 'ledger.intent.json').read_bytes()).hexdigest(),
                'ledger_adopted': False}
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError('retained computation CPU ledger verification failed') from error


def verify_owner_binding(configuration: dict) -> dict:
    """Read-only ownership validation; pending after client termination stays pending."""
    try:
        scope = configuration['execution_scope']
        registry = Path(configuration['scope_registry'])
        row = strict_json((registry / 'registry.intent.json').read_bytes())
        if row != {'schema': 'crane-condition-session-registry/v1-development',
            'campaign_id': scope['campaign_id'], 'plan_sha256': configuration['plan_sha256'],
            'scope': 'ONE_MCP_V5_SESSION_PER_REGISTERED_CONDITION_METHOD', 'model_execution_authorized': False}:
            raise ValueError('registry binding mismatch')
        owner = registry / canonical_sha256(scope)
        sources = [ROOT / 'analysis' / name for name in [
            'evidence_calibration_condition_session.py', 'evidence_calibration_mcp_stdio_v5.py',
            'evidence_calibration_tool_broker_v7.py', 'evidence_calibration_computation_cpu_ledger_v2.py',
            'evidence_calibration_local_tool_sandbox_v10.py']]
        expected = {'schema': 'crane-condition-session-owner/v1-development', 'execution_scope': scope,
            'plan_sha256': configuration['plan_sha256'], 'configuration_sha256': canonical_sha256(configuration),
            'records': str(Path(configuration['records']).resolve()),
            'workspace_sha256': configuration['identity']['workspace_sha256'],
            'computation_cpu_limit': configuration['computation_cpu_limit'], 'cpu_budget': configuration['cpu_budget'],
            'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'terminal_record_pending': True, 'model_execution_authorized': False}
        intent = owner / 'session-owner.intent.json'
        if strict_json(intent.read_bytes()) != expected:
            raise ValueError('owner scope/configuration/source mismatch')
        result = {'status': 'PENDING_OR_UNKNOWN_NO_RESTART',
            'owner_intent_sha256': hashlib.sha256(intent.read_bytes()).hexdigest(),
            'owner_terminal_sha256': None, 'ledger_adopted': False}
        terminal = owner / 'session-owner.result.json'
        if terminal.exists():
            retained = strict_json(terminal.read_bytes())
            session_path = Path(configuration['records']) / 'session.result.json'
            session = strict_json(session_path.read_bytes())
            if (retained['status'] != 'SESSION_TERMINAL_RETAIN_NO_RESTART'
                    or retained['session_terminal_status'] != session['status']
                    or retained['session_terminal_sha256'] != hashlib.sha256(session_path.read_bytes()).hexdigest()
                    or retained['computation_cpu_ledger'] != session['computation_cpu_ledger']
                    or retained['model_execution_authorized'] is not False):
                raise ValueError('owner terminal mismatch')
            result.update(status=retained['status'], owner_terminal_sha256=hashlib.sha256(terminal.read_bytes()).hexdigest())
        return result
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise RuntimeError('retained condition owner verification failed') from error


def verify_replacement_denial(configuration: dict, directory: Path) -> dict:
    """One predeclared denied constructor probe, no study request or second client."""
    from copy import deepcopy
    changed = deepcopy(configuration)
    changed['records'] = str(directory / 'forbidden-replacement-events')
    changed['computation_cpu_limit']['total_nanoseconds'] = 5_000_000_000
    path = directory / 'denied-constructor-configuration.json'
    write_once(path, changed)
    completed = subprocess.run([sys.executable, str(ROOT / 'analysis/evidence_calibration_condition_session.py'),
        '--configuration', str(path)], input=b'', capture_output=True, timeout=5)
    (directory / 'denied-constructor-stdout.bin').write_bytes(completed.stdout)
    (directory / 'denied-constructor-stderr.bin').write_bytes(completed.stderr)
    if (completed.returncode == 0 or completed.stdout != b''
            or b'condition session already reserved' not in completed.stderr
            or Path(changed['records']).exists()):
        raise RuntimeError('condition replacement constructor was not denied before session creation')
    return {'status': 'DENIED_BEFORE_SESSION_CREATION', 'return_code': completed.returncode,
        'stdout_bytes': len(completed.stdout), 'stderr_sha256': hashlib.sha256(completed.stderr).hexdigest(),
        'probe_is_model_or_study_retry': False, 'second_installed_client_launched': False}


def observe(method: str, directory: Path) -> dict:
    if method not in {'B0', 'B1', 'B2', 'B3', 'B4'}:
        raise ValueError('unknown method')
    # Raw app-server framing may include host instructions/paths. Keep it out of the repository.
    if directory.exists() or Path('/tmp') not in directory.resolve().parents:
        raise ValueError('fresh /tmp observation directory required; never adopt retained sessions')
    directory.mkdir(parents=True)
    workspace = directory / 'job'
    workspace.mkdir()
    (workspace / 'visible.txt').write_text('synthetic visible αβ')
    identity = {'method_id': method, 'inventory': inventory(workspace)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    configuration = {'workspace': str(workspace), 'identity': identity, 'records': str(directory / 'events'),
        'limits': {'wall_seconds': 2, 'cpu_seconds_per_process': 1,
                   'address_space_bytes_per_process': 256 * 1024**2, 'combined_output_bytes': 1024},
        'tree_limits': {'memory_bytes': 64 * 1024**2, 'tasks': 16, 'cpu_rate_percent': 100},
        'scratch_limits': {'temporary_bytes': 1024**2, 'shared_memory_bytes': 1024**2},
        'cpu_budget': {'cumulative_nanoseconds': 300_000_000, 'poll_milliseconds': 20, 'query_timeout_milliseconds': 250},
        'computation_cpu_limit': {'total_nanoseconds': 310_000_000},
        'max_calls': 5, 'max_messages': 50, 'max_request_bytes': 65536}
    from evidence_calibration_condition_session import create_registry
    configuration.update(scope_registry=str(directory / 'scope-registry'),
        execution_scope={'campaign_id': 'synthetic-installed-owner', 'episode_id': 'synthetic-one',
                         'condition_id': 'E0', 'method_id': method},
        plan_sha256=canonical_sha256({'schema': 'fixed-offline-owner-observation/v1',
            'method_id': method, 'flow': 'read_literal_cutoff_denied_compute_read',
            'model_calls_authorized': False}))
    create_registry(Path(configuration['scope_registry']), configuration['execution_scope']['campaign_id'],
                    configuration['plan_sha256'])
    config = directory / 'configuration.json'
    config.write_text(json.dumps(configuration))
    argv = command(config, workspace, method)
    write_once(directory / 'observer.intent.json', {'command': argv,
        'configuration_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
        'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'model_calls_authorized': False})
    client = None
    result = {'schema': 'crane-offline-app-server-mcp-observation/v6-development',
              'method_id': method, 'status': 'INCOMPLETE', 'model_call_attempted': False}
    try:
        client = OfflineClient(argv)
        client.request('initialize', {'clientInfo': {'name': 'crane-offline-observer', 'version': '1'},
                                     'capabilities': {'experimentalApi': True}})
        client.initialized()
        thread = client.request('thread/start', {'cwd': str(workspace), 'ephemeral': True,
            'model': 'gpt-6-sol', 'sandbox': 'read-only', 'approvalPolicy': 'never'})
        thread_id = thread['thread']['id']
        status = client.request('mcpServerStatus/list', {'threadId': thread_id, 'serverName': SERVER,
                                                        'detail': 'toolsAndAuthOnly', 'limit': 10})
        if status.get('nextCursor') is not None or len(status['data']) != 1:
            raise RuntimeError('unexpected server inventory or pagination')
        server = status['data'][0]
        expected = {row['name']: row for row in tool_definitions(method)}
        if (server['name'] != SERVER or server['runtimeStatus'] != 'connected'
                or server['toolsError'] is not None or server['tools'] != expected):
            raise RuntimeError('installed-client MCP inventory does not match assigned tools')
        result = {'schema': 'crane-offline-app-server-mcp-observation/v6-development', 'method_id': method,
            'status': 'INCOMPLETE', 'tools': server['tools'], 'tools_sha256': canonical_sha256(server['tools']),
            'runtime_status': server['runtimeStatus'], 'provider_request_tools_verified': False,
            'model_call_attempted': False, 'ephemeral_thread_started': True,
            'network_namespace_used': True, 'full_harness_confinement_verified': False}
        if expected:
            read = client.request('mcpServer/tool/call', {'threadId': thread_id, 'server': SERVER,
                'tool': READ, 'arguments': {'path': 'visible.txt', 'offset': 0, 'length': None}})
            computed = client.request('mcpServer/tool/call', {'threadId': thread_id, 'server': SERVER,
                'tool': COMPUTE, 'arguments': {'code': "print('%n ${HOME} $$ αβ')"}})
            if (read['isError'] or read['structuredContent']['result']['text'] != 'synthetic visible αβ'
                    or computed['isError'] or computed['structuredContent']['result']['stdout'] != '%n ${HOME} $$ αβ\n'):
                raise RuntimeError('installed-client read or arithmetic route failed')
            result['synthetic_read_and_computation_passed'] = True
            cutoff = client.request('mcpServer/tool/call', {'threadId': thread_id, 'server': SERVER,
                'tool': COMPUTE, 'arguments': {'code': "import subprocess,sys\ncs=[subprocess.Popen([sys.executable,'-c','while True: pass'],start_new_session=True) for _ in range(4)]\nprint('partial',flush=True)\nfor child in cs:child.wait()"}})
            if (not cutoff['isError'] or cutoff['structuredContent'].get('status') != 'TECHNICAL_FAILURE'
                    or cutoff['structuredContent'].get('result') is not None
                    or cutoff['structuredContent'].get('error') != 'CUMULATIVE_CPU_LIMIT'
                    or 'base64' in json.dumps(cutoff) or 'partial' in json.dumps(cutoff)):
                raise RuntimeError('installed-client failure rendering differs from registered null result')
            denied = client.request('mcpServer/tool/call', {'threadId': thread_id, 'server': SERVER,
                'tool': COMPUTE, 'arguments': {'code': 'print("must not execute")'}})
            full_read = client.request('mcpServer/tool/call', {'threadId': thread_id, 'server': SERVER,
                'tool': READ, 'arguments': {'path': 'visible.txt', 'offset': 0, 'length': None}})
            if (not denied['isError'] or denied['structuredContent'].get('result') is not None
                    or 'EXHAUSTED' not in denied['structuredContent'].get('error', '')
                    or full_read['isError'] or full_read['structuredContent']['result']['text'] != 'synthetic visible αβ'):
                raise RuntimeError('installed-client exhausted CPU admission or subsequent full read failed')
            for reply in [computed, cutoff, denied, full_read]:
                if 'ledger' in json.dumps(reply) or json.loads(reply['content'][0]['text']) != reply['structuredContent']:
                    raise RuntimeError('operator accounting exposed or duplicate content rendering differs')
            result['bounded_tool_failure_passed'] = True
            result['exhausted_compute_denied_read_preserved'] = True
            result['execution_records'] = verify_execution_records(directory / 'events', configuration)
            result['computation_cpu_ledger'] = verify_ledger_records(directory / 'events', configuration, result['execution_records'])
        else:
            result['synthetic_read_and_computation_passed'] = None
            result['bounded_tool_failure_passed'] = None
            result['exhausted_compute_denied_read_preserved'] = None
        result['condition_owner'] = verify_owner_binding(configuration)
        result['status'] = 'PASS'
    except BaseException as error:
        write_once(directory / 'observer.error.json', {'error_type': type(error).__name__, 'error': str(error)})
        if result is not None:
            result['error_type'] = type(error).__name__
            result['status'] = 'FAILED_NO_RETRY'
        raise
    finally:
        cleanup_error = None
        try:
            if client is not None:
                client.close()
            if result.get('status') == 'PASS':
                # Cleanup can kill the coordinator. Retain its true pending/terminal state.
                result['condition_owner_after_cleanup'] = verify_owner_binding(configuration)
                result['replacement_constructor'] = verify_replacement_denial(configuration, directory)
        except BaseException as error:
            cleanup_error = error
            result['status'] = 'FAILED_NO_RETRY'
            result['error_type'] = type(error).__name__
            write_once(directory / 'observer.cleanup-error.json',
                {'error_type': type(error).__name__, 'error': str(error)})
        raw_buffers = client.raw if client is not None else {'stdout': bytearray(), 'stderr': bytearray()}
        for name, raw in raw_buffers.items():
            (directory / f'app-server-{name}.bin').write_bytes(raw)
        (directory / 'request-log.json').write_text(json.dumps(client.requests if client is not None else [], ensure_ascii=True, indent=2))
        if result is not None:
            result.update(request_methods=[row['method'] for row in client.requests] if client is not None else [],
                cleanup=client.cleanup if client is not None else None, process_exit_code=client.process.returncode if client is not None else None,
                stdout_bytes=len(raw_buffers['stdout']), stderr_bytes=len(raw_buffers['stderr']),
                stdout_sha256=hashlib.sha256(raw_buffers['stdout']).hexdigest(),
                stderr_sha256=hashlib.sha256(raw_buffers['stderr']).hexdigest())
            (directory / 'sanitized-result.json').write_text(json.dumps(result, indent=2)+'\n')
        if cleanup_error is not None:
            raise cleanup_error
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['B0', 'B1', 'B2', 'B3', 'B4'], required=True)
    parser.add_argument('--raw-directory', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(observe(args.method, args.raw_directory), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
