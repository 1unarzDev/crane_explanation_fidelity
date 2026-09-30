#!/usr/bin/env python3
"""Audit blind pilot atomization records without certifying semantic completeness."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs, load_interruption
from run_evidence_calibration_atomization_qualification import canonical
from validate_evidence_calibration_atomization import validate


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def uncovered_text(response: str, claims: list[dict]) -> list[str]:
    """Return substantial uncovered text for reviewer triage, not a completeness verdict."""
    covered = [False] * len(response)
    for claim in claims:
        span = claim["response_span"]
        start = 0
        while True:
            index = response.find(span, start)
            if index < 0:
                break
            covered[index:index + len(span)] = [True] * len(span)
            start = index + len(span)
    remainder = "".join(char if not flag else " " for char, flag in zip(response, covered))
    segments = re.split(r"[.!?;\n]+", remainder)
    return [" ".join(segment.split()) for segment in segments
            if len(re.findall(r"[A-Za-z][A-Za-z'-]*", segment)) >= 4]


def audit(output_root: Path, *, allow_incomplete: bool = False) -> dict:
    declaration, entries, freeze_path, _, _, _ = load_declared_inputs()
    freeze_hash = sha256(freeze_path.read_bytes())
    skipped_id = load_interruption(entries, output_root)
    rows = []
    for entry in entries:
        response_id = entry["opaque_response_id"]
        if response_id == skipped_id:
            rows.append({"opaque_response_id": response_id, "status": "RETAINED_AMBIGUOUS_TECHNICAL_INTERRUPTION"})
            continue
        path = output_root / f"{response_id}.json"
        if not path.is_file():
            rows.append({"opaque_response_id": response_id, "status": "MISSING_CALL_RECORD"})
            continue
        call = json.loads(path.read_text(encoding="utf-8"))
        identity = call["request_identity"]
        if (identity["freeze_sha256"] != freeze_hash
                or identity["payload_sha256"] != sha256(canonical(entry))
                or identity["role"] != "pilot-method-blind-atomizer"
                or call["attempt_count"] != 1 or call["quality_driven_retries"] != 0
                or call["method_key_accessed"] is not False):
            raise ValueError(f"call identity or no-retry boundary failed: {response_id}")
        if call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED":
            rows.append({"opaque_response_id": response_id, "status": call["status"],
                         "call_sha256": sha256(path.read_bytes())})
            continue
        parsed = call["parsed_final"]
        validate(entry, parsed)
        rows.append({"opaque_response_id": response_id, "status": "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED",
                     "call_sha256": sha256(path.read_bytes()), "claim_count": len(parsed["claims"]),
                     "unresolved_span_count": len(parsed["unresolved_spans"]),
                     "uncovered_text_for_review": uncovered_text(entry["response_text"], parsed["claims"])})
    missing = sum(row["status"] == "MISSING_CALL_RECORD" for row in rows)
    technical = sum(row["status"] == "RETAINED_AMBIGUOUS_TECHNICAL_INTERRUPTION" for row in rows)
    failed = sum(row["status"] not in {"MISSING_CALL_RECORD", "RETAINED_AMBIGUOUS_TECHNICAL_INTERRUPTION",
                                                   "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"} for row in rows)
    if (missing or failed) and not allow_incomplete:
        raise ValueError(f"pilot atomization has {missing} missing and {failed} failed call records")
    return {"schema": "crane-evidence-calibration-pilot-atomization-audit/v1",
            "bank_sha256": declaration["blinded_bank"]["raw_sha256"],
            "expected_responses": len(entries), "structural_returns": len(entries) - missing - failed - technical,
            "missing_calls": missing, "failed_calls": failed,
            "retained_ambiguous_technical_interruptions": technical,
            "total_claims": sum(row.get("claim_count", 0) for row in rows),
            "responses_with_uncovered_text_for_review": sum(bool(row.get("uncovered_text_for_review")) for row in rows),
            "semantic_completeness_established": False,
            "abstraction_tags_qualified": False, "support_annotation_authorized": False,
            "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "model_outputs/automated_annotations/evidence-calibration-b2-b4-pilot-v1-atomization-v2")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit(args.output_root, allow_incomplete=args.allow_incomplete)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2, sort_keys=True))
    return 0 if result["missing_calls"] == result["failed_calls"] == result["retained_ambiguous_technical_interruptions"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
