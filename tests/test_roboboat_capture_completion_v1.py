import json
from pathlib import Path
import subprocess
import sys

import pytest
from roboboat_capture_completion_v1 import publish_exclusive, run

TOKEN = 'a' * 64


def child(tmp_path, *, status='succeeded', observed=8, code=0, run_id='run'):
    summary = tmp_path / 'summary.json'
    data = {'schema': 'crane-nav2-controller-fixture-v1', 'run_id': run_id,
            'episode_id': 'episode', 'status': status,
            'postResultSecondsRequested': 8, 'btTerminalDrainSecondsRequested': .5,
            'postResultSecondsObserved': observed}
    script = tmp_path / 'child.py'
    # Real subprocess: writes then exits, so the publisher must wait for the exit.
    script.write_text('import json,sys\nfrom pathlib import Path\n'
                      'Path(sys.argv[1]).write_text(sys.argv[2])\n'
                      'sys.exit(int(sys.argv[3]))\n')
    return [sys.executable, str(script), str(summary), json.dumps(data), str(code)], summary


@pytest.mark.parametrize('status,observed', [('succeeded', 8), ('aborted', 8),
                                           ('canceled', 8), ('timeout', None)])
def test_successful_fixture_exit_retains_all_dispositions(tmp_path, status, observed):
    command, summary = child(tmp_path, status=status, observed=observed)
    marker = tmp_path / 'complete'
    receipt = run(command, summary, marker, TOKEN, 'run', 'episode', 8, .5)
    assert marker.read_bytes() == (TOKEN + '\n').encode()
    assert receipt['status'] == status and receipt['fixture_exit_code'] == 0
    assert json.loads((tmp_path / 'complete.receipt.json').read_text()) == receipt


@pytest.mark.parametrize('changes', [{'observed': 7.99}, {'observed': None},
                                   {'observed': float('nan')}, {'run_id': 'old'},
                                   {'status': 'executing'}, {'code': 3}])
def test_invalid_or_failed_fixture_never_publishes(tmp_path, changes):
    command, summary = child(tmp_path, **changes)
    marker = tmp_path / 'complete'
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        run(command, summary, marker, TOKEN, 'run', 'episode', 8, .5)
    assert not marker.exists() and not marker.with_name(marker.name + '.receipt.json').exists()


def test_existing_destination_cannot_be_replaced(tmp_path):
    path = tmp_path / 'marker'
    publish_exclusive(path, b'original')
    with pytest.raises(FileExistsError): publish_exclusive(path, b'replacement')
    assert path.read_bytes() == b'original'
    command, summary = child(tmp_path)
    with pytest.raises(FileExistsError):
        run(command, summary, path, TOKEN, 'run', 'episode', 8, .5)
    assert not summary.exists()


def test_marker_is_published_after_process_exit(tmp_path):
    summary = tmp_path / 'summary.json'; marker = tmp_path / 'complete'
    command, _ = child(tmp_path)
    script = Path(command[1])
    script.write_text(script.read_text().replace('sys.exit(int(sys.argv[3]))',
        'assert not Path(sys.argv[1]).with_name("complete").exists()\n'
        'Path(sys.argv[1]).with_name("process-footer").write_text("closed")\n'
        'sys.exit(int(sys.argv[3]))'))
    run(command, summary, marker, TOKEN, 'run', 'episode', 8, .5)
    assert (tmp_path / 'process-footer').read_text() == 'closed' and marker.exists()
