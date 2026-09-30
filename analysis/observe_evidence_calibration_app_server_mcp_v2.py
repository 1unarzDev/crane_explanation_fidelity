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
from evidence_calibration_mcp_stdio_v2 import strict_json
from observe_evidence_calibration_cgroup_limits import write_once
from evidence_calibration_tool_broker_v3 import READ, COMPUTE, tool_definitions
from stage_evidence_calibration_workspace import inventory

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
        f'mcp_servers.{SERVER}.args': [str(ROOT / 'analysis/evidence_calibration_mcp_stdio_v2.py'),
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
        'max_calls': 3, 'max_messages': 50, 'max_request_bytes': 65536}
    config = directory / 'configuration.json'
    config.write_text(json.dumps(configuration))
    argv = command(config, workspace, method)
    write_once(directory / 'observer.intent.json', {'command': argv,
        'configuration_sha256': hashlib.sha256(config.read_bytes()).hexdigest(),
        'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'model_calls_authorized': False})
    client = None
    result = {'schema': 'crane-offline-app-server-mcp-observation/v2-development',
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
        result = {'schema': 'crane-offline-app-server-mcp-observation/v2-development', 'method_id': method,
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
            overflow = client.request('mcpServer/tool/call', {'threadId': thread_id, 'server': SERVER,
                'tool': COMPUTE, 'arguments': {'code': 'print("x"*2048)'}})
            if (not overflow['isError'] or overflow['structuredContent'].get('status') != 'TECHNICAL_FAILURE'
                    or overflow['structuredContent'].get('result') is not None
                    or 'base64' in json.dumps(overflow)):
                raise RuntimeError('installed-client failure rendering differs from registered null result')
            result['bounded_tool_failure_passed'] = True
        else:
            result['synthetic_read_and_computation_passed'] = None
            result['bounded_tool_failure_passed'] = None
        result['status'] = 'PASS'
    except BaseException as error:
        write_once(directory / 'observer.error.json', {'error_type': type(error).__name__, 'error': str(error)})
        if result is not None:
            result['error_type'] = type(error).__name__
            result['status'] = 'FAILED_NO_RETRY'
        raise
    finally:
        if client is not None:
            client.close()
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
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--method', choices=['B0', 'B1', 'B2', 'B3', 'B4'], required=True)
    parser.add_argument('--raw-directory', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(observe(args.method, args.raw_directory), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
