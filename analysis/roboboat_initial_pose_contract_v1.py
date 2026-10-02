"""Candidate varied-start launch/receipt contract; not platform qualification.

Only read the exact worker log bound by its collector. A receipt authenticates
an immediate initialization readback, not subsequent odometry or navigation.
"""
import hashlib
import json
import math
from pathlib import Path

OPTION = '--crane-roboboat-start-pose'
PREFIX = 'CRANE_ROBOBOAT_INITIAL_POSE '
UNITS = {'frame': 'odom', 'x': 'm', 'y': 'm', 'yaw': 'rad'}


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('finite numeric pose component required')
    return float(value)


def requested_pose(row):
    if row.get('initial_pose_units') != UNITS or row.get('initial_pose_cli_option') != OPTION:
        raise ValueError('explicit odom/metre/radian start-pose contract required')
    pose = row.get('initial_pose_request')
    if not isinstance(pose, dict) or set(pose) != {'x', 'y', 'yaw'}:
        raise ValueError('exact x/y/yaw initial request required')
    result = tuple(finite(pose[k]) for k in ('x', 'y', 'yaw'))
    if abs(result[2]) > math.pi:
        raise ValueError('canonical start yaw required')
    # Unity consumes System.Single; reject values outside that representable
    # range before starting a player. Readback separately checks its precision.
    if any(abs(v) > 3.4028234663852886e38 for v in result):
        raise ValueError('start pose exceeds Unity float range')
    return result


def launch_args(row, existing=()):
    """Return an argv list, avoiding shell interpolation and duplicate overrides."""
    existing = list(existing)
    if any(arg == OPTION or arg.startswith(OPTION + '=') for arg in existing):
        raise ValueError('existing start override forbidden')
    return existing + [OPTION, ','.join(format(v, '.17g') for v in requested_pose(row))]


def assess(row, worker_log):
    path = Path(worker_log).resolve()
    raw = path.read_bytes()
    receipts = []
    issues = []
    for line in raw.decode('utf-8', errors='replace').splitlines():
        if line.startswith(PREFIX):
            try:
                receipts.append(json.loads(line[len(PREFIX):]))
            except (ValueError, TypeError):
                issues.append('malformed initialization receipt')
    x, y, yaw = requested_pose(row)
    checks = {'exactly_one_receipt': len(receipts) == 1 and not issues}
    if len(receipts) == 1:
        receipt = receipts[0]
        try:
            request = receipt['requestedRosXYAndYaw']
            position = receipt['observedUnityPosition']
            rotation = receipt['observedUnityRotation']
            actual = tuple(finite(request[k]) for k in ('x', 'y', 'z'))
            p = tuple(finite(position[k]) for k in ('x', 'y', 'z'))
            q = tuple(finite(rotation[k]) for k in ('x', 'y', 'z', 'w'))
            expected_q = (0., math.sin((math.pi / 2 - yaw) / 2), 0.,
                          math.cos((math.pi / 2 - yaw) / 2))
            checks.update(
                requested_pose_matches=all(abs(a-b) <= 1e-5 for a, b in zip(actual, (x, y, yaw))),
                planar_position_matches=abs(p[0] + y) <= 1e-5 and abs(p[2] - x) <= 1e-5,
                unit_rotation=abs(sum(v*v for v in q) - 1) <= 1e-5,
                rotation_matches=min(sum((a-b)**2 for a, b in zip(q, expected_q)),
                                     sum((a+b)**2 for a, b in zip(q, expected_q))) <= 1e-10,
                correct_scene=receipt['scene'] == 'Roboboat Course',
                correct_phase=receipt['phase'] == 'sceneLoaded-before-Start-and-physics',
                supported_body=receipt['bodyType'] in ('ArticulationBody', 'Rigidbody') and
                               isinstance(receipt['body'], str) and bool(receipt['body']))
        except (KeyError, ValueError, TypeError):
            issues.append('incomplete/nonfinite initialization receipt')
            checks['receipt_shape_complete'] = False
    return {'schema': 'roboboat-initial-pose-contract-audit/v1',
            'row_id': row['id'], 'requested_pose': dict(row['initial_pose_request']),
            'worker_log': {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest()},
            'checks': checks, 'issues': issues, 'receipt_count': len(receipts),
            'initialization_readback_pass': bool(checks) and all(checks.values()) and not issues,
            'navigation_qualified': False, 'physical_equivalence_qualified': False,
            'platform_qualified': False, 'independent_n_added': 0}
