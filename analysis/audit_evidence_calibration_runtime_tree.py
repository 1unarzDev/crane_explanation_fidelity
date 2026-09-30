#!/usr/bin/env python3
"""Offline full-tree runtime identity candidate; no sandbox migration or study activation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import time

from evidence_calibration_io import canonical_sha256
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once

SCHEMA = 'crane-runtime-tree-inventory/v1-development'


def fingerprint(value):
    return (value.st_dev, value.st_ino, value.st_mode, value.st_uid, value.st_gid,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _scan(root: Path, *, hash_contents: bool, progress=None):
    entries, observed = {}, {}
    byte_count = 0
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    def visit(fd, prefix):
        nonlocal byte_count
        before_dir = os.fstat(fd)
        with os.scandir(fd) as directory:
            names = sorted(entry.name for entry in directory)
        for name in names:
            path = prefix + name
            before = os.stat(name, dir_fd=fd, follow_symlinks=False)
            metadata = {'mode': stat.S_IMODE(before.st_mode), 'uid': before.st_uid, 'gid': before.st_gid}
            if stat.S_ISLNK(before.st_mode):
                row = {'kind': 'symlink', **metadata, 'target': os.readlink(name, dir_fd=fd)}
            elif stat.S_ISDIR(before.st_mode):
                child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                try:
                    if fingerprint(os.fstat(child)) != fingerprint(before):
                        raise ValueError('runtime directory changed before traversal')
                    row = {'kind': 'directory', **metadata}
                    visit(child, path + '/')
                finally:
                    os.close(child)
            elif stat.S_ISREG(before.st_mode):
                row = {'kind': 'file', **metadata, 'bytes': before.st_size}
                if hash_contents:
                    try:
                        source = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
                    except PermissionError as error:
                        raise PermissionError(error.errno, 'runtime file unreadable; full identity unavailable', path) from error
                    try:
                        if fingerprint(os.fstat(source)) != fingerprint(before):
                            raise ValueError('runtime file changed before hashing')
                        digest = hashlib.sha256()
                        read_bytes = 0
                        while True:
                            data = os.read(source, 1024**2)
                            if not data:
                                break
                            digest.update(data)
                            read_bytes += len(data)
                        if fingerprint(os.fstat(source)) != fingerprint(before) or read_bytes != before.st_size:
                            raise ValueError('runtime file changed during hashing')
                        row['raw_sha256'] = digest.hexdigest()
                        byte_count += read_bytes
                    finally:
                        os.close(source)
            else:
                raise ValueError('runtime special file prohibited')
            after = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if fingerprint(after) != fingerprint(before):
                raise ValueError('runtime entry changed during inventory')
            entries[path], observed[path] = row, fingerprint(after)
            if progress is not None and len(entries) % 5000 == 0:
                progress(len(entries), byte_count)
        if fingerprint(os.fstat(fd)) != fingerprint(before_dir):
            raise ValueError('runtime directory changed during inventory')
    try:
        root_stat = os.fstat(root_fd)
        visit(root_fd, '')
        if fingerprint(os.fstat(root_fd)) != fingerprint(root_stat):
            raise ValueError('runtime root changed during inventory')
        root_metadata = {'mode': stat.S_IMODE(root_stat.st_mode), 'uid': root_stat.st_uid, 'gid': root_stat.st_gid}
        observed['.'] = fingerprint(root_stat)
    finally:
        os.close(root_fd)
    return entries, observed, root_metadata


def inventory(root: Path, *, progress=None) -> dict:
    entries, observed, metadata = _scan(root, hash_contents=True, progress=progress)
    # Detect ordinary changes to already-hashed entries before calling this a complete scan.
    # Fingerprints are transient checks, not part of the portable content identity.
    _, current, _ = _scan(root, hash_contents=False)
    if observed != current:
        raise ValueError('runtime changed before completed inventory; no stable identity')
    result = {'schema': SCHEMA, 'root_metadata': metadata, 'entries': entries}
    result['inventory_sha256'] = canonical_sha256(result)
    return result


def validate(record: dict):
    if set(record) != {'schema', 'root_metadata', 'entries', 'inventory_sha256'} or record['schema'] != SCHEMA:
        raise ValueError('unsupported runtime inventory')
    if canonical_sha256({k: v for k, v in record.items() if k != 'inventory_sha256'}) != record['inventory_sha256']:
        raise ValueError('runtime inventory hash mismatch')
    def metadata(row):
        if any(type(row[k]) is not int for k in ('mode', 'uid', 'gid')) or not 0 <= row['mode'] <= 0o7777 or min(row['uid'],row['gid']) < 0:
            raise ValueError('invalid runtime metadata')
    if set(record['root_metadata']) != {'mode', 'uid', 'gid'}:
        raise ValueError('invalid root metadata')
    metadata(record['root_metadata'])
    if not isinstance(record['entries'], dict):
        raise ValueError('runtime entries must be an object')
    for path, row in record['entries'].items():
        if not isinstance(path, str) or not path or path.startswith('/') or any(p in {'', '.', '..'} for p in path.split('/')):
            raise ValueError('invalid runtime relative path')
        if not isinstance(row, dict) or row.get('kind') not in {'file', 'directory', 'symlink'}:
            raise ValueError('invalid runtime entry')
        fields = {'kind', 'mode', 'uid', 'gid'}
        fields |= {'bytes', 'raw_sha256'} if row['kind'] == 'file' else {'target'} if row['kind'] == 'symlink' else set()
        if set(row) != fields:
            raise ValueError('invalid runtime entry fields')
        metadata(row)
        if row['kind'] == 'file' and (type(row['bytes']) is not int or row['bytes'] < 0
                or not isinstance(row['raw_sha256'], str) or len(row['raw_sha256']) != 64
                or any(c not in '0123456789abcdef' for c in row['raw_sha256'])):
            raise ValueError('invalid runtime file digest or size')
        if row['kind'] == 'symlink' and (not isinstance(row['target'], str) or not row['target'] or '\x00' in row['target']):
            raise ValueError('invalid runtime symlink')
        parent = Path(path).parent.as_posix()
        if parent != '.' and record['entries'].get(parent, {}).get('kind') != 'directory':
            raise ValueError('runtime parent directory absent or not a directory')


def verify(root: Path, expected: dict):
    validate(expected)
    current = inventory(root)
    if current != expected:
        raise ValueError('runtime inventory differs from expected content/metadata identity')


def summary(record: dict) -> dict:
    validate(record)
    counts = {kind: sum(row['kind'] == kind for row in record['entries'].values()) for kind in ('file', 'directory', 'symlink')}
    return {'inventory_sha256': record['inventory_sha256'], 'entry_counts': counts,
            'regular_file_bytes': sum(row['bytes'] for row in record['entries'].values() if row['kind'] == 'file')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='fresh /tmp full inventory; never overwrites')
    args = parser.parse_args()
    if args.output.exists() or Path('/tmp') not in args.output.resolve().parents:
        raise ValueError('fresh /tmp runtime inventory output required')
    intent = args.output.with_suffix('.intent.json')
    if intent.exists():
        raise ValueError('retained/unknown inventory intent; do not adopt or replay')
    _write_once(intent, {'scope': 'NON_STUDY_RUNTIME_OBSERVATION', 'runtime_root': '/usr',
                         'terminal_record_pending': True, 'model_call_attempted': False})
    started = time.monotonic()
    try:
        record = inventory(Path('/usr'), progress=lambda n, b: print(json.dumps({'entries_hashed': n, 'bytes_read': b}), flush=True))
        _write_once(args.output, record)
        print(json.dumps({'status': 'OBSERVED_LIVE_RUNTIME_NOT_IMMUTABLE', **summary(record),
                          'elapsed_seconds': round(time.monotonic()-started, 3),
                          'full_runtime_frozen': False, 'model_call_attempted': False}), flush=True)
    except BaseException as error:
        failure = args.output.with_suffix('.failure.json')
        _write_once(failure, {'status': 'FAILED_RUNTIME_OBSERVATION_NO_REPLAY', 'error_type': type(error).__name__,
                              'error': str(error), 'model_call_attempted': False})
        raise


if __name__ == '__main__':
    main()
