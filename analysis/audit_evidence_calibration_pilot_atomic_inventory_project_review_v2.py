#!/usr/bin/env python3
"""Verify the amended, method-blind 52-response development inventory review."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_inventory_prefix_project_review import REVIEW as PRIOR, audit as audit_prior
from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-atomic-inventory-project-review-v2.json"
FORM_ROOT = ROOT / "model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/atomization-review-v1"
COMMAND_SENTENCE = "A valid delivered command stream is present."
COMMAND_ATOMS = (
    "A command stream is present.",
    "The command stream is valid.",
    "The command stream was delivered.",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path = REVIEW) -> dict:
    audit_prior()
    review = json.loads(path.read_text(encoding="utf-8"))
    if (review.get("schema") != "crane-evidence-calibration-pilot-atomic-inventory-project-review/v2-development"
            or review.get("status") != "PARTIAL_52_RESPONSE_REVIEW_SUPERSEDES_PREFIX_V1"
            or review.get("supersedes_review_raw_sha256") != digest(PRIOR)
            or ROOT / review.get("review_form_root", "") != FORM_ROOT
            or review.get("method_identity_opened") is not False
            or review.get("evaluator_truth_opened") is not False
            or any(review.get(key) is not False for key in
                   ("whole_bank_inventory_complete", "support_annotation_authorized",
                    "endpoint_scoring_authorized", "p11_authorized"))
            or review.get("confirmation_independent_n") != 0
            or review.get("replication_independent_n") != 0):
        raise ValueError("v2 inventory project-review governance boundary changed")
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    prior_rows = {row["opaque_response_id"]: row for row in prior["rows"]}
    declaration, entries, _, _, _, _ = load_declared_inputs()
    bank = {entry["opaque_response_id"]: entry for entry in entries}
    selected = set(prior_rows)
    for form_path in FORM_ROOT.glob("*.json"):
        if form_path.stem in selected:
            continue
        form = json.loads(form_path.read_text(encoding="utf-8"))
        if (len(form["atomic_claim_candidates"]) <= 5 and not form["unresolved_spans"]
                and not form["uncovered_text_for_reviewer_triage"]):
            selected.add(form_path.stem)
    rows = review["rows"]
    if (len(rows) != 52 or len({row["opaque_response_id"] for row in rows}) != 52
            or {row["opaque_response_id"] for row in rows} != selected):
        raise ValueError("v2 inventory review does not cover its exact declared response set")
    call_root = ROOT / declaration["output_root"]
    original_total = final_total = 0
    splits = []
    for row in rows:
        response_id = row["opaque_response_id"]
        form_path = FORM_ROOT / f"{response_id}.json"
        form = json.loads(form_path.read_text(encoding="utf-8"))
        call_path = call_root / f"{response_id}.json"
        call = json.loads(call_path.read_text(encoding="utf-8"))
        candidates = form["atomic_claim_candidates"]
        original_count = len(candidates)
        if (digest(form_path) != row["form_raw_sha256"]
                or form["blind_bank_raw_sha256"] != review["blind_bank_raw_sha256"]
                or form["response_text"] != bank[response_id]["response_text"]
                or form["extractor_call_raw_sha256"] != digest(call_path)
                or call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"
                or len(call["parsed_final"]["claims"]) != original_count
                or any({key: claim[key] for key in ("response_span", "claim_text")}
                       != {key: candidate[key] for key in ("response_span", "claim_text")}
                       for claim, candidate in zip(call["parsed_final"]["claims"], candidates, strict=True))
                or row["original_candidate_count"] != original_count
                or row["unresolved_spans"] != form["unresolved_spans"]
                or row["inventory_complete_after_review"] is not True):
            raise ValueError(f"v2 reviewed inventory differs from retained blind source: {response_id}")
        split = (form["response_text"].startswith(COMMAND_SENTENCE)
                 and candidates[0]["claim_text"] == COMMAND_SENTENCE)
        if split:
            splits.append(response_id)
        expected_added = ([{"response_span": COMMAND_SENTENCE, "claim_text": claim}
                           for claim in COMMAND_ATOMS] if split else [])
        if (row["accepted_candidate_indices"] != (list(range(1, original_count)) if split
                                                   else list(range(original_count)))
                or row["rejected_candidate_indices"] != ([0] if split else [])
                or row["appended_atomic_claims"] != expected_added
                or row["approved_claim_text_replacements"]
                   != prior_rows.get(response_id, {}).get("approved_claim_text_replacements", {})
                or row["review_set"] != ("AMENDED_PREFIX_17" if response_id in prior_rows
                                         else "ADDED_SHORT_35")):
            raise ValueError(f"v2 atomic split or earlier repair changed: {response_id}")
        original_total += original_count
        final_total += len(row["accepted_candidate_indices"]) + len(expected_added)
    if (sorted(splits) != review["split_command_stream_response_ids"]
            or len(splits) != 11 or review["reviewed_response_count"] != 52
            or review["original_candidate_count"] != original_total
            or review["final_atomic_claim_count"] != final_total
            or original_total != 274 or final_total != 296):
        raise ValueError("v2 inventory review totals or split identities changed")
    return {"schema": "crane-evidence-calibration-pilot-atomic-inventory-project-review-audit/v2",
            "status": "PASS_BOUND_PARTIAL_52_RESPONSE_REVIEW", "reviewed_responses": 52,
            "final_atomic_claims": final_total, "composite_candidates_split": len(splits),
            "remaining_unreviewed_forms": 61, "whole_bank_inventory_complete": False,
            "support_annotation_authorized": False, "endpoint_scoring_authorized": False,
            "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
