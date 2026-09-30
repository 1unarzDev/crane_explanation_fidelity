#!/usr/bin/env python3
"""Verify pre-call v2r2 construction review without qualifying the classifier."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_claim_role_v2_reference_adjudication import audit as audit_adjudication
from audit_evidence_calibration_pilot_atomization import uncovered_text
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, RETURN_SCHEMA, validate


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/annotation/evidence-calibration-claim-role-v2r2-final-construction-review.json"


def audit(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-claim-role-v2r2-final-construction-review/v1"
            or manifest.get("status") != "ACCEPTED_FOR_SEPARATE_MEASUREMENT_TASK_FREEZE_ONLY"
            or manifest.get("independent_automated_reference_critique_reviewed") is not True
            or manifest.get("project_adjudication_completed") is not True
            or manifest.get("role_task_freeze_permitted") is not True
            or any(manifest.get(key) is not False for key in
                   ("human_validation_claimed", "role_qualification_authorized",
                    "pilot_role_annotation_authorized", "endpoint_scoring_authorized",
                    "p11_confirmation_authorized"))
            or manifest.get("classifier_calls_on_suite") != 0
            or manifest.get("confirmation_independent_n") != 0
            or manifest.get("replication_independent_n") != 0):
        raise ValueError("v2r2 construction authorization boundary changed")
    sources = {}
    for key in ("suite", "prompt", "return_schema", "prior_failed_v1_suite",
                "independent_reference_adjudication"):
        item = manifest[key]
        raw = (ROOT / item["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["raw_sha256"]:
            raise ValueError(f"v2r2 construction component changed: {key}")
        sources[key] = json.loads(raw) if key.endswith("suite") or key == "independent_reference_adjudication" else raw
    adjudicated = audit_adjudication(ROOT / manifest["independent_reference_adjudication"]["path"])
    if adjudicated["status"] != "PASS_BOUND_REPAIR_UNCALLED":
        raise ValueError("upstream synthetic reference repair not bound")
    if sources["independent_reference_adjudication"]["revised_suite"]["raw_sha256"] != manifest["suite"]["raw_sha256"]:
        raise ValueError("final review suite differs from reviewed repair")
    if sources["independent_reference_adjudication"]["revised_prompt"]["raw_sha256"] != manifest["prompt"]["raw_sha256"]:
        raise ValueError("final review prompt differs from reviewed repair")
    suite = sources["suite"]
    if suite.get("status") != "UNCALLED_REVISED_CONSTRUCTION_DRAFT_NOT_FROZEN":
        raise ValueError("revised suite status changed")
    cases = suite["cases"]
    rows = manifest["case_reviews"]
    if (len(cases) != manifest["case_count"] or len(rows) != len(cases)
            or sum(len(case["claims"]) for case in cases) != manifest["atomic_meaning_count"]
            or sum(case["split"] == "heldout" for case in cases) != manifest["heldout_count"]
            or sum(case["split"] == "development" for case in cases) != manifest["development_count"]
            or len({case["case_id"] for case in cases}) != len(cases)):
        raise ValueError("v2r2 construction case inventory changed")
    old_text = {case["response_text"] for case in sources["prior_failed_v1_suite"]["cases"]}
    if any(case["response_text"] in old_text for case in cases):
        raise ValueError("v2r2 held-out text reuses failed v1 text")
    for case, row in zip(cases, rows, strict=True):
        if (row["case_id"] != case["case_id"] or row["split"] != case["split"]
                or row["atomic_meaning_count"] != len(case["claims"])
                or row["final_project_review"] != "ACCEPTED_PRE_CLASSIFIER_CALL"
                or not row["semantic_note"]):
            raise ValueError("v2r2 final case review changed")
        payload = {"schema": INPUT_SCHEMA, "opaque_response_id": case["case_id"],
                   "response_text": case["response_text"], "claims": case["claims"]}
        returned = {"schema": RETURN_SCHEMA, "opaque_response_id": case["case_id"],
                    "claim_roles": case["expected"],
                    "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT"}
        validate(payload, returned)
        if uncovered_text(case["response_text"], case["claims"]):
            raise ValueError("v2r2 reference has uncovered text")
    return {"schema": "crane-evidence-calibration-claim-role-v2r2-final-review-audit/v1",
            "status": "PASS_FOR_MEASUREMENT_TASK_FREEZE_ONLY", "cases": len(cases),
            "atoms": manifest["atomic_meaning_count"], "role_qualification_authorized": False,
            "pilot_role_annotation_authorized": False, "endpoint_scoring_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
