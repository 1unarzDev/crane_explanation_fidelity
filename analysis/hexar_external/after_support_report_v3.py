#!/usr/bin/env python3
"""Run each registered descriptive report once after ordered support closes."""
import argparse
import subprocess
import sys
import time
from pathlib import Path

from audit_release import ROOT
from verify_v3 import V3, study


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--support-pid', type=int, required=True)
    args = parser.parse_args()
    study()
    process = Path('/proc') / str(args.support_pid)
    while process.exists():
        try:
            command = (process / 'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:
            break
        if not any(command):
            break
        if b'analysis/hexar_external/after_roles_v3.py' not in command:
            raise RuntimeError('Support PID changed identity; refusing report.')
        time.sleep(10)
    base = V3 / 'reserved'
    assert (base / 'annotation/annotation_summary.json').exists(), 'Support not closed.'
    for script, arguments, result in [
        ('report_v3.py', ['--cohort', 'reserved'], 'results.json'),
        ('report_causal_v3.py', [], 'causal_reporting.json'),
    ]:
        if (base / result).exists():
            print('RETAIN_EXISTING_REPORT', result, flush=True)
            continue
        subprocess.run([sys.executable, str(ROOT / 'analysis/hexar_external' / script), *arguments],
                       cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / 'analysis/hexar_external/validate_v3.py'),
                    '--require-final'], cwd=ROOT, check=True)
    print('REGISTERED_REPORTS_CLOSED_REVIEW_FIGURE_AND_FINALIZE_MANUSCRIPT_ARCHIVE', flush=True)


if __name__ == '__main__':
    main()
