#!/usr/bin/env python3
"""Verify proposed actor repairs without approving a blind atomic inventory."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from run_evidence_calibration_pilot_atomization import ROOT, load_declared_inputs


MANIFEST = ROOT / "manifests/annotation/evidence-calibration-pilot-full-bank-actor-triage-v1.json"


def audit(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-pilot-full-bank-actor-triage/v1"
            or manifest.get("status") != "PROPOSED_BLIND_TRIAGE_ONLY"
            or any(manifest.get(key) is not False for key in
                   ("semantic_inventory_approved", "support_annotation_authorized", "method_identity_visible"))
            or manifest.get("confirmation_independent_n") != 0
            or manifest.get("replication_independent_n") != 0):
        raise ValueError("triage authorization boundary changed")
    _, entries, _, _, _, _ = load_declared_inputs()
    bank_ids = {entry["opaque_response_id"] for entry in entries}
    if hashlib.sha256((ROOT / manifest["prior_triage_path"]).read_bytes()).hexdigest() != manifest["prior_triage_raw_sha256"]:
        raise ValueError("prior prefix triage changed")
    root = ROOT / manifest["review_form_root"]
    seen = set()
    repair_count = 0
    for row in manifest["findings"]:
        response_id = row["opaque_response_id"]
        if response_id in seen or response_id not in bank_ids:
            raise ValueError("duplicate or non-bank response")
        seen.add(response_id)
        form_path = root / f"{response_id}.json"
        raw = form_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["review_form_raw_sha256"]:
            raise ValueError("blind review form changed")
        form = json.loads(raw)
        if (form["opaque_response_id"] != response_id or form["status"] != "PROJECT_REVIEW_PENDING"
                or form["method_identity_visible"] is not False
                or form["support_annotation_authorized"] is not False):
            raise ValueError("review form boundary changed")
        if not row["proposed_repairs"]:
            raise ValueError("empty actor repair row")
        indices = set()
        for repair in row["proposed_repairs"]:
            index = repair["candidate_index"]
            if index in indices or not isinstance(index, int):
                raise ValueError("duplicate or invalid repair index")
            indices.add(index)
            candidate = form["atomic_claim_candidates"][index]
            if (candidate["candidate_index"] != index
                    or candidate["claim_text"] != repair["original_claim_text"]
                    or "FollowPath" in candidate["claim_text"]
                    or "FollowPath" not in repair["proposed_claim_text"]
                    or "failures" not in candidate["claim_text"]
                    or "FollowPath" not in form["response_text"]):
                raise ValueError("actor repair no longer matches blind response")
            repair_count += 1
    if len(seen) != 7 or repair_count != 8:
        raise ValueError("actor repair inventory changed")
    return {"schema": "crane-evidence-calibration-pilot-full-bank-actor-triage-audit/v1",
            "status": "PASS_BOUND_PROPOSALS_ONLY", "blind_responses": len(seen),
            "proposed_claim_repairs": repair_count, "semantic_inventory_approved": False,
            "support_annotation_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
