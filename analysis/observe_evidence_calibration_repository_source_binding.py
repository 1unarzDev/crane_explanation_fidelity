#!/usr/bin/env python3
"""Fixed non-model development checks of static repository source binding."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess

import evidence_calibration_condition_session_v5 as previous
import evidence_calibration_condition_session_v6 as candidate
from evidence_calibration_io import canonical_sha256
from evidence_calibration_mcp_stdio_v5 import encode, strict_json
from observe_evidence_calibration_cgroup_limits import write_once
from stage_evidence_calibration_workspace import inventory


ROOT = Path(__file__).resolve().parents[1]
METHODS = ('B0', 'B1', 'B2', 'B3', 'B4')


def configuration(directory, method, registry, plan, campaign):
    directory.mkdir(parents=True, exist_ok=False)
    workspace = directory / 'workspace'
    workspace.mkdir()
    (workspace / 'visible.txt').write_text('synthetic visible αβ')
    identity = {'method_id': method, 'inventory': inventory(workspace)}
    identity['workspace_sha256'] = canonical_sha256(identity)
    return {'workspace': str(workspace), 'identity': identity,
        'records': str(directory / 'events'),
        'limits': {'wall_seconds': 2, 'cpu_seconds_per_process': 1,
            'address_space_bytes_per_process': 256 * 1024**2, 'combined_output_bytes': 1024},
        'tree_limits': {'memory_bytes': 64 * 1024**2, 'tasks': 16, 'cpu_rate_percent': 100},
        'scratch_limits': {'temporary_bytes': 1024**2, 'shared_memory_bytes': 1024**2},
        'cpu_budget': {'cumulative_nanoseconds': 300_000_000,
            'poll_milliseconds': 20, 'query_timeout_milliseconds': 250},
        'computation_cpu_limit': {'total_nanoseconds': 310_000_000},
        'max_calls': 5, 'max_messages': 50, 'max_request_bytes': 65536,
        'response_byte_limit': {'total_bytes': 65536},
        'scope_registry': str(registry), 'execution_plan': str(plan), 'plan_sha256': '0'*64,
        'execution_scope': {'campaign_id': campaign, 'episode_id': 'synthetic-one',
            'condition_id': 'E0', 'method_id': method}}


def bind(configurations):
    path = Path(configurations[0]['execution_plan'])
    write_once(path, candidate.build_plan(configurations))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    candidate.create_registry(Path(configurations[0]['scope_registry']), path, digest)
    for row in configurations:
        row['plan_sha256'] = digest


def request(method, params=None, identifier=None):
    row = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
    if identifier is not None:
        row['id'] = identifier
    return encode(row)


def observe(directory: Path):
    if not __debug__:
        raise ValueError('fixed observation checks require assertions enabled')
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    sources = candidate.source_hashes()
    write_once(directory / 'observation.intent.json', {
        'observer_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'candidate_source_sha256': sources, 'assignments': list(METHODS),
        'unchanged_constructor_probes': 5,
        'copied_source_drift_probes': ['evidence_calibration_io.py', 'evidence_calibration_namespace_wrapper.py'],
        'model_calls_authorized': False, 'retries_authorized': False})
    rows = [configuration(directory / method, method, directory / 'registry',
        directory / 'plan.json', 'synthetic-source-binding') for method in METHODS]
    bind(rows)
    results, services, drifts = [], [], []
    try:
        for row in rows:
            method = row['identity']['method_id']
            wire = request('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                'clientInfo': {'name': 'synthetic-source-check', 'version': '1'}}, 0)
            wire += request('notifications/initialized') + request('tools/list', identifier=1)
            if method in ('B2', 'B3', 'B4'):
                wire += request('tools/call', {'name': 'compute_visible_python',
                    'arguments': {'code': 'print(42)'}}, 2)
            sink = io.BytesIO()
            assert candidate.serve(row, io.BytesIO(wire), sink) == 0
            write_once(directory / method / 'configuration.json', row)
            (directory / method / 'response.bin').write_bytes(sink.getvalue())
            replies = [strict_json(line) for line in sink.getvalue().splitlines()]
            names = sorted(tool['name'] for tool in replies[1]['result']['tools'])
            assert names == ([] if method in ('B0', 'B1') else ['compute_visible_python', 'read_staged_file'])
            if names:
                assert replies[-1]['result']['structuredContent']['result']['stdout'] == '42\n'
            owner = Path(row['scope_registry']) / canonical_sha256(row['execution_scope'])
            terminal = strict_json((owner / 'session-owner.result.json').read_bytes())
            assert terminal['status'] == 'SESSION_TERMINAL_RETAIN_NO_RESTART'
            assert terminal['response_egress']['settled_flushed_bytes'] == len(sink.getvalue())
            try:
                candidate.claim(row)
            except ValueError as error:
                assert 'already reserved' in str(error)
            else:
                raise AssertionError('unchanged scope admitted twice')
            results.append({'method_id': method, 'tools': names,
                'response_bytes': len(sink.getvalue()), 'owner_status': terminal['status'],
                'restart_denied': True})
        for dependency in ('evidence_calibration_io.py', 'evidence_calibration_namespace_wrapper.py'):
            case = directory / ('drift-' + dependency.removesuffix('.py'))
            code = case / 'copied-source'
            code.mkdir(parents=True)
            for name in set(sources) | set(previous.source_hashes()):
                (code / name).write_bytes((ROOT / 'analysis' / name).read_bytes())
            old_file, new_file = previous.__file__, candidate.__file__
            try:
                previous.__file__ = str(code / Path(old_file).name)
                candidate.__file__ = str(code / Path(new_file).name)
                baseline = previous.source_hashes()
                row = configuration(case / 'B2', 'B2', case / 'registry', case / 'plan.json', 'synthetic-drift')
                bind([row])
                (code / dependency).write_bytes((code / dependency).read_bytes() + b'\n# synthetic copied-source drift\n')
                assert previous.source_hashes() == baseline
                try:
                    candidate.claim(row)
                except ValueError as error:
                    assert 'source' in str(error)
                    drifts.append({'dependency': dependency, 'previous_binding_changed': False,
                        'candidate_admission': 'DENIED_BEFORE_OWNERSHIP', 'error': str(error)})
                else:
                    raise AssertionError('copied-source drift admitted')
                assert not list((case / 'registry').glob('*/session-owner.intent.json'))
                assert not Path(row['records']).exists()
            finally:
                previous.__file__, candidate.__file__ = old_file, new_file
        for path in directory.glob('B*/events/tool-*.execution/terminal.json'):
            terminal = strict_json(path.read_bytes())
            unit = terminal['unit']
            check = subprocess.run(['systemctl', '--user', 'show', unit, '--property=LoadState', '--value'],
                capture_output=True, text=True, timeout=5, check=True)
            assert check.stdout.strip() == 'not-found'
            services.append({'unit': unit, 'load_state': check.stdout.strip(),
                'actual_service_cpu_nanoseconds': terminal['cpu_accounting']['final_cpu_nanoseconds']})
        result = {'status': 'PASS_STATIC_REPOSITORY_BINDING_AND_FIXED_LOCAL_FLOWS',
            'bound_source_count': len(sources), 'results': results, 'copied_source_drifts': drifts,
            'services': services, 'model_calls_attempted': False,
            'installed_client_integration_verified': False, 'scientific_runtime_adopted': False}
        write_once(directory / 'observation.result.json', result)
        return result
    except BaseException as error:
        write_once(directory / 'observation.error.json', {'status': 'FAILED_NO_RETRY',
            'error_type': type(error).__name__, 'error': str(error)})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    print(json.dumps(observe(parser.parse_args().directory), indent=2))
