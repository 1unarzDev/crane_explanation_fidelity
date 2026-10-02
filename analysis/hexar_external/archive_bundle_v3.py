#!/usr/bin/env python3
"""Preserve actual private bytes and verify restoration, without shared storage writes."""
import argparse
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from pathlib import Path

from audit_release import ROOT, sha, write


def command(*args, cwd=ROOT):
    return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tag', required=True)
    parser.add_argument('--closed-development-only', action='store_true')
    args = parser.parse_args()
    assert args.tag and all(c.isalnum() or c in '-_' for c in args.tag)
    base = ROOT / 'data/hexar_external'
    if not args.closed_development_only:
        command(str(base / '.venv/bin/python'), str(ROOT / 'analysis/hexar_external/validate_v3.py'), '--require-final')
    target = base / 'archives' / args.tag
    target.mkdir(parents=True, mode=0o700, exist_ok=False)
    os.chmod(target.parent, 0o700)
    code_commit = command('git', 'rev-parse', 'HEAD')
    upstream_commit = command('git', '-C', str(base / 'upstream'), 'rev-parse', 'HEAD')
    assert upstream_commit == 'f5e9567edb43899ad7dd4efcbeb5429ff4b0c6fc'
    code_bundle = target / 'code.bundle'
    upstream_bundle = target / 'upstream.bundle'
    command('git', 'bundle', 'create', str(code_bundle), 'HEAD')
    command('git', '-C', str(base / 'upstream'), 'bundle', 'create', str(upstream_bundle), 'HEAD')
    selected = []
    for path in sorted(base.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(base)
        if any(part in {'.venv', '.git', 'tmp', 'archives', '__pycache__'} for part in relative.parts):
            continue
        if args.closed_development_only and relative.parts[0] == 'v3':
            if len(relative.parts) < 2 or relative.parts[1] not in {'qualification', 'runtime_provenance.json', 'annotation_binding.json'}:
                continue
        selected.append((path, str(path.relative_to(ROOT)), sha(path), path.stat().st_size))
    assets = target / 'private-assets.tar.gz'
    with tarfile.open(assets, 'w:gz') as archive:
        for path, relative, digest, _ in selected:
            archive.add(path, arcname=relative, recursive=False)
            assert sha(path) == digest, 'Source changed while archiving: ' + relative
    manifest = {'schema': 'hexar-private-byte-preservation/v3', 'code_commit': code_commit,
                'upstream_commit': upstream_commit, 'closed_development_only': args.closed_development_only,
                'files': [{'path': p, 'sha256': h, 'bytes': n} for _, p, h, n in selected],
                'excluded': ['venv (dependency lock and interpreter retained)', 'Git metadata (bundles retained)',
                             'temporary directories', 'archives', 'compiled Python caches'],
                'private_only': True, 'redistribution_rights_resolved': False}
    write(target / 'assets_manifest.json', manifest)
    with tempfile.TemporaryDirectory(prefix='restore-', dir=target) as temporary:
        recovered = Path(temporary) / 'code'
        command('git', 'clone', '--quiet', str(code_bundle), str(recovered))
        assert command('git', 'rev-parse', 'HEAD', cwd=recovered) == code_commit
        upstream = recovered / 'data/hexar_external/upstream'
        upstream.parent.mkdir(parents=True, exist_ok=True)
        command('git', 'clone', '--quiet', str(upstream_bundle), str(upstream))
        assert command('git', '-C', str(upstream), 'rev-parse', 'HEAD') == upstream_commit
        with tarfile.open(assets) as archive:
            expected = {relative for _, relative, _, _ in selected}
            assert {m.name for m in archive.getmembers()} == expected
            assert all(m.isfile() for m in archive.getmembers())
            archive.extractall(recovered, filter='data')
        for _, relative, digest, _ in selected:
            assert sha(recovered / relative) == digest, 'Restored byte mismatch: ' + relative
        tests = command(str(base / '.venv/bin/python'), '-m', 'unittest', 'discover', '-s', 'tests/hexar_external', '-v', cwd=recovered)
        assert 'OK' in tests
    receipt = {'schema': 'hexar-private-restore-receipt/v3', 'archive_location': str(target),
               'storage': 'private local filesystem; no external transfer or disaster-recovery durability claim',
               'code_commit_restored': code_commit, 'upstream_commit_restored': upstream_commit,
               'files_restored_and_sha256_checked': len(selected), 'scoped_tests_restored': True,
               'assets_sha256': sha(assets), 'code_bundle_sha256': sha(code_bundle),
               'upstream_bundle_sha256': sha(upstream_bundle), 'manifest_sha256': sha(target / 'assets_manifest.json'),
               'no_shared_git_or_storage_mutation': True, 'alpha_consumed': 0}
    write(target / 'restore_receipt.json', receipt)
    write(base / 'v3' / ('closed_development_restore_receipt.json' if args.closed_development_only else 'final_restore_receipt.json'), receipt)
    for path in target.iterdir():
        if path.is_file():
            os.chmod(path, 0o400)
    print('PRIVATE_BYTES_ARCHIVED_AND_RESTORED', len(selected), str(target))


if __name__ == '__main__':
    main()
