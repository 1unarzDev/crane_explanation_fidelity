"""Exact-source isolated launch tree; no compiled platform files are modified."""
import hashlib
import json
from pathlib import Path
import shutil


def binding(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}


def relative_route(row):
    value = Path(row['path_file']['path'])
    if value.is_absolute() or '..' in value.parts:
        raise ValueError('canonical repository-relative route required')
    relative = value.relative_to('packages/crane_ml')
    if not relative.is_relative_to('Tools/Performance/generated_populations'):
        raise ValueError('generated public route required')
    return relative


def launch_route(launch_root, row, source_root):
    root = Path(launch_root).resolve()
    relative = relative_route(row)
    original = Path(source_root)/row['path_file']['path']
    target = root/relative
    if not target.resolve().is_relative_to(root):
        raise ValueError('route resolves outside mounted launch root')
    expected = row['path_file']['sha256']
    if binding(original)['sha256'] != expected or binding(target)['sha256'] != expected:
        raise ValueError('staged/source route differs from declared bytes')
    return target


def stage(project, launch_root, rows, source_root):
    project, root = Path(project).resolve(), Path(launch_root).resolve()
    if root.exists():
        raise FileExistsError('fresh isolated launch root required')
    files = sorted(p for p in (project/'Tools/Performance').iterdir() if p.is_file() and
                   p.suffix in ('.py', '.sh', '.yaml', '.xml', '.json', '.csv', '.md', '.txt'))
    if not all((project/'Tools/Performance'/name) in files for name in
               ('run_nav2_controller_fixture_capture_v15.sh', 'run_worker.sh',
                'nav2_follow_path_fixture_capture_v15.py', 'roboboat_capture_completion_v1.py')):
        raise ValueError('exact launch closure incomplete')
    root.mkdir(parents=True); copied = []
    for original in files:
        target = root/original.relative_to(project); target.parent.mkdir(parents=True, exist_ok=True)
        before = binding(original); shutil.copy2(original, target)
        if binding(target)['sha256'] != before['sha256'] or binding(original) != before:
            raise ValueError('launch source copy changed')
        copied.append({'original': before, 'snapshot': binding(target)})
    routes = []
    for row in rows:
        if 'path_file' not in row:
            continue
        original = Path(source_root)/row['path_file']['path']; target = root/relative_route(row)
        if binding(original)['sha256'] != row['path_file']['sha256']:
            raise ValueError('original route changed')
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists(): shutil.copy2(original, target)
        target = launch_route(root, row, source_root)
        routes.append({'row_id': row['id'], 'original': binding(original), 'snapshot': binding(target)})
    manifest = {'schema': 'roboboat-isolated-launch-mount/v24', 'root': str(root),
        'parent_project': str(project), 'launch_files': copied, 'routes': routes,
        'helper': binding(__file__), 'platform_source_modified': False, 'compiled_player_modified': False,
        'independent_n_added': 0, 'scope': 'Unchanged runtime Tools plus exact route JSON, mounted under a separate root. No operational/platform qualification.'}
    (root/'launch-mount-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest
