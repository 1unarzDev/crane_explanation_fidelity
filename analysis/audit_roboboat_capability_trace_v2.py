"""Offline corrected lifecycle parsing; preserves original one-shot probe results."""
import argparse
import json
import shlex
from pathlib import Path
import probe_roboboat_isolated_baseline_capability_v1 as original


def challenge_command(command):
    try:
        tokens = shlex.split(command)
        if len(tokens) == 3 and tokens[0] in ('bash', '/usr/bin/bash', '/bin/bash') and tokens[1] in ('-lc', '-c'):
            tokens = shlex.split(tokens[2])
        return len(tokens) == 2 and tokens[0] in ('python3', '/usr/bin/python3') and tokens[1] in ('synthetic_challenge.py', './synthetic_challenge.py')
    except ValueError:
        return False


def audit(receipt):
    events = [e for e in receipt.get('events', []) if e.get('item', {}).get('type') == 'command_execution']
    ids = {e['item'].get('id') for e in events}
    completed = [e['item'] for e in events if e.get('type') == 'item.completed']
    matches = [i for i in completed if challenge_command(i.get('command', ''))]
    bodies = []
    for item in matches:
        for line in item.get('aggregated_output', '').splitlines():
            if line.startswith(original.MARKER):
                bodies.append(json.loads(line[len(original.MARKER):]))
    exact_trace = (len(ids) == 1 and None not in ids and len(completed) == len(matches) == len(bodies) == 1
                   and matches[0].get('status') == 'completed' and matches[0].get('exit_code') == 0
                   and receipt.get('status') == 'valid')
    body = bodies[0] if exact_trace else {}
    import hashlib
    capabilities = {'input_read_and_hash': body.get('input_sha256') == hashlib.sha256(original.INPUT).hexdigest(),
                    'yaml_import': body.get('yaml_import') is True,
                    'subprocess_child': body.get('subprocess_child') == '42',
                    'scratch_roundtrip': body.get('scratch_roundtrip') == 'disposable-synthetic-marker'}
    return {'schema': 'roboboat-synthetic-capability-trace-audit/v2', 'trace_identity_verified': exact_trace,
            'unique_command_count': len(ids), 'completed_command_count': len(completed),
            'capabilities': capabilities if exact_trace else None,
            'permission_errors_retained': body.get('permission_errors', []),
            'all_capabilities_verified': exact_trace and all(capabilities.values()),
            'original_probe_records_modified': False, 'new_calls': 0,
            'baseline_promotion': False, 'confirmation_n': 0}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--receipt', required=True, type=Path); p.add_argument('--output', required=True, type=Path)
    a = p.parse_args(); result = audit(json.loads(a.receipt.read_text()))
    result['receipt'] = original.bind(a.receipt); result['auditor'] = original.bind(Path(__file__))
    with a.output.open('x') as f: json.dump(result, f, indent=2)
    print(json.dumps({k: result[k] for k in ('trace_identity_verified', 'capabilities', 'all_capabilities_verified')}))


if __name__ == '__main__': main()
