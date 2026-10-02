"""Fixed two-output compositor ownership probe. No Unity, ROS, or study N."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from roboboat_owned_player_bundle_v1 import binding

ROOT = Path(__file__).resolve().parents[1]


def prepare(root):
    root = Path(root).resolve()
    if root.exists():
        raise FileExistsError('fresh prospective parallel-render probe required')
    root.mkdir()
    paths = [Path(__file__), ROOT / 'analysis/roboboat_hidden_render_v4.py',
             ROOT / 'analysis/roboboat_render_fps_lease_v1.py', ROOT / 'scripts/run_roboboat_hidden_render_v4.sh',
             ROOT / 'analysis/roboboat_owned_player_bundle_v1.py']
    d = {'schema': 'roboboat-parallel-compositor-probe/v1', 'root': str(root),
         'sources': [binding(p) for p in paths], 'cases': ['output-a', 'output-b'],
         'hold_s': 5, 'mode': 'two concurrent empty nonce-owned headless outputs; no Unity or ROS',
         'compatibility': 'Each child waits on shared legacy render gate; old exclusive runs remain protected.',
         'stopping': 'Both fixed cases once. Retain failures; no retries or outcome-dependent changes.',
         'independent_n_added': 0, 'confirmation_n': 0, 'replication_n': 0,
         'scope': 'Compositor/FPS concurrency only; no window routing, sensing/physics, navigation or platform qualification.'}
    (root / 'declaration.json').write_text(json.dumps(d, indent=2) + '\n')
    return d


def execute(root):
    root = Path(root).resolve(); declaration = root / 'declaration.json'
    d = json.loads(declaration.read_text())
    if d['root'] != str(root) or any(d[k] != 0 for k in ('independent_n_added', 'confirmation_n', 'replication_n')):
        raise ValueError('zero-N fixed compositor declaration required')
    for record in d['sources']:
        if binding(record['path']) != record:
            raise ValueError('declared parallel-probe source changed')
    with (root / 'run-intent.json').open('x') as stream:
        json.dump({'declaration': binding(declaration), 'state': 'FIXED_TWO_CHILDREN_WAIT_FOR_LEGACY_GATE'}, stream)
    jobs = []
    for case in d['cases']:
        output = root / case; output.mkdir()
        command = [str(ROOT / 'scripts/run_roboboat_hidden_render_v4.sh'), '--probe-only',
                   '--probe-hold-seconds', str(d['hold_s']), '--audit-path', str(output / 'render-audit.json')]
        log = (output / 'process-output.log').open('x')
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
            env={**{k: v for k, v in os.environ.items() if not k.startswith('CRANE_')}, 'CRANE_NOGRAPHICS': '0'})
        receipt = {'case': case, 'command': command, 'pid': process.pid, 'independent_n_added': 0}
        (output / 'launch-intent.json').write_text(json.dumps(receipt, indent=2) + '\n')
        jobs.append((process, log, output, receipt))
    print(json.dumps({'state': 'TWO_COMPOSITOR_PROBES_LIVE_OR_WAITING_FOR_LEGACY_GATE',
                      'child_pids': [p.pid for p, _, _, _ in jobs], 'independent_n_added': 0}), flush=True)
    results = []
    for process, log, output, receipt in jobs:
        receipt['return_code'] = process.wait(); log.close()
        path = output / 'render-audit.json'
        report = json.loads(path.read_text()) if path.exists() else {}
        receipt['audit'] = binding(path) if path.exists() else None
        receipt['report'] = report
        receipt['passed'] = (process.returncode == 0 and report.get('status') == 'COMPLETE_DEVELOPMENT_ONLY'
                             and not report.get('cleanup_errors') and report.get('owned_output_removed') is True)
        (output / 'terminal.json').write_text(json.dumps(receipt, indent=2) + '\n'); results.append(receipt)
    active_counts = [r['report'].get('fps_lease', {}).get('active_owners') for r in results]
    releases = [r['report'].get('fps_lease_release', {}) for r in results]
    matched_scope = (len({r['report'].get('fps_lease', {}).get('original_fps') for r in results}) == 1)
    result = {'schema': 'roboboat-parallel-compositor-result/v1', 'declaration': binding(declaration),
        'results': results, 'both_outputs_clean': all(r['passed'] for r in results),
        'concurrent_leases_observed': 2 in active_counts,
        'one_nonlast_and_one_last_release': sorted(r.get('remaining_owners', -1) for r in releases) == [0, 1],
        'common_original_fps': matched_scope, 'independent_n_added': 0, 'confirmation_n': 0,
        'full_platform_qualified': False, 'actual_Unity_multiwindow_qualified': False}
    result['compositor_concurrency_passed'] = all(result[k] for k in ('both_outputs_clean',
        'concurrent_leases_observed', 'one_nonlast_and_one_last_release', 'common_original_fps'))
    (root / 'terminal.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('compositor_concurrency_passed', 'independent_n_added')}))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=('prepare', 'execute')); p.add_argument('--root', required=True)
    a = p.parse_args(); prepare(a.root) if a.phase == 'prepare' else execute(a.root)
