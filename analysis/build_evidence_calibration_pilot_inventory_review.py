#!/usr/bin/env python3
"""Build method-blind review forms for retained pilot atomization candidates."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_atomization import uncovered_text
from evidence_calibration_io import canonical_json_bytes
from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs, load_interruption
from validate_evidence_calibration_atomization import validate


DEFAULT_ROOT = ROOT / "model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/atomization-review-v1"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(output_root: Path = DEFAULT_ROOT) -> dict:
    declaration, entries, _, _, _, _ = load_declared_inputs()
    call_root = ROOT / declaration["output_root"]
    skipped = load_interruption(entries, call_root)
    count = 0
    for entry in entries:
        response_id = entry["opaque_response_id"]
        if response_id == skipped:
            continue
        call_path = call_root / f"{response_id}.json"
        if not call_path.is_file():
            continue
        call = json.loads(call_path.read_text(encoding="utf-8"))
        if call.get("status") != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
            continue
        parsed = call["parsed_final"]
        validate(entry, parsed)
        form = {
            "schema": "crane-evidence-calibration-blind-inventory-review-form/v1",
            "status": "PROJECT_REVIEW_PENDING",
            "opaque_response_id": response_id,
            "blind_bank_raw_sha256": declaration["blinded_bank"]["raw_sha256"],
            "extractor_call_raw_sha256": sha256(call_path.read_bytes()),
            "response_text": entry["response_text"],
            "atomic_claim_candidates": [
                {"candidate_index": index, "response_span": claim["response_span"],
                 "claim_text": claim["claim_text"]}
                for index, claim in enumerate(parsed["claims"])
            ],
            "unresolved_spans": parsed["unresolved_spans"],
            "uncovered_text_for_reviewer_triage": uncovered_text(entry["response_text"], parsed["claims"]),
            "review_fields": {
                "accepted_candidate_indices": None,
                "rejected_candidate_indices": None,
                "omitted_atomic_claims": None,
                "inventory_complete_after_review": None,
                "source_or_non_diagnostic_claim_indices": None,
                "reviewer_attestation": None,
            },
            "method_identity_visible": False,
            "extractor_abstraction_tags_used": False,
            "support_annotation_authorized": False,
        }
        path = output_root / f"{response_id}.json"
        raw = canonical_json_bytes(form) + b"\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if path.read_bytes() != raw:
                raise ValueError(f"refusing to overwrite changed blind review form: {response_id}")
        else:
            path.write_bytes(raw)
        count += 1
    return {"schema": "crane-evidence-calibration-blind-inventory-review-build/v1",
            "forms": count, "retained_ambiguous_technical_interruption": 1 if skipped else 0,
            "all_forms_pending": True, "method_key_opened": False,
            "support_annotation_authorized": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    print(json.dumps(build(args.output_root), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
