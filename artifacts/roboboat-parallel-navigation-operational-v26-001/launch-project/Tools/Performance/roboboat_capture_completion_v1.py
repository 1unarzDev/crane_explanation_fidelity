"""Run a fixture and publish nonce completion only after successful process exit.

No navigation-outcome filtering. This is an unqualified development mechanism;
full trace/footer and owned player shutdown require operational qualification.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import tempfile


def publish_exclusive(path, data):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        # Atomic visibility, refusing replacement of any previous marker/receipt.
        os.link(name, path)
        directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        os.unlink(name)


def run(command, summary, marker, token, run_id, episode_id, post_seconds, drain_seconds):
    summary, marker = Path(summary), Path(marker)
    receipt = marker.with_name(marker.name + '.receipt.json')
    if not re.fullmatch('[a-f0-9]{64}', token):
        raise ValueError('fresh 64 lowercase hex token required')
    if not marker.is_absolute() or not summary.is_absolute():
        raise ValueError('absolute capture paths required')
    if not command or not run_id or not episode_id:
        raise ValueError('command and run/episode identities required')
    if any(not math.isfinite(v) or v < 0 for v in (post_seconds, drain_seconds)):
        raise ValueError('finite nonnegative capture durations required')
    if any(p.exists() or p.is_symlink() for p in (summary, marker, receipt)):
        raise FileExistsError('fresh capture and completion destinations required')
    subprocess.run(command, check=True)
    if summary.is_symlink():
        raise ValueError('summary symlink rejected')
    raw = summary.read_bytes()
    d = json.loads(raw)
    if d.get('schema') != 'crane-nav2-controller-fixture-v1':
        raise ValueError('unexpected fixture schema')
    if d.get('run_id') != run_id or d.get('episode_id') != episode_id:
        raise ValueError('fixture identity mismatch')
    if d.get('status') not in ('succeeded', 'aborted', 'canceled', 'timeout'):
        raise ValueError('terminal fixture disposition required')
    if d.get('postResultSecondsRequested') != post_seconds:
        raise ValueError('requested post-result duration mismatch')
    if d.get('btTerminalDrainSecondsRequested') != drain_seconds:
        raise ValueError('requested drain duration mismatch')
    observed = d.get('postResultSecondsObserved')
    if observed is None:
        if d['status'] != 'timeout':
            raise ValueError('terminal result missing capture duration')
    elif (type(observed) not in (int, float) or not math.isfinite(observed)
          or observed < max(post_seconds, drain_seconds)):
        raise ValueError('post-result capture incomplete')
    record = {'schema': 'roboboat-capture-completion/v1', 'run_id': run_id,
              'episode_id': episode_id, 'fixture_exit_code': 0,
              'summary': {'path': str(summary), 'sha256': hashlib.sha256(raw).hexdigest()},
              'status': d['status'], 'post_result_seconds': post_seconds,
              'bt_drain_seconds': drain_seconds, 'post_result_observed': observed,
              'token_sha256': hashlib.sha256(token.encode()).hexdigest(),
              'command': command, 'independent_n_added': 0,
              'full_trace_or_shutdown_qualified': False}
    publish_exclusive(receipt, (json.dumps(record, indent=2, allow_nan=False) + '\n').encode())
    publish_exclusive(marker, (token + '\n').encode())
    return record


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('summary', 'marker', 'token', 'run-id', 'episode-id'):
        p.add_argument('--' + name, required=True)
    p.add_argument('--post-seconds', required=True, type=float)
    p.add_argument('--drain-seconds', required=True, type=float)
    p.add_argument('command', nargs=argparse.REMAINDER)
    a = p.parse_args()
    command = a.command[1:] if a.command[:1] == ['--'] else a.command
    value = run(command, a.summary, a.marker, a.token, a.run_id, a.episode_id,
                a.post_seconds, a.drain_seconds)
    print(json.dumps({'status': value['status'], 'capture_complete_published': True}))
