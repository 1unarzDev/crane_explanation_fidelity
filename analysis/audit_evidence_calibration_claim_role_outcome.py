#!/usr/bin/env python3
"""Bind the failed frozen role qualification to its retained calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_claim_role_qualification import audit
from run_evidence_calibration_claim_role_qualification import FREEZE, ROOT


DEFAULT_OUTCOME = ROOT / "manifests/study/evidence-calibration-claim-role-v1-qualification-outcome.json"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify(path: Path = DEFAULT_OUTCOME) -> dict:
    outcome = json.loads(path.read_text(encoding="utf-8"))
    if (outcome.get("schema") != "crane-evidence-calibration-claim-role-qualification-outcome/v1"
            or outcome.get("status") != "FAILED_FROZEN_EXACT_GATE_PENDING_SEMANTIC_REVIEW"
            or any(outcome.get(key) is not False for key in
                   ("independent_semantic_review_complete", "role_qualification_authorized",
                    "pilot_role_annotation_authorized", "endpoint_scoring_authorized"))
            or outcome.get("quality_driven_retries") != 0
            or outcome.get("freeze_raw_sha256") != hashlib.sha256(FREEZE.read_bytes()).hexdigest()):
        raise ValueError("role outcome governance boundary changed")
    result = audit(ROOT / outcome["retained_output_root"])
    rows = [{key: row[key] for key in ("slot", "case_id", "intent_raw_sha256", "record_raw_sha256")}
            for row in result["rows"]]
    if (len(rows) != outcome["retained_call_count"]
            or canonical_sha256(rows) != outcome["retained_call_record_set_canonical_sha256"]
            or canonical_sha256(result) != outcome["qualification_audit_canonical_sha256"]
            or result["canary_status"] != outcome["canary_status"]
            or result["exact_candidate"] is not False
            or result["all_calls_structurally_valid"] is not True):
        raise ValueError("retained role qualification no longer matches failed outcome")
    for slot in ("A", "B"):
        expected = outcome["isolated_passes"][slot]
        if any(result["per_pass"][slot][key] != value for key, value in expected.items()):
            raise ValueError(f"role pass summary changed: {slot}")
        mismatches = [row["case_id"] for row in result["rows"]
                      if row["slot"] == slot and row["case_id"].startswith("role-ho-")
                      and row.get("reference_exact_match") is False]
        if mismatches != outcome["mismatched_heldout_case_ids"][slot]:
            raise ValueError(f"role mismatch identities changed: {slot}")
    return {"schema": "crane-evidence-calibration-claim-role-outcome-audit/v1",
            "status": "PASS_BOUND_FAILED_QUALIFICATION", "retained_calls": len(rows),
            "heldout_exact_matches": {slot: result["per_pass"][slot]["heldout_exact_matches"]
                                      for slot in ("A", "B")},
            "role_qualification_authorized": False, "endpoint_scoring_authorized": False}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
