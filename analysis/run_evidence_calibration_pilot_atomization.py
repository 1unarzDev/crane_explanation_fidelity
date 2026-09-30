#!/usr/bin/env python3
"""Extract development pilot claim inventories from the governed blind bank.

This produces unreviewed inventory candidates only. It never reads the method
join key, evaluator truth, source context, or support annotation packet.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from run_evidence_calibration_atomization_qualification import call_once, load_freeze


ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-atomization-v2-run.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_declared_inputs(declaration_path: Path = DECLARATION):
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    if declaration["schema"] != "crane-evidence-calibration-development-atomization-run/v1":
        raise ValueError("unsupported pilot atomization declaration")
    if declaration["support_annotation_authorized"] or declaration["unqualified_output_fields"] != ["asserted_abstraction_level"]:
        raise ValueError("pilot atomization scope was expanded")
    bank_binding = declaration["blinded_bank"]
    bank_path = ROOT / bank_binding["path"]
    if digest(bank_path) != bank_binding["raw_sha256"]:
        raise ValueError("blinded response bank bytes changed")
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    entries = bank["entries"]
    if len(entries) != bank_binding["response_count"] or len({e["opaque_response_id"] for e in entries}) != len(entries):
        raise ValueError("blinded response count or opaque identity changed")
    if any(set(entry) != {"opaque_response_id", "response_text"} for entry in entries):
        raise ValueError("bank entry has unknown or missing fields")
    qualified = declaration["qualified_inventory_extractor"]
    disposition_path = ROOT / qualified["disposition_path"]
    freeze_path = ROOT / qualified["freeze_path"]
    if digest(disposition_path) != qualified["disposition_raw_sha256"] or digest(freeze_path) != qualified["freeze_raw_sha256"]:
        raise ValueError("qualified extractor binding changed")
    disposition = json.loads(disposition_path.read_text(encoding="utf-8"))
    if disposition["status"] != "QUALIFIED_SYNTHETIC_ATOMIC_INVENTORY_ONLY":
        raise ValueError("extractor inventory qualification is unavailable")
    freeze, _, prompt, schema = load_freeze(freeze_path)
    return declaration, entries, freeze_path, freeze, prompt, schema


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--declaration", type=Path, default=DECLARATION)
    args = parser.parse_args()
    declaration, entries, freeze_path, freeze, prompt, schema = load_declared_inputs(args.declaration)
    output_root = ROOT / declaration["output_root"]
    completed = 0
    for entry in entries:
        response_id = entry["opaque_response_id"]
        if not response_id or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in response_id):
            raise ValueError("unsafe opaque response ID")
        output = output_root / f"{response_id}.json"
        result = call_once(entry=entry, role="pilot-method-blind-atomizer",
                           freeze=freeze, prompt=prompt, schema=schema,
                           output=output, freeze_path=freeze_path)
        if result["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
            print(json.dumps({"status": "STOPPED_ON_RETAINED_FAILURE", "completed_structural_returns": completed,
                              "failed_opaque_response_id": response_id, "support_annotation_authorized": False}, indent=2))
            return 1
        completed += 1
    print(json.dumps({"status": "UNREVIEWED_ATOMIC_INVENTORY_CANDIDATES", "structural_returns": completed,
                      "semantic_completeness_established": False, "abstraction_tags_qualified": False,
                      "support_annotation_authorized": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
