import hashlib
import json
from audit_roboboat_capability_trace_v2 import audit, challenge_command
from probe_roboboat_isolated_baseline_capability_v1 import INPUT, MARKER


def test_actual_started_completed_lifecycle_and_shell_wrapper_preserve_permission_failures():
    body = {'input_sha256': hashlib.sha256(INPUT).hexdigest(), 'yaml_import': True,
            'subprocess_child': None, 'scratch_roundtrip': None,
            'permission_errors': [{'operation': 'subprocess_child', 'error_type': 'PermissionError'}]}
    item = {'type': 'command_execution', 'id': 'item_1', 'command': "/usr/bin/bash -lc 'python3 synthetic_challenge.py'"}
    receipt = {'status': 'valid', 'events': [{'type': 'item.started', 'item': item},
               {'type': 'item.completed', 'item': {**item, 'status': 'completed', 'exit_code': 0,
                 'aggregated_output': MARKER+json.dumps(body)}}]}
    result = audit(receipt)
    assert result['trace_identity_verified'] and result['unique_command_count'] == 1
    assert result['capabilities']['yaml_import'] and not result['all_capabilities_verified']
    assert result['permission_errors_retained'] == body['permission_errors']
    assert not audit({'status': 'valid', 'parsed_final': body})['trace_identity_verified']


def test_shell_extra_commands_or_fake_echo_do_not_qualify():
    assert challenge_command('python3 synthetic_challenge.py')
    for command in ('echo python3 synthetic_challenge.py', "bash -lc 'python3 synthetic_challenge.py; true'", 'python3 evil.py'):
        assert not challenge_command(command)
