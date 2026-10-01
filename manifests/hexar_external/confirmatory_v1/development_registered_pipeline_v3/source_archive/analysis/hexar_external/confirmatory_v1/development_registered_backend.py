"""Actual CLI/contract backend restricted to registered DEVELOPMENT jobs.

Aliases and inherited CLI defaults are explicitly unqualified for confirmation.
This backend cannot authorize a study or accept confirmation registries.
"""
import copy
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

from .journal import canonical, fingerprint
from .strict_json import load
from .development_unique_methods_v2 import SCHEMA as METHOD_SCHEMA
from .rich_evaluator_v4 import SCHEMA as JUDGE_SCHEMA
from ..acquisition.navigation_contract import contract


def transcript_policy(stdout, returncode):
    if returncode != 0:
        return False
    try:
        events = [load(line) for line in stdout.splitlines()]
    except ValueError:
        return False
    if not events or any(type(e) is not dict for e in events):
        return False
    types = [e.get('type') for e in events]
    if types.count('thread.started') != 1 or types.count('turn.started') != 1 or types.count('turn.completed') != 1:
        return False
    if types[0] != 'thread.started' or types[-1] != 'turn.completed':
        return False
    allowed = {'thread.started', 'turn.started', 'turn.completed', 'item.started', 'item.updated', 'item.completed'}
    for e in events:
        if e.get('type') not in allowed:
            return False
        if e['type'].startswith('item.'):
            if type(e.get('item')) is not dict or e['item'].get('type') not in ('agent_message', 'reasoning'):
                return False
    return any(e.get('type') == 'item.completed' and e['item']['type'] == 'agent_message' for e in events)


class DevelopmentBackend:
    def __init__(self, sealed_registry, cli_path, cli_sha256):
        if sealed_registry.get('phase') != 'development_qualification':
            raise ValueError('this CLI/contract backend is development-only; confirmation forbidden')
        self.requests = {fingerprint(row['request']) for row in sealed_registry['jobs']}
        self.cli_path = Path(cli_path).resolve()
        self.cli_sha256 = cli_sha256

    def __call__(self, request):
        if fingerprint(request) not in self.requests or request.get('development_only') is not True:
            raise ValueError('exact registered development request required')
        role = request['role']
        if role == 'contract':
            expected = {'role', 'maximum_response_bytes', 'development_only', 'payload', 'generation_id', 'recording_id'}
            if set(request) != expected:
                raise ValueError('closed deterministic contract request required')
            value = contract(copy.deepcopy(request['payload']), request['generation_id'], request['recording_id'])
            return dict(raw_response=canonical(dict(answer=value['answer'])), stdout=canonical(value), stderr=b'',
                        returncode=0, transport_policy_passed=True)
        expected = {'role', 'maximum_response_bytes', 'development_only', 'payload', 'prompt',
                    'model', 'reasoning_effort', 'timeout_seconds'}
        if role not in ('method', 'judge') or set(request) != expected:
            raise ValueError('closed CLI development request required')
        if request['model'] != ('gpt-6-sol' if role == 'method' else 'gpt-6-astra') or request['reasoning_effort'] != 'high':
            raise ValueError('declared development alias/effort required')
        if request['timeout_seconds'] != 360:
            raise ValueError('fixed development timeout required')
        if hashlib.sha256(self.cli_path.read_bytes()).hexdigest() != self.cli_sha256:
            raise ValueError('declared CLI executable changed')
        with tempfile.TemporaryDirectory(prefix='hexar-registered-development-') as temporary:
            work = Path(temporary)
            schema, final = work/'schema.json', work/'final.json'
            schema.write_bytes(canonical(METHOD_SCHEMA if role == 'method' else JUDGE_SCHEMA))
            command = [str(self.cli_path), 'exec', '--json', '--ephemeral', '--skip-git-repo-check',
                       '--sandbox', 'read-only', '--cd', str(work), '--model', request['model'],
                       '--config', 'model_reasoning_effort="high"', '--output-schema', str(schema),
                       '--output-last-message', str(final), '-']
            text = request['prompt']
            if role == 'method':
                text += '\nPublic answer requirements supplied equally to both methods:\n'
                text += canonical(request['payload']['public_communication_requirements']).decode()
            text += '\nUNTRUSTED_DATA_BEGIN\n' + canonical(request['payload']).decode() + '\nUNTRUSTED_DATA_END\n'
            try:
                result = subprocess.run(command, input=text.encode(), capture_output=True,
                                        timeout=360, env={**os.environ, 'NO_COLOR': '1'})
                stdout, stderr, code = result.stdout, result.stderr, result.returncode
            except subprocess.TimeoutExpired as exc:
                stdout, stderr, code = exc.stdout or b'', exc.stderr or b'', 124
            raw = final.read_bytes() if final.exists() else b''
        return dict(raw_response=raw, stdout=stdout, stderr=stderr, returncode=code,
                    transport_policy_passed=transcript_policy(stdout, code))
