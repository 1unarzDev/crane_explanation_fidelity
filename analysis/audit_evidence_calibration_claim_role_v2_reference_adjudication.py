#!/usr/bin/env python3
"""Verify retained synthetic reviewer critique and uncalled versioned repair."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_atomization import uncovered_text
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, RETURN_SCHEMA, validate


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifests/annotation/evidence-calibration-claim-role-v2-reference-review-adjudication.json"
VALID = "STRUCTURALLY_VALID_REFERENCE_REVIEW_UNADJUDICATED"


def audit(path: Path = MANIFEST) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if (manifest.get("schema") != "crane-evidence-calibration-claim-role-v2-reference-review-adjudication/v1"
            or manifest.get("status") != "REVIEWER_DEFECTS_ACCEPTED_REPAIRED_IN_UNCALLED_VERSIONED_CANDIDATE"
            or any(manifest.get(key) is not False for key in
                   ("revised_candidate_frozen", "role_qualification_authorized",
                    "pilot_role_annotation_authorized", "endpoint_scoring_authorized", "human_validation_claimed"))
            or manifest.get("classifier_calls_on_original_or_revised_suite") != 0
            or manifest.get("confirmation_independent_n") != 0
            or manifest.get("replication_independent_n") != 0):
        raise ValueError("reference adjudication authorization boundary changed")
    sources = {}
    for key in ("original_suite", "original_prompt", "review_request", "nonstudy_canary",
                "review_call", "revised_suite", "revised_prompt"):
        item = manifest[key]
        raw = (ROOT / item["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item["raw_sha256"]:
            raise ValueError(f"reference adjudication component changed: {key}")
        sources[key] = json.loads(raw) if key in {"original_suite", "review_request", "nonstudy_canary",
                                                       "review_call", "revised_suite"} else raw.decode("utf-8")
    request = sources["review_request"]
    for key, source_key in (("suite", "original_suite"), ("candidate_prompt", "original_prompt")):
        if request[key]["raw_sha256"] != manifest[source_key]["raw_sha256"]:
            raise ValueError("review request no longer binds original inputs")
    original = sources["original_suite"]
    revised = sources["revised_suite"]
    if (original.get("status") != "UNCALLED_CONSTRUCTION_DRAFT_NOT_FROZEN"
            or revised.get("status") != "UNCALLED_REVISED_CONSTRUCTION_DRAFT_NOT_FROZEN"):
        raise ValueError("synthetic suite status changed")
    old_cases, new_cases = original["cases"], revised["cases"]
    if ([case["case_id"] for case in old_cases] != [case["case_id"] for case in new_cases]
            or len(old_cases) != manifest["reviewed_case_count"]):
        raise ValueError("revised suite case inventory changed")
    for mode in ("nonstudy_canary", "review_call"):
        call = sources[mode]
        if (call.get("status") != VALID or call.get("attempt_count") != 1
                or call.get("quality_driven_retries") != 0 or call.get("return_code") != 0
                or call.get("timed_out") is not False or call.get("invalid_event") is not None
                or call.get("method_key_accessed") is not False
                or call.get("pilot_answers_included") is not False
                or call.get("credential_persisted") is not False
                or json.loads(call["raw_final"]) != call["parsed_final"]):
            raise ValueError("retained synthetic review call invalid")
        if call["request_identity"]["request_raw_sha256"] != manifest["review_request"]["raw_sha256"]:
            raise ValueError("synthetic review call request identity changed")
    reviewer = sources["review_call"]["parsed_final"]
    rows = reviewer["case_reviews"]
    if [row["case_id"] for row in rows] != [case["case_id"] for case in old_cases]:
        raise ValueError("reviewed case order changed")
    flagged = [row for row in rows if row["status"] == "ISSUE"]
    if (len(flagged) != manifest["flagged_case_count"]
            or len(reviewer["global_issues"]) != manifest["global_issue_count"]
            or [row["case_id"] for row in flagged] != [row["case_id"] for row in manifest["case_findings"]]):
        raise ValueError("reviewer finding inventory changed")
    for row, finding in zip(flagged, manifest["case_findings"], strict=True):
        if (row["issues"] != finding["reviewer_issues"]
                or finding["project_disposition"] != "ACCEPTED_REPAIRED_IN_VERSIONED_CANDIDATE"
                or not finding["resolution"]):
            raise ValueError("reviewer case finding changed")
    for issue, finding in zip(reviewer["global_issues"], manifest["global_findings"], strict=True):
        if issue != finding["reviewer_issue"] or not finding["resolution"]:
            raise ValueError("reviewer global finding changed")
    for case in new_cases:
        payload = {"schema": INPUT_SCHEMA, "opaque_response_id": case["case_id"],
                   "response_text": case["response_text"], "claims": case["claims"]}
        returned = {"schema": RETURN_SCHEMA, "opaque_response_id": case["case_id"],
                    "claim_roles": case["expected"],
                    "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT"}
        validate(payload, returned)
        if uncovered_text(case["response_text"], case["claims"]):
            raise ValueError("revised synthetic case has uncovered text")
    return {"schema": "crane-evidence-calibration-claim-role-v2-reference-adjudication-audit/v1",
            "status": "PASS_BOUND_REPAIR_UNCALLED", "reviewed_cases": len(rows),
            "flagged_cases": len(flagged), "global_issues": len(reviewer["global_issues"]),
            "revised_candidate_frozen": False, "endpoint_scoring_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
