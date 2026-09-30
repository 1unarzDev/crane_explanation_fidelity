#!/usr/bin/env python3
"""Bind the remaining complete method-blind pilot inventories without scoring them."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_deictic_limitation_review import REVIEW as PRIOR, audit as audit_prior
from audit_evidence_calibration_pilot_atomic_inventory_project_review_v2 import FORM_ROOT
from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-remaining-complete-inventories-v1.json"
EARLIER_REVIEWS = (
    ROOT / "manifests/annotation/evidence-calibration-pilot-atomic-inventory-project-review-v2.json",
    ROOT / "manifests/annotation/evidence-calibration-pilot-atomic-inventory-batch-9-review-v1.json",
    PRIOR,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path = REVIEW) -> dict:
    audit_prior()
    review = json.loads(path.read_text(encoding="utf-8"))
    if (
        review.get("schema") != "crane-evidence-calibration-pilot-remaining-complete-inventories/v1-development"
        or review.get("status") != "COMPLETE_ANSWER_ONLY_FORMS_REVIEWED_DEVELOPMENT_ONLY"
        or review.get("previous_review_raw_sha256") != digest(PRIOR)
        or ROOT / review.get("review_form_root", "") != FORM_ROOT
        or review.get("method_identity_opened") is not False
        or review.get("evaluator_truth_opened") is not False
        or any(review.get(key) is not False for key in
               ("whole_bank_inventory_complete", "support_annotation_authorized",
                "endpoint_scoring_authorized", "p11_authorized"))
        or review.get("confirmation_independent_n") != 0
        or review.get("replication_independent_n") != 0
    ):
        raise ValueError("remaining-inventory governance boundary changed")

    previous_ids = set()
    for prior_path in EARLIER_REVIEWS:
        previous_ids.update(row["opaque_response_id"] for row in json.loads(prior_path.read_text())["rows"])
    forms = {p.stem: p for p in FORM_ROOT.glob("*.json")}
    remaining_ids = set(forms) - previous_ids
    unresolved_ids = {response_id for response_id in remaining_ids
                      if json.loads(forms[response_id].read_text())["unresolved_spans"]}
    selected_ids = remaining_ids - unresolved_ids
    rows = review["rows"]
    if (
        len(forms) != 113 or len(previous_ids) != 71
        or len(selected_ids) != 39 or len(unresolved_ids) != 3
        or len(rows) != 39 or len({row["opaque_response_id"] for row in rows}) != 39
        or {row["opaque_response_id"] for row in rows} != selected_ids
        or review["remaining_question_dependent_response_ids"] != sorted(unresolved_ids)
    ):
        raise ValueError("review does not cover exactly the 39 remaining complete answer-only forms")

    declaration, entries, _, _, _, _ = load_declared_inputs()
    bank = {entry["opaque_response_id"]: entry for entry in entries}
    call_root = ROOT / declaration["output_root"]
    claim_count = 0
    for row in rows:
        response_id = row["opaque_response_id"]
        form_path = forms[response_id]
        form = json.loads(form_path.read_text(encoding="utf-8"))
        call_path = call_root / f"{response_id}.json"
        call = json.loads(call_path.read_text(encoding="utf-8"))
        claims = form["atomic_claim_candidates"]
        if (
            digest(form_path) != row["form_raw_sha256"]
            or form["blind_bank_raw_sha256"] != review["blind_bank_raw_sha256"]
            or form["extractor_call_raw_sha256"] != digest(call_path)
            or form["response_text"] != bank[response_id]["response_text"]
            or call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"
            or len(call["parsed_final"]["claims"]) != len(claims)
            or row["original_candidate_count"] != len(claims)
            or row["accepted_candidate_indices"] != list(range(len(claims)))
            or row["rejected_candidate_indices"] != []
            or row["appended_atomic_claims"] != []
            or row["inventory_complete_after_review"] is not True
            or row["uncovered_text_disposition"] != (
                "CITATION_MARKUP_OR_PUNCTUATION_ONLY"
                if form["uncovered_text_for_reviewer_triage"] else "NONE"
            )
            or form["method_identity_visible"] is not False
            or form["extractor_abstraction_tags_used"] is not False
            or "method_id" in form
            or form["unresolved_spans"]
        ):
            raise ValueError(f"review differs from retained blind source: {response_id}")
        claim_count += len(claims)
    if (review["reviewed_response_count"] != 39
            or review["original_candidate_count"] != claim_count
            or review["final_atomic_claim_count"] != claim_count):
        raise ValueError("review totals changed")
    return {
        "schema": "crane-evidence-calibration-pilot-remaining-complete-inventories-audit/v1",
        "status": "PASS_BOUND_39_COMPLETE_ANSWER_ONLY_FORMS",
        "reviewed_responses_total": 110,
        "remaining_question_dependent_forms": 3,
        "remaining_unknown_disposition_requests": 1,
        "batch_final_atomic_claims": claim_count,
        "whole_bank_inventory_complete": False,
        "support_annotation_authorized": False,
        "endpoint_scoring_authorized": False,
        "p11_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
