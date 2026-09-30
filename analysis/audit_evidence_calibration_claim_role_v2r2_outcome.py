#!/usr/bin/env python3
"""Verify the project-reviewed v2r2 synthetic role qualification disposition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_claim_role_v2r2_qualification import audit
from run_evidence_calibration_claim_role_v2r2_qualification import ROOT


OUTCOME = ROOT / "manifests/study/evidence-calibration-claim-role-v2r2-qualification-outcome.json"


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify(path: Path = OUTCOME) -> dict:
    outcome = json.loads(path.read_text(encoding="utf-8"))
    if (outcome.get("schema") != "crane-evidence-calibration-claim-role-v2r2-qualification-outcome/v1"
            or outcome.get("status") != "PASS_SYNTHETIC_STANCE_KIND_POLARITY_ONLY"
            or outcome.get("independent_project_semantic_review_complete") is not True
            or outcome.get("role_stance_kind_polarity_qualification_authorized") is not True
            or any(outcome.get(key) is not False for key in
                   ("pilot_role_annotation_authorized", "endpoint_scoring_authorized", "p11_authorized"))
            or outcome.get("quality_driven_retries") != 0
            or outcome.get("confirmation_independent_n") != 0
            or outcome.get("replication_independent_n") != 0):
        raise ValueError("v2r2 role outcome governance boundary changed")
    freeze = ROOT / outcome["freeze_path"]
    if hashlib.sha256(freeze.read_bytes()).hexdigest() != outcome["freeze_raw_sha256"]:
        raise ValueError("v2r2 role freeze changed")
    result = audit(ROOT / outcome["retained_output_root"])
    rows = [{key: row[key] for key in ("slot", "case_id", "intent_raw_sha256", "record_raw_sha256")}
            for row in result["rows"]]
    if (len(rows) != 49
            or canonical_sha256(rows) != outcome["retained_call_record_set_canonical_sha256"]
            or canonical_sha256(result) != outcome["qualification_audit_canonical_sha256"]
            or result["exact_candidate"] is not True
            or result["canary_status"] != "STRUCTURALLY_VALID_ROLE_QUALIFICATION_UNSCORED"):
        raise ValueError("retained v2r2 role calls no longer match disposition")
    for slot in ("A", "B"):
        row = result["per_pass"][slot]
        if (row["structurally_valid_cases"] != 24 or row["heldout_exact_matches"] != 20
                or row["retained_failures"] != 0 or row["interrupted_intents"] != 0):
            raise ValueError(f"v2r2 role pass changed: {slot}")
    return {"schema": "crane-evidence-calibration-claim-role-v2r2-outcome-audit/v1",
            "status": "PASS_BOUND_SYNTHETIC_ROLE_QUALIFICATION", "retained_calls": len(rows),
            "heldout_exact_matches": {slot: result["per_pass"][slot]["heldout_exact_matches"]
                                      for slot in ("A", "B")},
            "pilot_role_annotation_authorized": False, "endpoint_scoring_authorized": False,
            "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
