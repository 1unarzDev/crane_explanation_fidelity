"""Separate grouped-arithmetic synthetic runtime probe; no semantic inputs or calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .journal import exclusive_json, fingerprint
from .mixture_interval_v2 import summary

ROOT = Path(__file__).resolve().parents[3]
CASES = ((40, 32, 72), (63, 51, 114), (390, 260, 1296), (1690, 1382, 3072))
TIMEOUT = 60


def worker(index):
    f, u, n = CASES[index]
    print(json.dumps(summary(f, u, n)), flush=True)


def execute(destination):
    destination.mkdir(exist_ok=False)
    sources = [Path(__file__), Path(__file__).with_name('mixture_statistics.py'),
               Path(__file__).with_name('mixture_interval_v2.py'),
               Path(__file__).with_name('statistics.py'),
               ROOT / 'docs/hexar_external/confirmatory_v1/ANALYSIS_RUNTIME_V2_QUALIFICATION.md']
    archive = destination / 'source_archive'
    for source in sources:
        target = archive / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    declaration = dict(schema='hexar-synthetic-analysis-runtime-screen/v1',
        phase='development_only', cases=CASES, timeout_seconds=TIMEOUT,
        interval_iterations=48, source_hashes={str(p.relative_to(ROOT)):
            hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        python_executable=sys.executable, python_version=sys.version,
        confirmatory_N=0, alpha_consumed=0, no_semantic_inputs=True, no_provider_calls=True)
    exclusive_json(destination / 'declaration.json', declaration)
    rows = []
    for index, (f, u, n) in enumerate(CASES):
        if any(hashlib.sha256(p.read_bytes()).hexdigest() != declaration['source_hashes'][str(p.relative_to(ROOT))]
               for p in sources):
            raise ValueError('analysis sources changed during fixed runtime probe')
        start = time.monotonic()
        command = [sys.executable, '-m', __spec__.name, '--worker', str(index)]
        result, parsed = None, None
        try:
            result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=TIMEOUT)
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
            if code != 0:
                raise ValueError('worker returned nonzero')
            parsed = json.loads(stdout)
            interval = parsed['two_sided_interval']
            if (not all(math.isfinite(x) and -1 <= x <= 1 for x in interval)
                    or interval[0] > interval[1] or parsed['one_sided_lower'] != interval[0]
                    or parsed['n'] != n or parsed['favorable'] != f or parsed['unfavorable'] != u
                    or (parsed['reject'] and parsed['one_sided_lower'] <= 0)):
                raise ValueError('full interval/count/decision consistency failure')
            status, error = 'COMPLETE', None
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code = exc.stdout or b'', exc.stderr or b'', None
            status, error = 'TIMED_OUT_RETAINED', 'Fixed 60-second synthetic runtime limit exceeded.'
        except (ValueError, KeyError, TypeError) as exc:
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
            status, error = 'FAILED_RETAINED', str(exc)
        elapsed = time.monotonic() - start
        folder = destination / str(index)
        folder.mkdir()
        hashes = {}
        for name, data in (('stdout.bin', stdout), ('stderr.bin', stderr)):
            with (folder / name).open('xb') as stream:
                stream.write(data)
            hashes[name] = hashlib.sha256(data).hexdigest()
        row = dict(index=index, favorable=f, unfavorable=u, n=n,
                   elapsed_seconds=elapsed, status=status, error=error,
                   returncode=code, raw_hashes=hashes, parsed=parsed)
        exclusive_json(folder / 'outcome.json', row)
        rows.append(row)
        print(index, n, status, round(elapsed, 3), flush=True)
    report = dict(schema='hexar-synthetic-analysis-runtime-screen-report/v1',
        status='SYNTHETIC_RUNTIME_SCREEN_PASSED_NOT_FINAL_ADAPTER_QUALIFICATION'
            if all(r['status'] == 'COMPLETE' for r in rows) else 'FAILED_RUNTIME_SCREEN_RETAINED',
        rows=rows, declaration_sha256=fingerprint(declaration),
        selected_n=None, confirmatory_N=0, alpha_consumed=0,
        no_semantic_inputs=True, provider_calls=0, confirmation_authorized=False)
    exclusive_json(destination / 'report.json', report)
    print(report['status'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', type=int, choices=range(len(CASES)))
    args = parser.parse_args()
    if args.worker is not None:
        worker(args.worker)
    else:
        execute(ROOT / 'manifests/hexar_external/confirmatory_v1/analysis_runtime_screen_v2')
