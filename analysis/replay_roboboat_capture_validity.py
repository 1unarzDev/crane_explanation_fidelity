#!/usr/bin/env python3
"""Replay the existing strict validator on temporary copies of retained inputs.

Exit status is the production validator's status. Source recordings are never
written. Counterfactual probes belong in separate diagnostic scripts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ('fixture-summary.json', 'worker-0/result.json', 'endpoint.log',
          'controller.log')


def replay(source):
    hashes = {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
              for name in INPUTS}
    with tempfile.TemporaryDirectory(prefix='boat-validity-replay-') as scratch:
        scratch = Path(scratch)
        for name in INPUTS:
            destination = scratch / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source / name, destination)
        result = subprocess.run([
            sys.executable, str(ROOT / 'packages/crane_ml/Tools/Performance/'
                               'summarize_nav2_reset.py'), str(scratch)],
            capture_output=True, text=True)
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr)
        summary = json.loads((scratch / 'navigation-reset-summary.json').read_text())
    assert hashes == {name: hashlib.sha256((source / name).read_bytes()).hexdigest()
                      for name in INPUTS}, 'Replay changed retained input'
    return result.returncode, {
        'schema': 'roboboat-strict-validity-replay-v1',
        'input_sha256': hashes, 'valid': summary['valid'],
        'navigation_status': summary['navigation']['status'],
        'actions': summary['actions'], 'observations': summary['observations'],
        'validator_sha256': hashlib.sha256((ROOT / 'packages/crane_ml/Tools/'
            'Performance/summarize_nav2_reset.py').read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    code, report = replay(args.source)
    print(json.dumps(report, indent=2))
    return code


if __name__ == '__main__':
    sys.exit(main())
