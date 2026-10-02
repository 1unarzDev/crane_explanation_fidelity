"""Read-only narrower qualification of finished startup/compositor probes."""
import argparse
import hashlib
import json
from pathlib import Path

from roboboat_owned_player_bundle_v1 import binding, verify_build
from roboboat_initial_pose_contract_v1 import assess as assess_pose, UNITS, OPTION, PREFIX
from audit_roboboat_frame_timing_v1 import audit as audit_frames
from build_roboboat_terminal_batch import save


def checked(record):
    if binding(record['path']) != record:
        raise ValueError('original bound probe artifact changed')
    return Path(record['path'])


def startup(root):
    root = Path(root).resolve()
    d = json.loads((root/'declaration.json').read_text())
    terminal = json.loads((root/'terminal.json').read_text())
    if terminal['declaration'] != binding(root/'declaration.json'):
        raise ValueError('startup result declaration differs')
    for r in [d['probe_source'], *d['additional_sources']]:
        checked(r)
    manifest = checked(d['build']); build, _ = verify_build(manifest)
    for r in build['source_bindings_current']:
        checked(r)
    results = []
    for case in d['cases']:
        out = root/case['id']; original = json.loads((out/'terminal.json').read_text())
        worker_path = checked(original['worker_result']); render_path = checked(original['render_audit'])
        worker = json.loads(worker_path.read_text()); render = json.loads(render_path.read_text())
        frame = audit_frames(out/'frame-timing.jsonl')
        pose = case['pose']
        if pose is None:
            pose_audit = {'initialization_readback_pass': not any(line.startswith(PREFIX) for line in
                          (out/'player.log').read_text(errors='replace').splitlines()),
                          'scope': 'No initialization receipt when override absent; default physical pose not measured.'}
        else:
            row = {'id': case['id'], 'initial_pose_request': dict(zip(('x', 'y', 'yaw'), pose)),
                   'initial_pose_units': UNITS, 'initial_pose_cli_option': OPTION}
            pose_audit = assess_pose(row, out/'player.log')
        checks = {'exit_zero': original['return_code'] == 0 and not original.get('timeout_retained'),
            'worker_valid': worker.get('valid') is True, 'pose_readback': pose_audit['initialization_readback_pass'],
            'render_complete': render.get('status') == 'COMPLETE_DEVELOPMENT_ONLY' and render.get('placement_verified') is True and
                               render.get('owned_output_removed') is True and render.get('cleanup_errors') == [],
            'scene_profile': worker.get('scene') == 'Assets/Scenes/Roboboat Course.unity' and worker.get('runtimeProfile') == 'train-gpu',
            'seed_worker': worker.get('randomSeed') == d['seed'] and worker.get('workerId') == 0,
            'full_declared_duration': worker.get('wallSeconds', 0) >= d['duration_s'],
            'signatures': worker.get('imageSignatures') is True,
            'screen': (worker.get('screenWidth'), worker.get('screenHeight')) == (640, 360),
            'depth': (worker.get('depthCamera', {}).get('width'), worker.get('depthCamera', {}).get('height')) == (1280, 720) and worker.get('depthCamera', {}).get('acquisitionCount', 0) > 0,
            'camera_topology': tuple(worker.get(k) for k in ('enabledCameras', 'enabledSensorCameras', 'enabledSpectatorCameras', 'enabledWaterDriverCameras')) == (1, 1, 0, 0),
            'time_scale': worker.get('timeScale') == 1,
            'validation_path': worker.get('validationStream') == str(out/'worker-result.validation.jsonl'),
            'frame_trace': frame['retained_frame_rows'] > 0 and not frame['issues'],
            'fixed_step': abs(frame['metadata']['fixedDeltaTime']-.02) < 1e-7,
            'catch_up_cap': abs(frame['metadata']['appliedMaximumDeltaTime']-.04) < 1e-6,
            'ros_actions_absent': worker.get('acceptedActions') == 0 and worker.get('rejectedActions') == 0}
        for k in ('loggedErrors', 'loggedExceptions', 'invalidWaterSearches', 'staleObservations', 'failedObservations', 'depthBufferValidationMismatches'):
            checks[k+'_zero'] = worker.get(k) == 0
        results.append({'case': case, 'checks': checks, 'passed': all(checks.values()), 'pose_audit': pose_audit,
                        'worker': binding(worker_path), 'render': binding(render_path), 'frames': frame})
    return {'schema': 'roboboat-rendered-startup-review/v21', 'declaration': binding(root/'declaration.json'),
        'original_terminal': binding(root/'terminal.json'), 'review_source': binding(__file__), 'results': results,
        'rendered_startup_only_qualified': all(r['passed'] for r in results), 'independent_n_added': 0,
        'default_pose_measured': False, 'full_navigation_qualified': False, 'revised_v17_platform_qualified': False,
        'scope': 'Three fixed 8s startup benchmarks only. Readback is before Start/physics, not subsequent odometry or physical equivalence. Source review by root, no independent model/human audit.'}


def compositor(root):
    root = Path(root).resolve(); d = json.loads((root/'declaration.json').read_text())
    terminal = json.loads((root/'terminal.json').read_text())
    if terminal['declaration'] != binding(root/'declaration.json'):
        raise ValueError('compositor declaration differs')
    for source in d['sources']:
        checked(source)
    reports = []
    for case in d['cases']:
        out = root/case; item = json.loads((out/'terminal.json').read_text())
        report = json.loads(checked(item['audit']).read_text())
        reports.append((item, report))
    acquisitions = [r['fps_lease'] for _, r in reports]
    releases = [r['fps_lease_release'] for _, r in reports]
    originals = {r['original_fps'] for r in acquisitions}
    original = next(iter(originals)) if len(originals) == 1 else None
    checks = {'two_outputs': len(reports) == 2,
        'both_clean': all(item['return_code'] == 0 and r['status'] == 'COMPLETE_DEVELOPMENT_ONLY' and r['cleanup_errors'] == [] and r['owned_output_removed'] is True for item, r in reports),
        'distinct_output_workspace': len({r['owned_output'] for _, r in reports}) == 2 and len({r['owned_workspace'] for _, r in reports}) == 2,
        'distinct_lease_owners': len({(r['owner']['pid'], r['owner']['start'], r['owner']['nonce']) for r in acquisitions}) == 2,
        'two_simultaneous_leases': sorted(r['active_owners'] for r in acquisitions) == [1, 2],
        'common_original_fps': original is not None,
        'desired_fps_60': all(r['desired_fps'] == 60 for r in acquisitions),
        'release_order': sorted(r['remaining_owners'] for r in releases) == [0, 1],
        'release_restoration': all((r['remaining_owners'] == 0 and r['original_restored'] is True and r['fps'] == original) or
                                  (r['remaining_owners'] == 1 and r['original_restored'] is False and r['fps'] == 60) for r in releases)}
    return {'schema': 'roboboat-empty-compositor-review/v21', 'declaration': binding(root/'declaration.json'),
        'original_terminal': binding(root/'terminal.json'), 'review_source': binding(__file__), 'checks': checks,
        'empty_compositor_only_qualified': all(checks.values()), 'independent_n_added': 0,
        'Unity_windows_qualified': False, 'sensors_qualified': False, 'navigation_qualified': False,
        'scope': 'Two empty outputs with overlapping leases and final restoration only. No Unity or ROS; no full concurrent collection claim. Root source audit only.'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('kind', choices=('startup', 'compositor'))
    p.add_argument('--root', required=True); p.add_argument('--output', required=True); a = p.parse_args()
    if Path(a.output).exists(): raise FileExistsError('fresh immutable review output required')
    result = startup(a.root) if a.kind == 'startup' else compositor(a.root)
    save(Path(a.output), result)
    print(json.dumps({k: v for k, v in result.items() if k.endswith('qualified') or k == 'independent_n_added'}))
