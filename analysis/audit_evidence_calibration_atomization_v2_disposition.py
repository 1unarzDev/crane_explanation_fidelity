#!/usr/bin/env python3
"""Verify v2 inventory qualification and its deliberately limited scope."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_atomization_review import audit as audit_review


ROOT = Path(__file__).resolve().parents[1]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(root: Path = ROOT) -> dict:
    manifest = json.loads((root / "manifests/study/evidence-calibration-atomization-v2-disposition.json").read_text())
    if manifest["status"] != "QUALIFIED_SYNTHETIC_ATOMIC_INVENTORY_ONLY":
        raise ValueError("v2 qualification status changed")
    if manifest["unqualified_fields"] != ["asserted_abstraction_level"]:
        raise ValueError("v2 abstraction-tag limitation was removed")
    freeze = manifest["qualification_freeze"]
    freeze_path = root / freeze["path"]
    if sha256(freeze_path.read_bytes()) != freeze["raw_sha256"]:
        raise ValueError("v2 freeze bytes changed")
    review = manifest["semantic_review"]
    review_path = root / review["path"]
    if sha256(review_path.read_bytes()) != review["raw_sha256"]:
        raise ValueError("v2 semantic-review bytes changed")
    records = manifest["retained_calls"]
    call_root = root / records["root"]
    paths = sorted(call_root.rglob("*.json"))
    rows = [{"path": str(path.relative_to(call_root)), "sha256": sha256(path.read_bytes())} for path in paths]
    if len(rows) != records["record_count"]:
        raise ValueError("v2 retained call count changed")
    row_hash = sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    if row_hash != records["sorted_relative_path_and_raw_sha256_record_set_sha256"]:
        raise ValueError("v2 retained call bytes changed")
    result = audit_review(freeze_path, call_root, review_path)
    if not result["qualification_passed"]:
        raise ValueError("v2 frozen inventory gates failed")
    for slot in ("A", "B"):
        if result["per_pass"][slot]["gold_atoms"] != review["heldout_gold_atoms_per_pass"]:
            raise ValueError("v2 held-out atom denominator changed")
    return {"status": "PASS_INVENTORY_ONLY", "retained_records": len(rows),
            "inventory_qualification_passed": True, "abstraction_tags_qualified": False,
            "pilot_inventory_completeness_established": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
