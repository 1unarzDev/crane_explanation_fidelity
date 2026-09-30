#!/usr/bin/env python3
"""Verify the second blinded project review batch and preserve its closed scoring gate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_atomic_inventory_project_review_v2 import (
    COMMAND_ATOMS, COMMAND_SENTENCE, FORM_ROOT, REVIEW as PRIOR, audit as audit_prior,
)
from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-atomic-inventory-batch-9-review-v1.json"
PAIR_IDS = {"ax-29e5692faa220a136a8dc8b9f69da44b",
            "ax-4acdcf48d44b117b92730636bddd1ee2"}
SPLIT_ID = "ax-4e2a3ed8c6e3de96f1bfd4c07b45af9e"
TRACE_DUPLICATE_INDICES = {
    "ax-4acdcf48d44b117b92730636bddd1ee2": [6, 7],
    "ax-cc3206f1fc25ba97d96b9c8d13968a71": [3, 4],
}
DELIVERY_ID = "ax-29e5692faa220a136a8dc8b9f69da44b"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path = REVIEW) -> dict:
    audit_prior()
    review = json.loads(path.read_text(encoding="utf-8"))
    if (review.get("schema") != "crane-evidence-calibration-pilot-atomic-inventory-incremental-review/v1-development"
            or review.get("status") != "BATCH_9_REVIEWED_DEVELOPMENT_ONLY"
            or review.get("previous_review_raw_sha256") != digest(PRIOR)
            or ROOT / review.get("review_form_root", "") != FORM_ROOT
            or review.get("method_identity_opened") is not False
            or review.get("evaluator_truth_opened") is not False
            or any(review.get(key) is not False for key in
                   ("whole_bank_inventory_complete", "support_annotation_authorized",
                    "endpoint_scoring_authorized", "p11_authorized"))
            or review.get("confirmation_independent_n") != 0
            or review.get("replication_independent_n") != 0):
        raise ValueError("batch-9 inventory governance boundary changed")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    prior_ids = {row["opaque_response_id"] for row in prior["rows"]}
    selected = set(PAIR_IDS)
    for form_path in FORM_ROOT.glob("*.json"):
        if form_path.stem in prior_ids:
            continue
        form = json.loads(form_path.read_text(encoding="utf-8"))
        if (len(form["atomic_claim_candidates"]) <= 9 and not form["unresolved_spans"]
                and not form["uncovered_text_for_reviewer_triage"]):
            selected.add(form_path.stem)
    rows = review["rows"]
    if (len(rows) != 9 or len({row["opaque_response_id"] for row in rows}) != 9
            or {row["opaque_response_id"] for row in rows} != selected):
        raise ValueError("batch-9 review does not cover its exact declared response set")
    declaration, entries, _, _, _, _ = load_declared_inputs()
    bank = {entry["opaque_response_id"]: entry for entry in entries}
    call_root = ROOT / declaration["output_root"]
    original_total = final_total = 0
    for row in rows:
        response_id = row["opaque_response_id"]
        form_path = FORM_ROOT / f"{response_id}.json"
        form = json.loads(form_path.read_text(encoding="utf-8"))
        call_path = call_root / f"{response_id}.json"
        call = json.loads(call_path.read_text(encoding="utf-8"))
        claims = form["atomic_claim_candidates"]
        count = len(claims)
        if (digest(form_path) != row["form_raw_sha256"]
                or form["response_text"] != bank[response_id]["response_text"]
                or form["blind_bank_raw_sha256"] != review["blind_bank_raw_sha256"]
                or form["extractor_call_raw_sha256"] != digest(call_path)
                or call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"
                or len(call["parsed_final"]["claims"]) != count
                or row["original_candidate_count"] != count
                or row["inventory_complete_after_review"] is not True
                or form["unresolved_spans"] or form["uncovered_text_for_reviewer_triage"]):
            raise ValueError(f"batch-9 review differs from retained blind source: {response_id}")
        rejected = ([0] if response_id == SPLIT_ID else
                    TRACE_DUPLICATE_INDICES.get(response_id, []))
        added = ([{"response_span": COMMAND_SENTENCE, "claim_text": claim}
                  for claim in COMMAND_ATOMS] if response_id == SPLIT_ID else
                 [{"response_span": "Delivered commanded motion",
                   "claim_text": "The commanded motion was delivered."}] if response_id == DELIVERY_ID else [])
        if (row["accepted_candidate_indices"] != [i for i in range(count) if i not in rejected]
                or row["rejected_candidate_indices"] != rejected
                or row["appended_atomic_claims"] != added
                or any(item["response_span"] not in form["response_text"] for item in added)):
            raise ValueError(f"batch-9 atomic disposition changed: {response_id}")
        original_total += count
        final_total += count - len(rejected) + len(added)
    if (original_total != 79 or final_total != 78
            or review["reviewed_response_count"] != 9
            or review["original_candidate_count"] != original_total
            or review["final_atomic_claim_count"] != final_total):
        raise ValueError("batch-9 inventory totals changed")
    return {"schema": "crane-evidence-calibration-pilot-atomic-inventory-batch-9-audit/v1",
            "status": "PASS_BOUND_BLINDED_BATCH_9", "reviewed_responses_total": 61,
            "remaining_unreviewed_forms": 52, "batch_final_atomic_claims": final_total,
            "whole_bank_inventory_complete": False, "support_annotation_authorized": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
