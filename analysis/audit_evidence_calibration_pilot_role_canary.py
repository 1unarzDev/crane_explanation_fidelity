#!/usr/bin/env python3
"""Verify the bound non-study role schema canary before pilot role calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from run_evidence_calibration_pilot_claim_roles import CANARY, DECLARATION, ROOT, load_declared
from run_evidence_calibration_claim_role_v2r2_qualification import VALID_STATUS, _payload
from validate_evidence_calibration_claim_roles_v2 import validate


MANIFEST = ROOT / "manifests/operations/evidence-calibration-pilot-role-canary-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(manifest_path: Path = MANIFEST) -> dict:
    declaration, _, _, _, _ = load_declared()
    output = ROOT / declaration["output_root"] / "canary" / f"{CANARY['case_id']}.json"
    intent = output.with_suffix(".intent")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = json.loads(output.read_text(encoding="utf-8"))
    original_intent = json.loads(intent.read_text(encoding="utf-8"))
    if (
        manifest.get("schema") != "crane-evidence-calibration-pilot-role-canary-manifest/v1"
        or manifest.get("status") != "PASS_NON_STUDY_SCHEMA_CANARY"
        or manifest.get("declaration_raw_sha256") != digest(DECLARATION)
        or manifest.get("call_record") != {"path": str(output.relative_to(ROOT)),
                                            "raw_sha256": digest(output)}
        or manifest.get("intent") != {"path": str(intent.relative_to(ROOT)),
                                       "raw_sha256": digest(intent)}
        or manifest.get("study_calls_attempted") != 0
        or manifest.get("method_key_opened") is not False
        or manifest.get("endpoint_scoring_authorized") is not False
        or manifest.get("p11_authorized") is not False
        or record["status"] != VALID_STATUS
        or record["return_code"] != 0
        or record["timed_out"] is not False
        or record["invalid_event"] is not None
        or record["attempt_count"] != 1
        or record["quality_driven_retries"] != 0
        or record["method_key_accessed"] is not False
        or original_intent["request_identity"] != record["request_identity"]
        or original_intent["terminal_record_pending"] is not True
        or record["request_identity"]["slot"] != "canary"
        or record["request_identity"]["model"] != declaration["model"]
        or record["request_identity"]["reasoning_effort"] != declaration["reasoning_effort"]
    ):
        raise ValueError("role schema canary binding or no-study boundary changed")
    parsed = json.loads(record["raw_final"])
    if parsed != record["parsed_final"] or validate(_payload(CANARY, "canary"), parsed) != record["structural_validation"]:
        raise ValueError("canary raw return fails current structural validation")
    return {"status": "PASS_BOUND_NON_STUDY_ROLE_CANARY", "study_calls_attempted": 0,
            "pilot_role_calls_admissible": True, "endpoint_scoring_authorized": False,
            "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
