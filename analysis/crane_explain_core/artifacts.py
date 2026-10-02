"""Deterministic artifact and provenance helpers used by analysis CLIs."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of an artifact without changing it."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json_once(path: Path, record: Any) -> None:
    """Write a retained JSON artifact, rejecting conflicting rewrites."""
    raw = json.dumps(record, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != raw:
            raise RuntimeError(f"Retained result differs: {path}")
        return
    path.write_text(raw)
