"""Outcome-blind raw recording integrity audit; navigation failures stay eligible."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import re
import yaml

REQUIRED = ('/clock', '/rosout', '/tf', '/scan_raw', '/mobile_base_controller/odom', '/amcl_pose', '/task_info', '/joy_priority', '/power/is_charging')

def audit(folder):
    metadata_path = folder / 'raw/metadata.yaml'
    issues = []
    counts = {}
    hashes = []
    if not metadata_path.exists():
        issues.append('missing bag metadata')
    else:
        metadata = yaml.safe_load(metadata_path.read_text())['rosbag2_bagfile_information']
        counts = {t['topic_metadata']['name']: t['message_count'] for t in metadata['topics_with_message_count']}
        for topic in REQUIRED:
            if not counts.get(topic):
                issues.append('missing required topic messages: ' + topic)
        if counts.get('/task_info', 0) < 2:
            issues.append('missing task boundary messages')
        for relative in metadata['relative_file_paths']:
            database = folder / 'raw' / relative
            if not database.exists():
                issues.append('missing bag segment: ' + relative)
                continue
            connection = sqlite3.connect('file:' + str(database) + '?mode=ro', uri=True)
            checked = connection.execute('PRAGMA integrity_check').fetchone()[0]
            if checked != 'ok':
                issues.append('sqlite integrity failure: ' + relative)
            connection.close()
            hashes.append({'path': str(database), 'sha256': hashlib.file_digest(database.open('rb'), 'sha256').hexdigest()})
    runtime = folder / 'runtime.log'
    if not runtime.exists() or 'Applied Gazebo seed:' not in runtime.read_text():
        issues.append('seed application not evidenced')
    episode_path = folder / 'episode.json'
    seed_applied_matches_plan = False
    if episode_path.exists() and runtime.exists():
        expected_seed = json.loads(episode_path.read_text())['seed_hidden']
        applied = re.findall(r'Applied Gazebo seed: (\d+)', runtime.read_text())
        seed_applied_matches_plan = applied == [str(expected_seed)]
        if not seed_applied_matches_plan:
            issues.append('applied simulator seed differs from recorded episode seed')
    else:
        issues.append('missing episode seed report')
    probe = folder / 'runtime_probe.json'
    if not probe.exists() or not json.loads(probe.read_text())['qualified']:
        issues.append('post-episode clock/sensor/lifecycle probe did not pass')
    return {'schema': 'hexar-development-technical-integrity/v1', 'phase': 'development_only',
            'bag_integrity_passed': not issues, 'seed_applied_matches_plan': seed_applied_matches_plan, 'issues': issues, 'counts': counts, 'bag_hashes': hashes,
            'family_intervention_qualified': False, 'independent_reset_qualified': False,
            'full_acquisition_qualified': False,
            'navigation_success_used_as_exclusion': False, 'semantic_outputs_inspected': False}

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('folder', type=Path)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    report = audit(args.folder)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    raise SystemExit(0 if report['bag_integrity_passed'] else 1)
