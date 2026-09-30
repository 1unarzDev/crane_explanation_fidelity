#!/usr/bin/env python3
"""Bind an uncalled v2 role-reference desk review without qualifying the task."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_atomization import uncovered_text
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, RETURN_SCHEMA, validate


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/annotation/evidence-calibration-claim-role-v2-construction-desk-review.json"


def audit(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-claim-role-v2-construction-desk-review/v1"
            or manifest.get("status") != "PROVISIONAL_AGENT_ASSISTED_DESK_REVIEW_SECOND_REVIEW_PENDING"
            or any(manifest.get(key) is not False for key in
                   ("second_independent_reference_review_complete", "qualification_freeze_authorized",
                    "pilot_role_annotation_authorized", "endpoint_scoring_authorized", "human_validation_claimed"))
            or manifest.get("model_calls_performed") != 0
            or manifest.get("confirmation_independent_n") != 0
            or manifest.get("replication_independent_n") != 0):
        raise ValueError("v2 desk-review authorization boundary changed")
    for key in ("suite", "prompt", "return_schema"):
        item = manifest[key]
        if hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["raw_sha256"]:
            raise ValueError(f"v2 desk-review component changed: {key}")
    suite = json.loads((ROOT / manifest["suite"]["path"]).read_text(encoding="utf-8"))
    if suite.get("status") != "UNCALLED_CONSTRUCTION_DRAFT_NOT_FROZEN":
        raise ValueError("v2 suite status changed")
    cases = suite["cases"]
    rows = manifest["reviewed_cases"]
    if ([row["case_id"] for row in rows] != [case["case_id"] for case in cases]
            or len(rows) != manifest["reviewed_case_count"]
            or sum(len(case["claims"]) for case in cases) != manifest["reviewed_atom_count"]):
        raise ValueError("v2 desk-review case inventory changed")
    uncovered = 0
    for row, case in zip(rows, cases, strict=True):
        if (row["split"] != case["split"] or row["atomic_meaning_count"] != len(case["claims"])
                or row["desk_review"] != "PROVISIONAL_PRECALL_ACCEPT" or not row["review_note"]):
            raise ValueError("v2 desk-review row changed")
        payload = {"schema": INPUT_SCHEMA, "opaque_response_id": case["case_id"],
                   "response_text": case["response_text"], "claims": case["claims"]}
        returned = {"schema": RETURN_SCHEMA, "opaque_response_id": case["case_id"],
                    "claim_roles": case["expected"],
                    "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT"}
        validate(payload, returned)
        uncovered += bool(uncovered_text(case["response_text"], case["claims"]))
    if uncovered != manifest["substantial_uncovered_text_cases"] or uncovered != 0:
        raise ValueError("v2 reference has substantial uncovered text")
    return {"schema": "crane-evidence-calibration-claim-role-v2-desk-review-audit/v1",
            "status": "PASS_PROVISIONAL_SECOND_REVIEW_PENDING", "cases": len(cases),
            "atoms": manifest["reviewed_atom_count"], "qualification_freeze_authorized": False,
            "endpoint_scoring_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
