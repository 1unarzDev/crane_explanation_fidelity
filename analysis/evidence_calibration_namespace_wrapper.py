#!/usr/bin/env python3
"""Operator-side status descriptor launcher; no provider or model invocation."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


def launch(request_path: Path, expected_sha256: str) -> int:
    with request_path.open('rb') as handle:
        raw = handle.read(16 * 1024**2 + 1)
    if len(raw) > 16 * 1024**2 or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('wrapper request bytes exceed bound or differ from intent')
    request = json.loads(raw)
    if not isinstance(request, dict) or set(request) != {'command', 'status_path'}:
        raise ValueError('exact namespace wrapper request required')
    argv = request['command']
    if (not isinstance(argv, list) or not argv or argv[0] != '/usr/bin/bwrap'
            or any(not isinstance(argument, str) for argument in argv)
            or '--json-status-fd' in argv or not isinstance(request['status_path'], str)):
        raise ValueError('registered namespace command required')
    path = Path(request['status_path'])
    if not path.is_absolute() or path.parent != request_path.resolve().parent:
        raise ValueError('status file must share the operator transaction directory')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        argv = [argv[0], '--json-status-fd', str(fd), *argv[1:]]
        # Streams inherit the bounded outer service capture; status uses a separate FD.
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, close_fds=True, pass_fds=(fd,))
        os.fsync(fd)
        return result.returncode if result.returncode >= 0 else 128 - result.returncode
    finally:
        os.close(fd)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError('wrapper requires one bound request path and SHA-256')
    raise SystemExit(launch(Path(sys.argv[1]), sys.argv[2]))
