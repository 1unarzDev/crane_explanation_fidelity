#!/usr/bin/env python3
"""Local MCP stdio candidate; no provider client, authentication or model execution."""
from __future__ import annotations

import argparse
import base64
from dataclasses import asdict
import hashlib
import json
import math
from pathlib import Path
import sys

from evidence_calibration_local_tool_sandbox_v2 import Limits, ExecutionFailure
from evidence_calibration_tool_broker_v5 import ToolBroker
from evidence_calibration_local_tool_sandbox_v10 import TreeLimits, ScratchLimits, CpuBudget
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once

PROTOCOL = '2025-06-18'


def encode(value: dict) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8') + b'\n'


def strict_json(raw: bytes):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite JSON number')
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('nonfinite JSON number')
        return number
    parsed = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                        parse_constant=invalid, parse_float=finite_float)
    def unicode_strings(value):
        if isinstance(value, str):
            value.encode('utf-8')  # Reject escaped lone surrogates too.
        elif isinstance(value, dict):
            for key, item in value.items():
                unicode_strings(key)
                unicode_strings(item)
        elif isinstance(value, list):
            for item in value:
                unicode_strings(item)
    unicode_strings(parsed)
    return parsed


class ProtocolError(ValueError):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


class Server:
    def __init__(self, workspace: Path, identity: dict, records: Path, *, limits: Limits, tree_limits: TreeLimits, scratch_limits: ScratchLimits, cpu_budget: CpuBudget,
                 max_calls: int, max_messages: int, max_request_bytes: int):
        if type(max_messages) is not int or not 1 <= max_messages <= 10000:
            raise ValueError('explicit message budget required (1–10000)')
        if type(max_request_bytes) is not int or not 1024 <= max_request_bytes <= 16 * 1024**2:
            raise ValueError('explicit request byte budget required (1 KiB–16 MiB)')
        # Broker checks workspace identity, limits, method and fresh namespace before creating it.
        self.broker = ToolBroker(workspace, identity, records, max_calls=max_calls, limits=limits, tree_limits=tree_limits, scratch_limits=scratch_limits, cpu_budget=cpu_budget)
        self.records = records
        self.max_messages, self.max_request_bytes = max_messages, max_request_bytes
        self.ordinal, self.state, self.call_ids = 0, 'NEW', set()
        self.finished = False
        self.descriptor = {'schema': 'crane-local-mcp-session/v4-development',
            'protocol_version': PROTOCOL, 'method_id': identity['method_id'],
            'workspace_sha256': identity['workspace_sha256'], 'limits': asdict(limits), 'tree_limits': asdict(tree_limits), 'scratch_limits': asdict(scratch_limits), 'cpu_budget': asdict(cpu_budget),
            'max_calls': max_calls, 'max_messages': max_messages, 'max_request_bytes': max_request_bytes,
            'tools': self.broker.definitions, 'provider_connected': False, 'model_call_attempted': False}
        _write_once(records / 'session.intent.json', self.descriptor)

    def dispatch(self, request: dict, ordinal: int):
        method, params = request['method'], request.get('params', {})
        if not isinstance(params, dict):
            raise ProtocolError(-32602, 'params must be an object')
        if method == 'initialize':
            if self.state != 'NEW' or 'id' not in request:
                raise ProtocolError(-32600, 'single initialize request required')
            if (set(params) - {'protocolVersion', 'capabilities', 'clientInfo', '_meta'}
                    or not isinstance(params.get('protocolVersion'), str)
                    or not isinstance(params.get('capabilities'), dict)
                    or not isinstance(params.get('clientInfo'), dict)
                    or any(not isinstance(params['clientInfo'].get(key), str) for key in ('name', 'version'))):
                raise ProtocolError(-32602, 'invalid initialization parameters')
            self.state = 'INITIALIZING'
            return {'protocolVersion': PROTOCOL, 'capabilities': {'tools': {'listChanged': False}},
                    'serverInfo': {'name': 'crane-local-tools', 'version': '4-development'}}
        if method == 'notifications/initialized':
            if self.state != 'INITIALIZING' or 'id' in request or set(params) - {'_meta'}:
                raise ProtocolError(-32600, 'initialized notification required after initialize')
            self.state = 'READY'
            return None
        if method == 'ping':
            return {}
        if self.state != 'READY':
            raise ProtocolError(-32000, 'session not initialized')
        if method == 'tools/list':
            if 'id' not in request or set(params) - {'_meta'}:
                raise ProtocolError(-32602, 'tool list requires a request without cursor')
            return {'tools': self.broker.definitions}
        if method == 'tools/call':
            if ('id' not in request or set(params) - {'name', 'arguments', '_meta'}
                    or not isinstance(params.get('name'), str) or not isinstance(params.get('arguments'), dict)):
                raise ProtocolError(-32602, 'tool name and arguments required')
            # Repeated calculations under distinct IDs are permitted by the broker budget;
            # a repeated call identity is never executed again in this session.
            key = (type(request['id']).__name__, request['id'])
            if key in self.call_ids:
                raise ProtocolError(-32600, 'retained tool call identity; no replay')
            self.call_ids.add(key)
            if params['name'] not in {row['name'] for row in self.broker.definitions}:
                raise ProtocolError(-32602, 'tool not permitted for assigned method')
            if self.broker.calls >= self.broker.max_calls:
                raise ProtocolError(-32000, 'tool call budget exhausted')
            event = f'tool-{ordinal:08d}'
            try:
                record = self.broker.call(event, params['name'], params['arguments'])
                payload = {'status': record['status'], 'result': record['result']}
                failed = record['status'] != 'RETURNED'
            except (ValueError, OSError, ExecutionFailure) as error:
                # Terminal broker records contain bounded partial bytes where applicable.
                # Do not send those audit bytes back as substitute evidence or tool output.
                terminal_path = self.records / (event + '.result.json')
                if not terminal_path.is_file():
                    raise  # Retention failed: keep unknown intent and stop the server.
                terminal_record = strict_json(terminal_path.read_bytes())
                if terminal_record.get('status') != 'TECHNICAL_FAILURE':
                    raise RuntimeError('broker failure lacks matching terminal disposition') from error
                payload = {'status': 'TECHNICAL_FAILURE', 'result': None,
                           'error_type': type(error).__name__, 'error': str(error)}
                failed = True
            return {'content': [{'type': 'text', 'text': encode(payload).decode().rstrip('\n')}],
                    'structuredContent': payload, 'isError': failed}
        raise ProtocolError(-32601, 'method not available')

    def handle(self, raw: bytes) -> bytes | None:
        if self.finished:
            raise ValueError('session terminal; no replay')
        if self.ordinal >= self.max_messages:
            raise ValueError('session message budget exhausted')
        self.ordinal += 1
        ordinal = self.ordinal
        intent = self.records / f'rpc-{ordinal:08d}.intent.json'
        terminal = self.records / f'rpc-{ordinal:08d}.result.json'
        _write_once(intent, {'request_base64': base64.b64encode(raw).decode('ascii'),
                            'request_sha256': hashlib.sha256(raw).hexdigest(),
                            'terminal_record_pending': True})
        request, response, status, rpc_id, notification = None, None, 'PROTOCOL_ERROR', None, False
        fatal = len(raw) > self.max_request_bytes or not raw.endswith(b'\n')
        try:
            if fatal:
                raise ProtocolError(-32000, 'request framing or byte limit failure; session terminated')
            try:
                request = strict_json(raw)
            except (ValueError, UnicodeError, RecursionError) as error:
                raise ProtocolError(-32700, 'invalid JSON') from error
            if (not isinstance(request, dict) or request.get('jsonrpc') != '2.0'
                    or set(request) - {'jsonrpc', 'id', 'method', 'params'}
                    or not isinstance(request.get('method'), str)):
                raise ProtocolError(-32600, 'invalid JSON-RPC request')
            if 'id' in request and type(request['id']) not in (str, int):
                raise ProtocolError(-32600, 'request ID must be a string or integer')
            rpc_id, notification = request.get('id'), 'id' not in request
            result = self.dispatch(request, ordinal)
            if not notification:
                response = {'jsonrpc': '2.0', 'id': rpc_id, 'result': result}
            status = 'NOTIFICATION_RETAINED' if notification else 'RESPONSE_RETAINED'
        except ProtocolError as error:
            if not notification:
                response = {'jsonrpc': '2.0', 'id': rpc_id, 'error': {'code': error.code, 'message': str(error)}}
        wire = encode(response) if response is not None else None
        _write_once(terminal, {'status': status, 'response': response,
            'response_sha256': hashlib.sha256(wire).hexdigest() if wire is not None else None,
            'session_terminated': fatal})
        if fatal:
            self.finish('REQUEST_FRAMING_FAILURE')
        return wire

    def finish(self, status: str):
        if not self.finished:
            _write_once(self.records / 'session.result.json', {'schema': 'crane-local-mcp-terminal/v4-development',
                'status': status, 'messages_received': self.ordinal, 'tool_calls': self.broker.calls,
                'provider_connected': False, 'model_call_attempted': False})
            self.finished = True
            self.terminal_status = status

    def serve(self, source, sink):
        try:
            while not self.finished and self.ordinal < self.max_messages:
                raw = source.readline(self.max_request_bytes + 1)
                if not raw:
                    self.finish('STDIN_EOF')
                    return
                wire = self.handle(raw)
                if wire is not None:
                    sink.write(wire)
                    sink.flush()
            self.finish('MESSAGE_BUDGET_EXHAUSTED')
        except BaseException:
            # A wire/broker intent without a terminal record remains unknown; never adopt/replay.
            self.finish('LOCAL_SERVER_FAILURE')
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configuration', type=Path, required=True)
    args = parser.parse_args()
    config = strict_json(args.configuration.read_bytes())
    expected = {'workspace', 'identity', 'records', 'limits', 'tree_limits', 'scratch_limits', 'cpu_budget', 'max_calls', 'max_messages', 'max_request_bytes'}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError('exact coordinator configuration fields required')
    server = Server(Path(config['workspace']), config['identity'], Path(config['records']),
        limits=Limits(**config['limits']), tree_limits=TreeLimits(**config['tree_limits']), scratch_limits=ScratchLimits(**config['scratch_limits']), cpu_budget=CpuBudget(**config['cpu_budget']), max_calls=config['max_calls'],
        max_messages=config['max_messages'], max_request_bytes=config['max_request_bytes'])
    server.serve(sys.stdin.buffer, sys.stdout.buffer)
    return 0 if server.terminal_status == 'STDIN_EOF' else 65


if __name__ == '__main__':
    sys.exit(main())
