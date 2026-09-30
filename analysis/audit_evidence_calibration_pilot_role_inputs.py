#!/usr/bin/env python3
"""Verify the blind pilot role bundle is exactly rebuilt from reviewed inventories."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_evidence_calibration_pilot_role_inputs import OUTPUT, ROOT, build
from evidence_calibration_io import canonical_json_bytes


MANIFEST = ROOT / "manifests/study/evidence-calibration-pilot-role-inputs-v1.json"
QUALIFICATION = ROOT / "manifests/study/evidence-calibration-claim-role-v2r2-qualification-outcome.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(manifest_path: Path = MANIFEST, bundle_path: Path = OUTPUT) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    qualification = json.loads(QUALIFICATION.read_text(encoding="utf-8"))
    expected = build()
    raw = canonical_json_bytes(expected) + b"\n"
    actual = bundle_path.read_bytes()
    if (
        manifest.get("schema") != "crane-evidence-calibration-pilot-role-input-manifest/v1-development"
        or manifest.get("status") != "REVIEWED_INPUTS_ONLY_NO_PILOT_ROLE_CALL"
        or manifest.get("bundle") != {
            "path": str(OUTPUT.relative_to(ROOT)),
            "raw_sha256": hashlib.sha256(raw).hexdigest(),
            "response_count": 114,
            "atomic_claim_count": 1084,
        }
        or manifest.get("qualification") != {
            "path": str(QUALIFICATION.relative_to(ROOT)), "raw_sha256": digest(QUALIFICATION),
            "qualified_scope": "SYNTHETIC_STANCE_KIND_POLARITY_ONLY",
        }
        or qualification["status"] != "PASS_SYNTHETIC_STANCE_KIND_POLARITY_ONLY"
        or actual != raw
        or manifest.get("method_key_opened") is not False
        or manifest.get("evaluator_truth_opened") is not False
        or manifest.get("model_call_attempted") is not False
        or manifest.get("pilot_role_annotation_authorized") is not False
        or manifest.get("support_annotation_authorized") is not False
        or manifest.get("endpoint_scoring_authorized") is not False
        or manifest.get("p11_authorized") is not False
        or manifest.get("confirmation_independent_n") != 0
        or manifest.get("replication_independent_n") != 0
    ):
        raise ValueError("pilot role input bundle or scientific boundary changed")
    return {
        "schema": "crane-evidence-calibration-pilot-role-input-audit/v1",
        "status": "PASS_REBUILT_BLIND_INPUTS_NO_MODEL_CALL",
        "response_count": expected["response_count"],
        "atomic_claim_count": expected["atomic_claim_count"],
        "manual_inventory_responses": expected["manual_inventory_response_count"],
        "pilot_role_annotation_authorized": False,
        "endpoint_scoring_authorized": False,
        "p11_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
