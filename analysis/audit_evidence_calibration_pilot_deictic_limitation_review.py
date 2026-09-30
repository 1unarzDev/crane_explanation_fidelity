#!/usr/bin/env python3
"""Verify reviewed deictic limitation atoms without resolving their missing referent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_atomic_inventory_batch_9 import REVIEW as BATCH_9, audit as audit_batch_9
from audit_evidence_calibration_pilot_atomic_inventory_project_review_v2 import REVIEW as REVIEW_V2, FORM_ROOT
from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-deictic-limitation-review-v1.json"
DEICTIC = "A delivered-command/measured-motion discrepancy does not distinguish these specific physical causes."
DELIVERY = {"response_span": "Delivered commanded motion",
            "claim_text": "The commanded motion was delivered."}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path = REVIEW) -> dict:
    audit_batch_9()
    review = json.loads(path.read_text(encoding="utf-8"))
    if (review.get("schema") != "crane-evidence-calibration-pilot-deictic-limitation-review/v1-development"
            or review.get("status") != "TWELVE_DEICTIC_CLAIMS_REVIEWED_TEN_NEW_INVENTORIES"
            or review.get("previous_batch_review_raw_sha256") != digest(BATCH_9)
            or ROOT / review.get("review_form_root", "") != FORM_ROOT
            or review.get("method_identity_opened") is not False
            or review.get("evaluator_truth_opened") is not False
            or any(review.get(key) is not False for key in
                   ("support_label_assigned", "whole_bank_inventory_complete",
                    "support_annotation_authorized", "endpoint_scoring_authorized", "p11_authorized"))
            or review.get("confirmation_independent_n") != 0
            or review.get("replication_independent_n") != 0):
        raise ValueError("deictic limitation review governance boundary changed")
    prior_ids = {row["opaque_response_id"] for row in json.loads(REVIEW_V2.read_text())["rows"]}
    batch_ids = {row["opaque_response_id"] for row in json.loads(BATCH_9.read_text())["rows"]}
    reviewed_before = prior_ids | batch_ids
    affected = set()
    for form_path in FORM_ROOT.glob("*.json"):
        form = json.loads(form_path.read_text(encoding="utf-8"))
        if "these specific physical causes" in form["response_text"]:
            affected.add(form_path.stem)
    rows = review["rows"]
    if (len(rows) != 12 or len({row["opaque_response_id"] for row in rows}) != 12
            or {row["opaque_response_id"] for row in rows} != affected):
        raise ValueError("deictic review does not cover its exact twelve response texts")
    declaration, entries, _, _, _, _ = load_declared_inputs()
    bank = {entry["opaque_response_id"]: entry for entry in entries}
    call_root = ROOT / declaration["output_root"]
    new_count = old_count = 0
    for row in rows:
        response_id = row["opaque_response_id"]
        form_path = FORM_ROOT / f"{response_id}.json"
        form = json.loads(form_path.read_text(encoding="utf-8"))
        call_path = call_root / f"{response_id}.json"
        call = json.loads(call_path.read_text(encoding="utf-8"))
        candidates = form["atomic_claim_candidates"]
        matches = [claim for claim in candidates if "specific physical causes" in claim["claim_text"]]
        is_new = response_id not in reviewed_before
        if (digest(form_path) != row["form_raw_sha256"]
                or form["response_text"] != bank[response_id]["response_text"]
                or form["blind_bank_raw_sha256"] != review["blind_bank_raw_sha256"]
                or form["extractor_call_raw_sha256"] != digest(call_path)
                or call["status"] != "STRUCTURALLY_VALID_COMPLETENESS_UNQUALIFIED"
                or row["candidate_count"] != len(candidates)
                or len(matches) != 1
                or row["deictic_candidate_index"] != matches[0]["candidate_index"]
                or row["original_candidate_claim_text"] != matches[0]["claim_text"]
                or row["reviewed_replacement_claim_text"] != DEICTIC
                or row["antecedent_status"] != "NO_EXPLICIT_CAUSE_LIST_IN_ANSWER"
                or row["newly_reviewed_response"] is not is_new
                or row["append_delivery_atom"] != (DELIVERY if is_new else None)
                or row["inventory_complete_after_review"] is not True
                or DEICTIC not in form["response_text"]):
            raise ValueError(f"deictic review differs from retained blind answer: {response_id}")
        if is_new:
            if (not form["response_text"].startswith("Delivered commanded motion was not reflected")
                    or form["unresolved_spans"] or form["uncovered_text_for_reviewer_triage"]):
                raise ValueError(f"newly reviewed deictic answer has an open inventory signal: {response_id}")
            new_count += 1
        else:
            old_count += 1
    if (new_count != 10 or old_count != 2 or review["affected_responses"] != 12
            or review["newly_reviewed_responses"] != new_count
            or review["previously_reviewed_responses_amended"] != old_count):
        raise ValueError("deictic review counts changed")
    return {"schema": "crane-evidence-calibration-pilot-deictic-limitation-review-audit/v1",
            "status": "PASS_BOUND_UNRESOLVED_REFERENT", "affected_responses": 12,
            "newly_reviewed_responses": 10, "reviewed_responses_total": 71,
            "remaining_unreviewed_forms": 42, "support_label_assigned": False,
            "support_annotation_authorized": False, "endpoint_scoring_authorized": False,
            "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
