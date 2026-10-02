#!/usr/bin/env python3
"""Bounded ordered blind extraction; stop before independent parent review/support."""
import argparse
import subprocess
import sys
import time
from pathlib import Path

from audit_release import ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release-pid', type=int, required=True)
    args = parser.parse_args()
    process = Path('/proc') / str(args.release_pid)
    expected = b'analysis/hexar_external/after_v3_compatibility.py'
    while process.exists():
        try:
            command = (process / 'cmdline').read_bytes()
        except FileNotFoundError:
            break
        if not command:
            break
        if expected not in command.split(b'\0'):
            raise RuntimeError('Release PID changed identity; refusing concurrent extraction.')
        time.sleep(10)
    for stage in ('project', 'extract', 'assemble'):
        print('START_BLIND_EXTRACTION', stage, flush=True)
        subprocess.run([sys.executable, str(ROOT / 'analysis/hexar_external/extract_v3.py'),
                        '--stage', stage], cwd=ROOT, check=True)
    print('BLIND_CANDIDATE_READY_INDEPENDENT_PARENT_REVIEW_REQUIRED_NO_SUPPORT_YET', flush=True)


if __name__ == '__main__':
    main()
