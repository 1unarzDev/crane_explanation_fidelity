"""Bind static flat repository Python imports and explicitly named launch scripts.

This does not resolve installed packages, dynamic imports, Python search-path shadowing,
runtime immutability or races between inspection and execution.
"""
import ast
import hashlib
import os
from pathlib import Path
import re
import stat


def repository_source_hashes(directory: Path, roots: tuple[str, ...]) -> dict[str, str]:
    if not roots or len(set(roots)) != len(roots):
        raise ValueError('unique explicit repository source roots required')
    pending = list(roots)
    hashes = {}
    total = 0
    while pending:
        name = pending.pop()
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*\.py', name):
            raise ValueError('flat Python source names required')
        if name in hashes:
            continue
        if len(hashes) >= 512:
            raise ValueError('repository source closure exceeds file limit')
        fd = os.open(directory / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise ValueError('repository source must be a regular file')
            with os.fdopen(fd, 'rb', closefd=False) as stream:
                content = stream.read(8 * 1024**2 + 1)
        finally:
            os.close(fd)
        total += len(content)
        if len(content) > 8 * 1024**2 or total > 64 * 1024**2:
            raise ValueError('repository source closure exceeds byte limit')
        hashes[name] = hashlib.sha256(content).hexdigest()
        for node in ast.walk(ast.parse(content, filename=name)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    raise ValueError('relative imports require separate binding support')
                if node.module:
                    modules = [node.module]
            for module in modules:
                base = module.split('.')[0]
                path = directory / (base + '.py')
                # lexists includes dangling links, which must fail rather than disappear.
                if os.path.lexists(path):
                    if '.' in module:
                        raise ValueError('local dotted imports require separate binding support')
                    pending.append(path.name)
                elif (directory / base).is_dir():
                    raise ValueError('local packages require separate binding support')
    return dict(sorted(hashes.items()))
