#!/usr/bin/env python3
"""Recompute the exact common B2/B4 annotation source supplement."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_evidence_calibration_pilot_source_context_bundle import ROOT, DEFAULT_ASSETS, DEFAULT_AUDIT, build
from evidence_calibration_io import canonical_json_bytes


def audit(root: Path = ROOT) -> dict:
    assets, expected = build(root)
    asset_path = root / DEFAULT_ASSETS.relative_to(ROOT)
    audit_path = root / DEFAULT_AUDIT.relative_to(ROOT)
    if asset_path.read_bytes() != canonical_json_bytes(assets) + b"\n":
        raise ValueError("common source asset manifest differs from all 57 B2 call bindings")
    if audit_path.read_bytes() != canonical_json_bytes(expected) + b"\n":
        raise ValueError("source context audit manifest differs from reconstruction")
    return {"schema": "crane-evidence-calibration-pilot-source-context-audit/v1",
            "status": "PASS_HASH_BOUND_COMMON_CONTEXT", "condition_count": 57,
            "asset_count": len(assets), "asset_manifest_raw_sha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
            "annotation_performed": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
