#!/usr/bin/env python3
"""Audit the three blind pilot inventories requiring the registered question."""

from __future__ import annotations

import json
from pathlib import Path

from audit_evidence_calibration_pilot_remaining_complete_inventories import (
    REVIEW as PRIOR, FORM_ROOT, audit as audit_prior, digest,
)
from build_evidence_calibration_pilot_question_context import OUTPUT as CONTEXT, audit as audit_context
from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-question-dependent-inventories-v1.json"
ONE_WORD_CLAIMS = {
    "ax-99ba577363297382083274a6a2984c00": (
        "No.", "The answer denies that a navigation failure occurred in the successful episode."
    ),
    "ax-e45bb092d71d1f5ef9cc0162cff7110c": (
        "Yes.", "The answer affirms that a navigation failure occurred in the successful episode."
    ),
    "ax-f64508c4a53502524cf470b9e9ed61d1": (
        "Yes.", "The answer affirms that a navigation failure occurred in the successful episode."
    ),
}


def audit(path: Path = REVIEW) -> dict:
    audit_prior()
    audit_context()
    review = json.loads(path.read_text(encoding="utf-8"))
    context = json.loads(CONTEXT.read_text(encoding="utf-8"))
    if (
        review.get("schema") != "crane-evidence-calibration-pilot-question-dependent-inventories/v1-development"
        or review.get("status") != "STRUCTURAL_INVENTORY_REVIEWED_SCOPE_RETAINED"
        or review.get("previous_review_raw_sha256") != digest(PRIOR)
        or review.get("question_context_raw_sha256") != digest(CONTEXT)
        or review.get("method_identity_opened") is not False
        or review.get("evaluator_truth_opened") is not False
        or any(review.get(key) is not False for key in
               ("whole_bank_inventory_complete", "support_annotation_authorized",
                "endpoint_scoring_authorized", "p11_authorized"))
        or review.get("confirmation_independent_n") != 0
        or review.get("replication_independent_n") != 0
    ):
        raise ValueError("question-dependent inventory governance boundary changed")
    rows = review["rows"]
    if (len(rows) != 3 or len({row["opaque_response_id"] for row in rows}) != 3
            or {row["opaque_response_id"] for row in rows} != set(ONE_WORD_CLAIMS)
            or {row["opaque_response_id"] for row in context["rows"]} != set(ONE_WORD_CLAIMS)):
        raise ValueError("question-dependent response set changed")

    declaration, entries, _, _, _, _ = load_declared_inputs()
    bank = {entry["opaque_response_id"]: entry for entry in entries}
    call_root = ROOT / declaration["output_root"]
    original_count = 0
    for row in rows:
        response_id = row["opaque_response_id"]
        form_path = FORM_ROOT / f"{response_id}.json"
        form = json.loads(form_path.read_text(encoding="utf-8"))
        call_path = call_root / f"{response_id}.json"
        call = json.loads(call_path.read_text(encoding="utf-8"))
        claim_count = len(form["atomic_claim_candidates"])
        one_word, claim_text = ONE_WORD_CLAIMS[response_id]
        expected_append = [{"response_span": one_word, "claim_text": claim_text}]
        if (
            digest(form_path) != row["form_raw_sha256"]
            or form["extractor_call_raw_sha256"] != digest(call_path)
            or call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"
            or len(call["parsed_final"]["claims"]) != claim_count
            or form["response_text"] != bank[response_id]["response_text"]
            or form["blind_bank_raw_sha256"] != review["blind_bank_raw_sha256"]
            or form["unresolved_spans"] != [one_word]
            or not form["response_text"].startswith(one_word)
            or row["original_candidate_count"] != claim_count
            or row["accepted_candidate_indices"] != list(range(claim_count))
            or row["rejected_candidate_indices"] != []
            or row["appended_atomic_claims"] != expected_append
            or row["question_dependent_scope"] != "NAVIGATION_FAILURE_SCOPE_REQUIRES_LATER_ROLE_REVIEW"
            or row["inventory_complete_after_review"] is not True
        ):
            raise ValueError(f"question-dependent inventory changed: {response_id}")
        original_count += claim_count
    if (review["reviewed_response_count"] != 3
            or review["original_candidate_count"] != original_count
            or review["final_atomic_claim_count"] != original_count + 3):
        raise ValueError("question-dependent inventory totals changed")
    return {
        "schema": "crane-evidence-calibration-pilot-question-dependent-inventories-audit/v1",
        "status": "PASS_113_STRUCTURAL_FORMS_REVIEWED_ONE_REQUEST_QUARANTINED",
        "reviewed_structural_forms_total": 113,
        "unknown_disposition_requests": 1,
        "question_dependent_scope_still_requires_role_review": 3,
        "support_annotation_authorized": False,
        "endpoint_scoring_authorized": False,
        "p11_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
