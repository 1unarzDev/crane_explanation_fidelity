"""Deterministic raw extraction/reproduction for closed development attempts.

No provider calls. Failures remain explicit rows; original raw bytes are read
only. Derived files use exclusive creation and are never silently rewritten.
"""
import argparse
import json
from pathlib import Path
import sys
import tempfile


def write_derived(path, value):
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError('existing derived artifact differs from raw reproduction: ' + str(path))
        return
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def native(root, bank, run_path):
    sys.path.insert(0, str(bank))
    import extract_events
    import extract_motion_v2
    import sampling_clock_qualification
    import clock_envelope_review
    run = json.loads(run_path.read_text())
    if run.get('phase') != 'development_only':
        raise ValueError('development raw extraction only')
    rows = []
    for receipt in run['episodes']:
        row = dict(episode_id=receipt['episode_id'], status='UNRESOLVED_TECHNICAL_REVIEW', error=None)
        try:
            folder = root / receipt['episode_id']
            folder.resolve().relative_to(root.resolve())
            events = extract_events.extract(folder / 'raw')
            motion, provenance = extract_motion_v2.extract(folder / 'raw')
            import hashlib
            provenance['normalized_events_sha256'] = hashlib.sha256((json.dumps(motion, indent=2)+'\n').encode()).hexdigest()
            write_derived(folder / 'events_development.json', events)
            write_derived(folder / 'motion_events_v3.json', motion)
            write_derived(folder / 'motion_extraction_v3.json', provenance)
            with tempfile.TemporaryDirectory() as directory:
                mini = Path(directory) / 'single_closed_attempt.json'
                mini.write_text(json.dumps(dict(run, episodes=[receipt])))
                checks = sampling_clock_qualification.native(root, bank, mini)[0]
            envelope = clock_envelope_review.native(folder)
            full_stream = checks['checks'].pop('odometry_within_observed_simulated_clock_range')
            checks['checks'].update(
                action_boundaries_within_clock_envelope=envelope['action_boundaries_within_clock_envelope'],
                task_window_odometry_within_clock_envelope=envelope['task_window_odometry_outside_envelope_n'] == 0)
            checks.update(full_stream_clock_envelope_passed=full_stream,
                          clock_envelope_diagnostic=envelope,
                          passed=all(checks['checks'].values()))
            row.update(status='CLOSED_NATIVE_REVIEW', review=checks)
        except Exception as exc:
            row['error'] = type(exc).__name__ + ': ' + str(exc)
        rows.append(row)
    return rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--bank', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(native(args.root, args.bank, args.run)))
