"""Mechanical namespace lifecycle audit; no semantic/model failure attribution."""
from __future__ import annotations

import json

INITIAL_FIELDS = {'child-pid', 'user-namespace', 'cgroup-namespace', 'ipc-namespace',
                  'mnt-namespace', 'net-namespace', 'pid-namespace', 'uts-namespace'}


def audit(raw: bytes, launcher_return_code: int) -> dict:
    if (not isinstance(raw, bytes) or len(raw) > 8192 or type(launcher_return_code) is not int
            or not -128 <= launcher_return_code <= 255):
        raise ValueError('invalid bounded namespace observation')
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate status key')
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('nonfinite status number')
    try:
        rows = [json.loads(line, object_pairs_hook=pairs, parse_constant=invalid)
                for line in raw.decode('utf-8').splitlines()]
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError('invalid namespace status serialization') from error
    if not rows:
        return {'disposition': 'NAMESPACE_LIFECYCLE_UNVERIFIED', 'payload_exit_verified': False,
                'records': [], 'model_failure_attributed': False}
    if (len(rows) not in {1, 2} or not isinstance(rows[0], dict)
            or 'child-pid' not in rows[0] or set(rows[0]) - INITIAL_FIELDS
            or any(type(value) is not int or value <= 0 for value in rows[0].values())):
        raise ValueError('unrecognized namespace initial status')
    if len(rows) == 1:
        return {'disposition': 'NAMESPACE_LIFECYCLE_INCOMPLETE', 'payload_exit_verified': False,
                'records': rows, 'model_failure_attributed': False}
    exit_row = rows[1]
    if (not isinstance(exit_row, dict) or set(exit_row) != {'exit-code'}
            or type(exit_row['exit-code']) is not int or not 0 <= exit_row['exit-code'] <= 255
            or exit_row['exit-code'] != launcher_return_code):
        raise ValueError('namespace exit record missing or mismatched')
    return {'disposition': 'PAYLOAD_EXIT_VERIFIED', 'payload_exit_verified': True,
            'records': rows, 'model_failure_attributed': False}
