#!/usr/bin/env python3
"""Validate an atomizer return without treating structural validity as completeness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


LEVELS = {
    "task_outcome", "software_action_failure", "recovery_mechanism",
    "command_motion_discrepancy", "physical_execution_mechanism", "specific_physical_cause",
}


def validate(entry: dict, value: dict) -> dict:
    if set(entry) != {"opaque_response_id", "response_text"}:
        raise ValueError("blinded response entry has missing or unknown fields")
    if set(value) != {"schema", "opaque_response_id", "claims", "unresolved_spans", "attestation"}:
        raise ValueError("atomizer return has missing or unknown fields")
    if (value["schema"] != "crane-evidence-calibration-atomization-return/v1"
            or value["opaque_response_id"] != entry["opaque_response_id"]
            or value["attestation"] != "METHOD_BLIND_EXHAUSTIVE_EXTRACTION_ATTEMPT"):
        raise ValueError("atomizer return identity or attestation mismatch")
    claims = value["claims"]
    if not isinstance(claims, list) or not claims:
        raise ValueError("atomizer must return at least one claim")
    seen = set()
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"response_span", "claim_text", "asserted_abstraction_level"}:
            raise ValueError("atomic claim has missing or unknown fields")
        span, text, level = claim["response_span"], claim["claim_text"], claim["asserted_abstraction_level"]
        if (not isinstance(span, str) or not span.strip() or span not in entry["response_text"]
                or not isinstance(text, str) or not text.strip()
                or not isinstance(level, str) or level not in LEVELS):
            raise ValueError("atomic claim has invalid span, text, or abstraction level")
        identity = (span, text.strip().lower())
        if identity in seen:
            raise ValueError("duplicate atomic claim")
        seen.add(identity)
    unresolved = value["unresolved_spans"]
    if (not isinstance(unresolved, list)
            or any(not isinstance(span, str) or not span.strip() or span not in entry["response_text"] for span in unresolved)
            or len(unresolved) != len(set(unresolved))):
        raise ValueError("unresolved span inventory is invalid")
    return {
        "schema": "crane-evidence-calibration-atomization-validation/v1",
        "opaque_response_id": entry["opaque_response_id"],
        "status": "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED" if not unresolved else "REVIEW_REQUIRED_UNRESOLVED_ASSERTION",
        "claim_count": len(claims),
        "unresolved_span_count": len(unresolved),
        "semantic_completeness_established": False,
        "support_annotation_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", type=Path, required=True)
    parser.add_argument("--return-file", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.entry.read_text()), json.loads(args.return_file.read_text())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
