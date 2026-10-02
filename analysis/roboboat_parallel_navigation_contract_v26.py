"""Own-stream checks for a fixed concurrent navigation operational assay."""
import math
from pathlib import Path
from roboboat_launch_mount_v24 import relative_route
from probe_roboboat_parallel_players_v20 import simultaneous_progress


def own_stream_checks(row, fixture, summary, domain, port):
    checks = {
        'own_run': fixture.get('run_id') == row['id'],
        'own_episode': fixture.get('episode_id') == row['id']+'-worker-0',
        'own_action_mode': fixture.get('actionMode') == row['action_mode'],
        'own_domain': summary.get('transport', {}).get('rosDomainId') == domain,
        'own_port': summary.get('transport', {}).get('rosTcpPort') == port,
    }
    if 'path_file' in row:
        checks['own_path_bytes'] = fixture.get('suppliedPathFileSha256') == row['path_file']['sha256']
        checks['own_mounted_path'] = fixture.get('suppliedPathFile') == str(Path('/workspace/crane_sim')/relative_route(row))
    else:
        goal = fixture.get('goal') or {}; position = goal.get('position') or {}
        checks['own_goal_frame'] = goal.get('frame_id') == 'odom'
        checks['own_goal'] = all(isinstance(value, (float, int)) and math.isfinite(value) and
            abs(value-row['goal'][axis]) < 1e-6 for axis, value in
            (('x', position.get('x')), ('y', position.get('y')), ('yaw', goal.get('yaw'))))
        checks['no_foreign_path'] = fixture.get('suppliedPathFile') is None and fixture.get('suppliedPathFileSha256') is None
    return checks


def simultaneous_navigation_progress(samples):
    # The existing distinct-window predicate checks both live identities and
    # growing validation streams; additionally require both command traces grow.
    if not simultaneous_progress(samples):
        return False
    filtered = []
    for sample in samples:
        observations = [dict(o, validation_records=o.get('action_records', 0)) for o in sample['observations']]
        filtered.append(dict(sample, observations=observations))
    return simultaneous_progress(filtered)
