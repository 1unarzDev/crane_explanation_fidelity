import json
from pathlib import Path
import pytest
import roboboat_owned_player_bundle_v1 as bundle


def build(tmp_path):
    root = tmp_path/'build'; (root/'CRANE_Data').mkdir(parents=True)
    (root/'CRANE.x86_64').write_bytes(b'player'); (root/'CRANE_Data/assembly').write_bytes(b'compiled')
    manifest = tmp_path/'manifest.json'
    manifest.write_text(json.dumps({'build_root': str(root), 'full_build_files':
        [{'path': p.relative_to(root).as_posix(), 'bytes': p.stat().st_size, 'sha256': bundle.digest(p)}
         for p in root.rglob('*') if p.is_file()]}))
    return root, manifest


def test_fresh_nonce_bundle_preserves_exact_source_bytes_and_revalidates_data(tmp_path):
    root, manifest = build(tmp_path); target = tmp_path/'bundle'
    d = bundle.prepare(manifest, target, 'a'*32)
    assert bundle.verify(target) == d
    assert (target/d['expected_class']).stat().st_ino != (root/'CRANE.x86_64').stat().st_ino
    assert (target/(d['expected_class']+'_Data')).resolve() == root/'CRANE_Data'
    with pytest.raises(FileExistsError): bundle.prepare(manifest, target, 'b'*32)
    (root/'CRANE_Data/assembly').write_bytes(b'changed')
    with pytest.raises(ValueError): bundle.verify(target)


@pytest.mark.parametrize('attack', ['unlisted', 'duplicate', 'escape', 'bundle_extra', 'bundle_link'])
def test_manifest_and_bundle_admission_reject_incomplete_or_redirected_bytes(tmp_path, attack):
    root, manifest = build(tmp_path); target = tmp_path/'bundle'
    if attack in ('bundle_extra', 'bundle_link'):
        d = bundle.prepare(manifest, target, 'a'*32)
        if attack == 'bundle_extra': (target/'extra').write_text('extra')
        else:
            link = target/(d['expected_class']+'_Data'); link.unlink(); link.symlink_to(tmp_path)
        with pytest.raises(ValueError): bundle.verify(target)
    else:
        d = json.loads(manifest.read_text())
        if attack == 'unlisted': (root/'extra').write_text('extra')
        if attack == 'duplicate': d['full_build_files'].append(d['full_build_files'][0])
        if attack == 'escape': d['full_build_files'][0]['path'] = '../escape'
        manifest.write_text(json.dumps(d))
        with pytest.raises(ValueError): bundle.prepare(manifest, target, 'a'*32)
