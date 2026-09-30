"""Verify restored runtime bytes/metadata against the bound archive and inventory."""
from __future__ import annotations
from decimal import Decimal
import hashlib
import os
from pathlib import Path
import stat
import tarfile

from audit_evidence_calibration_runtime_tree import inventory, validate
from evidence_calibration_io import canonical_sha256


def verify(root: Path, archive_path: Path, expected: dict) -> dict:
    validate(expected)
    actual = inventory(root)
    if actual != expected:
        raise ValueError('restored full content/metadata differs from expected inventory')
    attributes, checked, links = {}, 0, 0
    with tarfile.open(archive_path, mode='r|') as archive:
        for member in archive:
            name = member.name.rstrip('/')
            if name != 'usr' and not name.startswith('usr/'):
                raise ValueError('archive member outside registered runtime')
            path = root if name == 'usr' else root / name[4:]
            info = path.lstat()
            stamp = int(Decimal(member.pax_headers.get('mtime', str(member.mtime))) * 10**9)
            if info.st_mtime_ns != stamp:
                raise ValueError('restored nanosecond timestamp differs from archive')
            desired = {key[13:]: value.encode('utf-8','surrogateescape').hex()
                       for key,value in member.pax_headers.items() if key.startswith('SCHILY.xattr.')}
            found = {key: os.getxattr(path,key,follow_symlinks=False).hex()
                     for key in os.listxattr(path,follow_symlinks=False)}
            if found != desired:
                raise ValueError('restored extended attributes differ from archive')
            attributes[name] = found
            if member.islnk():
                if not member.linkname.startswith('usr/'):
                    raise ValueError('hardlink target outside runtime')
                target = (root/member.linkname[4:]).lstat()
                if (info.st_dev,info.st_ino)!=(target.st_dev,target.st_ino) or not stat.S_ISREG(info.st_mode):
                    raise ValueError('restored hardlink identity differs from archive')
                links += 1
            checked += 1
    if checked != len(expected['entries'])+1:
        raise ValueError('archive member count differs from restored inventory')
    return {'inventory_sha256': actual['inventory_sha256'], 'members_checked': checked,
            'hardlinks_checked': links, 'extended_attributes_sha256':canonical_sha256(attributes),
            'entries_with_extended_attributes':sum(bool(value) for value in attributes.values()),
            'nanosecond_timestamps_verified':True,'content_owner_mode_and_symlinks_verified':True,
            'execution_parity_verified':False,'scientific_runtime_adopted':False}
