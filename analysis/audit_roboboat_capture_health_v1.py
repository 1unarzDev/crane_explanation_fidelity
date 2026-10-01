#!/usr/bin/env python3
"""Read-only freshness replay; not a substitute for full capture admission gates."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ZERO_COUNTERS = ('staleObservations', 'failedObservations', 'staleActions',
                 'rejectedActions', 'crossEpisodeActions', 'loggedErrors',
                 'loggedExceptions', 'invalidWaterSearches')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(worker_dir):
    worker_dir = Path(worker_dir)
    result_path = worker_dir / 'result.json'
    trace_path = worker_dir / 'result.validation.jsonl'
    worker = json.loads(result_path.read_text())
    rows = [json.loads(line) for line in trace_path.read_text().splitlines() if line.strip()]
    failures = []
    if worker.get('valid') is not True:
        failures.append('worker_valid_not_true')
    for key in ZERO_COUNTERS:
        if worker.get(key) != 0:
            failures.append(key + '_not_zero')
    if not rows:
        failures.append('empty_validation_trace')
    if len(rows) != worker.get('validationSamplesCaptured'):
        failures.append('validation_stream_count_mismatch')
    first_events = {}
    last_time = -1.0
    last_counts = {'staleObservations': 0, 'failedObservations': 0}
    maximum_age = -1
    for index, row in enumerate(rows):
        time = row.get('simulatedSeconds')
        if not isinstance(time, (int, float)) or not math.isfinite(time) or time < last_time:
            failures.append('invalid_trace_timestamp')
            continue
        age = row.get('observationQueueAgeTicks')
        if not isinstance(age, int) or age < -1:
            failures.append('invalid_trace_queue_age')
        else:
            maximum_age = max(maximum_age, age)
        for key in last_counts:
            count = row.get(key)
            if not isinstance(count, int) or count < last_counts[key]:
                failures.append('invalid_trace_counter_' + key)
                continue
            if count > last_counts[key]:
                if key not in first_events:
                    first_events[key] = {'previous_sample_seconds': last_time if index else None,
                                         'first_positive_sample_seconds': time,
                                         'count': count, 'queue_age_ticks': age}
                failures.append('trace_' + key + '_not_zero')
            last_counts[key] = count
        last_time = time
    for key, count in last_counts.items():
        if rows and count != worker.get(key):
            failures.append('trace_terminal_counter_mismatch_' + key)
    if maximum_age != worker.get('maximumObservationQueueAgeTicks'):
        failures.append('trace_maximum_age_mismatch')
    timing = worker.get('actionTiming', {})
    for key in ('maximumSourceToApplicationTicks', 'maximumReceiveToApplicationTicks'):
        value = timing.get(key)
        if not isinstance(value, (int, float)) or not 0 <= value <= 10:
            failures.append('action_lag_invalid_' + key)
    return {'schema': 'roboboat-capture-health-v1', 'worker_directory': str(worker_dir),
            'scope': 'worker freshness and validation-stream integrity only; full admission remains required',
            'bindings': {'result_sha256': sha256(result_path), 'trace_sha256': sha256(trace_path)},
            'healthy': not failures, 'failures': sorted(set(failures)),
            'validation_samples': len(rows), 'maximum_observation_queue_age_ticks': maximum_age,
            'first_counter_events': first_events,
            'terminal_counters': {key: worker.get(key) for key in ZERO_COUNTERS},
            'action_timing': timing,
            'runtime': {key: worker.get(key) for key in ('timeScale', 'screenWidth', 'screenHeight',
                        'meanGpuFrameMilliseconds', 'realTimeFactor', 'enabledSensorCameras')},
            'depth_dimensions': {key: worker.get('depthCamera', {}).get(key) for key in ('width', 'height')}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('worker_directories', nargs='+', type=Path)
    args = parser.parse_args()
    reports = []
    for directory in args.worker_directories:
        try:
            reports.append(audit(directory))
        except (OSError, ValueError, TypeError, KeyError) as error:
            reports.append({'worker_directory': str(directory), 'healthy': False,
                            'failures': ['unreadable_or_malformed_capture'], 'error': str(error)})
    print(json.dumps({'reports': reports}, indent=2, allow_nan=False))
    return 0 if all(report['healthy'] for report in reports) else 1


if __name__ == '__main__':
    raise SystemExit(main())
