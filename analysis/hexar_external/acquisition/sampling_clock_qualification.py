"""Native development sampling/clock/extraction compatibility qualification.

Reads technical setup and raw measurements, never method outputs or labels.
Actual ROS deserialization runs offline in the captured TIAGo image.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys


def check_timestamps(values, strict=False):
    if not values or any(type(v) is not int or v < 0 for v in values):
        return False
    return all(a < b if strict else a <= b for a, b in zip(values, values[1:]))


def native(root, bank, run_path):
    sys.path.insert(0, str(bank))
    import sampling
    import extract_events
    import extract_motion_v2
    import yaml
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    run = json.loads(run_path.read_text())
    rows = []
    for receipt in run['episodes']:
        folder = root / receipt['episode_id']
        episode = json.loads((folder / 'episode.json').read_text())
        expected_sampling = json.loads(json.dumps(sampling.sample(receipt['seed_hidden'])))
        observed_sampling = episode['sampling_hidden']
        metadata = yaml.safe_load((folder / 'raw/metadata.yaml').read_text())['rosbag2_bagfile_information']
        expected = {row['topic_metadata']['name']: row for row in metadata['topics_with_message_count']}
        counts, types, receipt_times, clock_times, odometry_times = {}, {}, [], [], []
        clock_type = get_message('rosgraph_msgs/msg/Clock')
        odometry_type = get_message('nav_msgs/msg/Odometry')
        sql_integrity = []
        for name in metadata['relative_file_paths']:
            path = folder / 'raw' / name
            # Fixed released recording layout; never admit path traversal.
            path.resolve().relative_to((folder / 'raw').resolve())
            connection = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
            try:
                sql_integrity.append(connection.execute('PRAGMA integrity_check').fetchone()[0] == 'ok')
                topics = dict((uid, (topic, kind)) for uid, topic, kind in
                              connection.execute('SELECT id,name,type FROM topics'))
                for uid, timestamp, blob in connection.execute('SELECT topic_id,timestamp,data FROM messages ORDER BY id'):
                    topic, kind = topics[uid]
                    receipt_times.append(timestamp)
                    counts[topic] = counts.get(topic, 0) + 1
                    if topic in types and types[topic] != kind:
                        raise ValueError('message type changed between bag segments')
                    types[topic] = kind
                    if topic == '/clock':
                        if kind != 'rosgraph_msgs/msg/Clock':
                            raise ValueError('unexpected clock schema')
                        stamp = deserialize_message(blob, clock_type).clock
                        clock_times.append(stamp.sec * 10**9 + stamp.nanosec)
                    elif topic == '/mobile_base_controller/odom':
                        if kind != 'nav_msgs/msg/Odometry':
                            raise ValueError('unexpected odometry schema')
                        stamp = deserialize_message(blob, odometry_type).header.stamp
                        odometry_times.append(stamp.sec * 10**9 + stamp.nanosec)
            finally:
                connection.close()
        count_match = (set(counts) <= set(expected)
                       and all(counts.get(topic, 0) == row['message_count'] for topic, row in expected.items()))
        type_match = all(types.get(topic) == row['topic_metadata']['type']
                         for topic, row in expected.items() if row['message_count'])
        original_events = json.loads((folder / 'events_development.json').read_text())
        original_motion = json.loads((folder / 'motion_events_v3.json').read_text())
        extracted_events = extract_events.extract(folder / 'raw')
        extracted_motion, _ = extract_motion_v2.extract(folder / 'raw')
        checks = dict(
            applied_sampling_matches_seed_and_captured_map=observed_sampling == expected_sampling,
            metadata_counts_match_actual_raw_messages=count_match,
            metadata_types_match_actual_raw_messages=type_match,
            sqlite_integrity=bool(sql_integrity) and all(sql_integrity),
            receipt_clock_monotone=check_timestamps(receipt_times),
            native_simulated_clock_monotone=check_timestamps(clock_times),
            odometry_clock_strictly_increases=check_timestamps(odometry_times, strict=True),
            odometry_within_observed_simulated_clock_range=bool(clock_times) and bool(odometry_times)
                and min(clock_times) <= min(odometry_times) <= max(odometry_times) <= max(clock_times),
            historical_interface_extraction_reproduces=original_events == extracted_events,
            motion_action_extraction_reproduces=original_motion == extracted_motion)
        rows.append(dict(episode_id=receipt['episode_id'], checks=checks,
                         passed=all(checks.values()), raw_message_count=len(receipt_times),
                         clock_messages=len(clock_times), odometry_messages=len(odometry_times),
                         navigation_success_used_as_exclusion=False,
                         clock_conversion_inferred=False))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native', action='store_true')
    parser.add_argument('--root', type=Path)
    parser.add_argument('--bank', type=Path)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.native:
        print(json.dumps(native(args.root, args.bank, args.run)))
        return
    if args.output is None:
        parser.error('host mode requires --output')
    from .technical_batch_candidate import ROOT, digest, verify_capture
    from ..confirmatory_v1.journal import exclusive_json
    run = json.loads(args.run.read_text())
    if run.get('phase') != 'development_only' or run.get('status') != 'DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED':
        raise ValueError('closed development run required')
    if len({r['execution_source_bank_sha256'] for r in run['episodes']}) != 1:
        raise ValueError('one captured sampler/extractor source bank required')
    for receipt in run['episodes']:
        verify_capture(ROOT, receipt, run['image_id'])
    base = ROOT / 'manifests/hexar_external/acquisition'
    bank = base / 'source_banks' / run['episodes'][0]['execution_source_bank_sha256']
    command = ['docker', 'run', '--rm', '--network', 'none', '--memory', '5g',
               '-v', str(base) + ':/input:ro', '-v', str(bank) + ':/bank:ro',
               '-v', str(Path(__file__).resolve()) + ':/qualify.py:ro',
               '--entrypoint', 'bash', run['image_id'], '-lc',
               'source /ws/install/setup.bash; python3 /qualify.py --native '
               '--root /input --bank /bank --run /input/' + args.run.name]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=True)
    rows = json.loads(result.stdout)
    sources = [Path(__file__), args.run]
    sources.extend(base / r['episode_id'] / name for r in run['episodes']
                   for name in ('episode.json', 'motion_extraction_v3.json'))
    report = dict(schema='hexar-native-sampling-clock-qualification/v1', phase='development_only',
        status='NATIVE_SAMPLING_CLOCK_EXTRACTION_SCOPE_PASSED_NOT_FINAL_ADMISSION'
            if all(row['passed'] for row in rows) else 'FAILED_RETAINED',
        episodes=rows, image_id=run['image_id'],
        executed_source_bank_sha256=run['episodes'][0]['execution_source_bank_sha256'],
        source_hashes={str(p.resolve().relative_to(ROOT)): digest(p) for p in sources},
        confirmatory_N=0, alpha_consumed=0, method_or_judge_calls=0,
        full_acquisition_qualified=False,
        scope='Raw count/type/clock, seeded sampling and native extraction compatibility. '
              'Does not establish a final adapter, reserve/failure-rate guarantee or scientific freeze.')
    exclusive_json(args.output, report)
    print(report['status'])


if __name__ == '__main__':
    main()
