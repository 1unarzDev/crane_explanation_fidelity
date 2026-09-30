#!/usr/bin/env python3
"""Verify retained v1 extraction calls without promoting the invalid reference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/study/evidence-calibration-atomization-v1-disposition.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["status"] != "INVALID_REFERENCE_CONTRACT_NO_QUALIFICATION_SCORE":
        raise ValueError("v1 disposition was changed")
    freeze = manifest["qualification_freeze"]
    if sha256((root / freeze["path"]).read_bytes()) != freeze["raw_sha256"]:
        raise ValueError("v1 frozen qualification changed")
    records = manifest["retained_calls"]
    call_root = root / records["root"]
    paths = sorted(call_root.rglob("*.json"))
    rows = [{"path": str(path.relative_to(call_root)), "sha256": sha256(path.read_bytes())} for path in paths]
    if len(rows) != records["record_count"]:
        raise ValueError("retained call count changed")
    row_hash = sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    if row_hash != records["sorted_relative_path_and_raw_sha256_record_set_sha256"]:
        raise ValueError("retained call record bytes changed")
    for slot, expected_count in (("canary", 1), ("A", 20), ("B", 20)):
        subset = list((call_root / slot).glob("*.json"))
        if len(subset) != expected_count:
            raise ValueError(f"retained {slot} call count changed")
        for path in subset:
            call = json.loads(path.read_text(encoding="utf-8"))
            if call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED" or call["attempt_count"] != 1:
                raise ValueError(f"invalid retained call: {path}")
    for case_id, expected_gold, expected_actual in (("at-ho-05", 2, 4), ("at-ho-06", 4, 5)):
        suite = json.loads((root / "research/explanation_fidelity/qualification/evidence-calibration-atomization-v1.json").read_text())
        case = next(case for case in suite["cases"] if case["case_id"] == case_id)
        if len(case["expected"]) != expected_gold:
            raise ValueError(f"v1 gold count changed: {case_id}")
        for slot in ("A", "B"):
            call = json.loads((call_root / slot / f"{case_id}.json").read_text())
            if len(call["parsed_final"]["claims"]) != expected_actual:
                raise ValueError(f"v1 returned claim count changed: {case_id}/{slot}")
    return {"status": "PASS_RETAINED_INVALID_REFERENCE", "retained_records": len(rows),
            "qualification_passed": False, "pilot_bank_extracted": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
