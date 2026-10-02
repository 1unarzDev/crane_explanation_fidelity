"""Separate task-window clock qualification; preserves failed whole-stream audit."""
import argparse
import json
from pathlib import Path
import subprocess

from .technical_batch_candidate import ROOT, digest, verify_capture
from ..confirmatory_v1.journal import exclusive_json


def window_checks(row):
    return dict(
        action_boundaries_within_clock_envelope=row['action_boundaries_within_clock_envelope'] is True,
        at_least_two_task_window_odometry_samples=type(row['task_window_odometry_n']) is int
            and row['task_window_odometry_n'] >= 2,
        task_window_odometry_within_clock_envelope=type(row['task_window_odometry_outside_envelope_n']) is int
            and row['task_window_odometry_outside_envelope_n'] == 0)


def build(run_path, prior_path):
    from . import sampling_clock_qualification as original
    from . import clock_envelope_review as diagnostic
    run = json.loads(run_path.read_text())
    prior = json.loads(prior_path.read_text())
    if run.get('phase') != 'development_only' or run.get('status') != 'DEVELOPMENT_RUNS_RECORDED_UNQUALIFIED':
        raise ValueError('closed development run required')
    if len({r['execution_source_bank_sha256'] for r in run['episodes']}) != 1:
        raise ValueError('one captured sampler/extractor bank required')
    for receipt in run['episodes']:
        verify_capture(ROOT, receipt, run['image_id'])
    base = ROOT / 'manifests/hexar_external/acquisition'
    bank = base / 'source_banks' / run['episodes'][0]['execution_source_bank_sha256']
    original_path, diagnostic_path = Path(original.__file__), Path(diagnostic.__file__)
    command = ['docker', 'run', '--rm', '--network', 'none', '--memory', '5g',
               '-v', str(base) + ':/input:ro', '-v', str(bank) + ':/bank:ro',
               '-v', str(original_path) + ':/native_check.py:ro',
               '--entrypoint', 'bash', run['image_id'], '-lc',
               'source /ws/install/setup.bash; python3 /native_check.py --native '
               '--root /input --bank /bank --run "$1"', 'native-check', '/input/' + run_path.name]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=True)
    rows = json.loads(result.stdout)
    if prior.get('image_id') != run['image_id'] or prior.get('episodes') != rows:
        raise ValueError('original native failed audit does not reproduce')
    for row in rows:
        command = ['docker', 'run', '--rm', '--network', 'none',
                   '-v', str(base) + ':/input:ro', '-v', str(diagnostic_path) + ':/review.py:ro',
                   '--entrypoint', 'bash', run['image_id'], '-lc',
                   'source /ws/install/setup.bash; python3 /review.py --folder "$1"',
                   'clock-review', '/input/' + row['episode_id']]
        result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=True)
        envelope = json.loads(result.stdout)
        checks = dict(row['checks'])
        full_stream = checks.pop('odometry_within_observed_simulated_clock_range')
        checks.update(window_checks(envelope))
        row.update(checks=checks, passed=all(checks.values()),
                   full_stream_clock_envelope_passed=full_stream, clock_envelope_diagnostic=envelope)
    declaration = ROOT / 'docs/hexar_external/confirmatory_v1/NATIVE_CLOCK_VALIDITY.md'
    sources = [Path(__file__), original_path, diagnostic_path, declaration, run_path, prior_path]
    return dict(schema='hexar-native-sampling-clock-qualification/v2', phase='development_only',
        status='NATIVE_TASK_WINDOW_SCOPE_PASSED_NOT_FINAL_ADMISSION'
            if all(row['passed'] for row in rows) else 'FAILED_RETAINED',
        episodes=rows, image_id=run['image_id'], prior_failed_report_reproduced=True,
        executed_source_bank_sha256=run['episodes'][0]['execution_source_bank_sha256'],
        source_hashes={str(p.resolve().relative_to(ROOT)): digest(p) for p in sources},
        confirmatory_N=0, alpha_consumed=0, method_or_judge_calls=0,
        full_acquisition_qualified=False,
        scope='Candidate seeded sampling/raw metadata/clock/extraction and task-window envelope checks; '
              'full-stream diagnostics retained. No final acquisition admission or invalid-rate guarantee.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--prior', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = build(args.run, args.prior)
    exclusive_json(args.output, value)
    print(value['status'])
