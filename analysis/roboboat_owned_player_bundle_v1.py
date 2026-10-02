"""Fresh nonce launch bundle for rendering-v3; exact build bytes verified.

No player/compositor launch. Shared immutable build data remain symlinked and
must be reverified immediately before every launch; the executable is copied.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    return {'path': str(Path(path).resolve()), 'sha256': digest(path)}


def verify_build(manifest_path):
    d = json.loads(Path(manifest_path).read_text()); root = Path(d['build_root']).resolve()
    listed = d['full_build_files']; names = [i['path'] for i in listed]
    if not names or len(names) != len(set(names)) or 'CRANE.x86_64' not in names:
        raise ValueError('complete unique build manifest required')
    for item in listed:
        relative = Path(item['path']); path = (root/relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(root):
            raise ValueError('invalid build path')
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('compiled build bytes changed')
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != set(names):
        raise ValueError('build manifest is not exhaustive')
    return d, root


def prepare(manifest_path, target, nonce):
    target = Path(target).resolve()
    if not re.fullmatch('[a-f0-9]{32}', nonce): raise ValueError('32 hex nonce required')
    if target.exists(): raise FileExistsError('fresh bundle namespace required')
    d, root = verify_build(manifest_path)
    name = 'CRANE-owned-'+nonce
    target.mkdir(parents=True)
    executable = target/name
    shutil.copy2(root/'CRANE.x86_64', executable)
    links = []
    for path in sorted(root.iterdir()):
        if path.name == 'CRANE.x86_64': continue
        destination = target/(name+'_Data' if path.name == 'CRANE_Data' else path.name)
        destination.symlink_to(path, target_is_directory=path.is_dir())
        links.append({'path': destination.name, 'target': str(path.resolve())})
    record = {'schema': 'roboboat-owned-player-bundle/v1-development',
              'manifest': binding(manifest_path), 'bundle_root': str(target),
              'expected_class': name, 'executable': binding(executable), 'links': links,
              'original_build_root': str(root), 'production_launch_requirements':
              {'SDL_VIDEODRIVER': 'x11', 'screen_fullscreen': 0, 'screen': [640, 360]},
              'class_requires_actual_runtime_verification': True,
              'physics_or_scientific_equivalence_claim': False, 'confirmation_n': 0}
    with (target/'bundle-binding.json').open('x') as f: json.dump(record, f, indent=2)
    verify(target)
    return record


def verify(target):
    target = Path(target).resolve(); d = json.loads((target/'bundle-binding.json').read_text())
    if d['bundle_root'] != str(target): raise ValueError('bundle identity changed')
    manifest = Path(d['manifest']['path'])
    if digest(manifest) != d['manifest']['sha256']: raise ValueError('manifest changed')
    _, root = verify_build(manifest)
    if str(root) != d['original_build_root']: raise ValueError('original build changed')
    executable = target/d['expected_class']
    if executable.is_symlink() or executable.resolve() != Path(d['executable']['path']) or digest(executable) != d['executable']['sha256']:
        raise ValueError('copied executable identity changed')
    expected = {'bundle-binding.json', d['expected_class']}
    for item in d['links']:
        path = target/item['path']; expected.add(item['path'])
        if not path.is_symlink() or str(path.resolve()) != item['target']:
            raise ValueError('build-data symlink changed')
    original_names = {p.name for p in root.iterdir() if p.name != 'CRANE.x86_64'}
    expected_links = {d['expected_class']+'_Data' if n == 'CRANE_Data' else n for n in original_names}
    if {i['path'] for i in d['links']} != expected_links or {p.name for p in target.iterdir()} != expected:
        raise ValueError('unexpected/missing bundle member')
    if digest(executable) != digest(root/'CRANE.x86_64'): raise ValueError('different player bytes')
    return d
