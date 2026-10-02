#!/usr/bin/env python3
"""Ordered descriptive release after the unchanged fresh compatibility gate."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from audit_release import ROOT
from verify_v3 import V3, qualified


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--annotation-pid', type=int, required=True)
    args = parser.parse_args()
    proc = Path('/proc') / str(args.annotation_pid)
    expected = b'analysis/hexar_external/annotate_v3.py'
    while proc.exists():
        try:
            command = (proc / 'cmdline').read_bytes()
        except FileNotFoundError:
            break
        if not command:
            break  # Completed zombie; no inference can remain in this parent.
        if expected not in command:
            raise RuntimeError('Annotation PID changed identity; refusing activation.')
        time.sleep(10)
    qualified()
    summary = json.loads((V3 / 'development/annotation/annotation_summary.json').read_text())
    if summary['n_responses'] != 54 or summary['qualified_completed'] < 0.9 * 54:
        raise RuntimeError('Unchanged fresh compatibility gate failed; retain failures.')
    print('FRESH_COMPATIBILITY_CLOSED_GATE_PASSED_ZERO_ALPHA_RELEASE', flush=True)
    subprocess.run(
        [sys.executable, str(ROOT / 'analysis/hexar_external/release_reserved_v3.py')],
        cwd=ROOT, check=True,
    )


if __name__ == '__main__':
    main()
