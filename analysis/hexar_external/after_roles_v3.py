#!/usr/bin/env python3
"""Close blind roles before the unchanged two-worker qualified support queue."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from audit_release import ROOT, sha
from verify_v3 import V3, study


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--role-pid', type=int, required=True)
    args = parser.parse_args()
    study()
    ann = V3 / 'reserved/annotation'
    review = json.loads((ann / 'parent_inventory_review.json').read_text())
    parent = json.loads((ann / 'causal_roles.parent.json').read_text())
    assert review['all_unique_texts_reviewed'] and not review['support_labels_accessed']
    assert parent['inventory_sha256'] == sha(ann / 'atomic_inventory.json')
    assert not parent['coder_labels_accessed'] and not parent['support_labels_accessed']
    process = Path('/proc') / str(args.role_pid)
    while process.exists():
        try:
            command = (process / 'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:
            break
        if not any(command):
            break
        if b'analysis/hexar_external/extract_v3.py' not in command or b'roles' not in command:
            raise RuntimeError('Role PID changed identity; refusing concurrent support.')
        time.sleep(10)
    assert (ann / 'extraction/roles/summary.json').exists(), 'Incomplete role queue.'
    for script, extra in [
        ('extract_v3.py', ['--stage', 'assemble-roles']),
        ('annotate_v3.py', ['--cohort', 'reserved', '--stage', 'packets']),
        ('annotate_v3.py', ['--cohort', 'reserved', '--stage', 'annotate']),
    ]:
        print('START', script, *extra, flush=True)
        subprocess.run([sys.executable, str(ROOT / 'analysis/hexar_external' / script), *extra],
                       cwd=ROOT, check=True)
    print('QUALIFIED_SUPPORT_CLOSED_READY_FOR_REGISTERED_REPORT', flush=True)


if __name__ == '__main__':
    main()
