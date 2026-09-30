#!/usr/bin/env python3
"""Verify the blinded 17-response project inventory review and closed scoring gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_inventory_triage import (
    DEFAULT_MANIFEST as TRIAGE, DEFAULT_PREFIX_REVIEW as PRIOR, EXPECTED_REPAIRS, ROOT,
    audit as audit_triage,
)


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-inventory-prefix-project-review-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path = REVIEW) -> dict:
    audit_triage()
    review = json.loads(path.read_text(encoding="utf-8"))
    if (review.get("schema") != "crane-evidence-calibration-pilot-inventory-prefix-project-review/v1"
            or review.get("status") != "PREFIX_17_ATOMIC_INVENTORIES_PROJECT_REVIEWED_DEVELOPMENT_ONLY"
            or review.get("prior_provisional_review_raw_sha256") != digest(PRIOR)
            or review.get("prior_triage_raw_sha256") != digest(TRIAGE)
            or review.get("method_identity_opened") is not False
            or review.get("evaluator_truth_opened") is not False
            or review.get("semantic_inventory_approved_for_reviewed_prefix") is not True
            or any(review.get(key) is not False for key in
                   ("whole_bank_inventory_complete", "support_annotation_authorized",
                    "endpoint_scoring_authorized", "p11_authorized"))
            or review.get("confirmation_independent_n") != 0
            or review.get("replication_independent_n") != 0):
        raise ValueError("prefix project-review governance boundary changed")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    expected_ids = {row["opaque_response_id"] for row in prior["per_response_provisional_disposition"]}
    rows = review["rows"]
    if (len(rows) != 17 or len({row["opaque_response_id"] for row in rows}) != 17
            or {row["opaque_response_id"] for row in rows} != expected_ids):
        raise ValueError("prefix project review does not cover the exact 17 responses")
    root = ROOT / review["review_form_root"]
    claims = 0
    observed_repairs = {}
    for row in rows:
        response_id = row["opaque_response_id"]
        form_path = root / f"{response_id}.json"
        form = json.loads(form_path.read_text(encoding="utf-8"))
        candidates = form["atomic_claim_candidates"]
        count = len(candidates)
        if (digest(form_path) != row["form_raw_sha256"]
                or form["blind_bank_raw_sha256"] != review["blind_bank_raw_sha256"]
                or row["candidate_count"] != count
                or row["accepted_candidate_indices"] != list(range(count))
                or row["rejected_candidate_indices"] != []
                or row["omitted_atomic_claims"] != []
                or row["unresolved_spans_reviewed"] != len(form["unresolved_spans"])
                or row["inventory_complete_after_review"] is not True):
            raise ValueError(f"reviewed inventory differs from retained blind form: {response_id}")
        for key, replacement in row["approved_claim_text_replacements"].items():
            index = int(key)
            if not 0 <= index < count or replacement == candidates[index]["claim_text"]:
                raise ValueError(f"invalid reviewed claim replacement: {response_id}/{key}")
            observed_repairs[(response_id, index)] = replacement
        claims += count
    if (observed_repairs != EXPECTED_REPAIRS or claims != 160
            or review.get("reviewed_responses") != 17
            or review.get("reviewed_candidate_claims") != claims):
        raise ValueError("prefix project review count or actor repairs changed")
    return {"schema": "crane-evidence-calibration-pilot-inventory-prefix-project-review-audit/v1",
            "status": "PASS_BOUND_BLINDED_PREFIX_REVIEW", "reviewed_responses": len(rows),
            "reviewed_candidate_claims": claims, "approved_actor_repairs": len(observed_repairs),
            "whole_bank_inventory_complete": False, "support_annotation_authorized": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
