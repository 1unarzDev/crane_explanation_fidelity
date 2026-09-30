#!/usr/bin/env python3
"""Audit a separately frozen synthetic role task without making model calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_claim_role_v2r2_final_review import audit as audit_final_review


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-claim-role-v2r2-freeze.json"


def audit(path: Path = FREEZE) -> dict:
    freeze = json.loads(path.read_text(encoding="utf-8"))
    if (freeze.get("schema") != "crane-evidence-calibration-claim-role-v2r2-qualification-freeze/v1"
            or freeze.get("status") != "FROZEN_BEFORE_ANY_V2R2_ROLE_MODEL_CALL"
            or freeze.get("endpoint_mapping_frozen") is not False
            or freeze.get("pilot_role_annotation_authorized") is not False
            or freeze.get("independent_episode_n") != 0
            or freeze.get("confirmatory_alpha_consumed") != 0.0):
        raise ValueError("v2r2 qualification freeze boundary changed")
    for key in ("suite", "construction_review"):
        item = freeze[key]
        if hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["raw_sha256"]:
            raise ValueError(f"v2r2 freeze component changed: {key}")
    candidate = freeze["candidate"]
    for key in ("prompt", "return_schema", "runner"):
        item = candidate[key]
        if hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["raw_sha256"]:
            raise ValueError(f"v2r2 candidate component changed: {key}")
    if (candidate.get("model") != "gpt-6-astra"
            or candidate.get("reasoning_effort") != "high"
            or candidate.get("transport") != "codex-cli-chatgpt-login-ephemeral/v1"
            or candidate.get("tools") != "none"
            or candidate.get("quality_driven_retries") != 0
            or candidate.get("isolated_passes") != 2):
        raise ValueError("v2r2 classifier configuration changed")
    suite = json.loads((ROOT / freeze["suite"]["path"]).read_text(encoding="utf-8"))
    cases = suite["cases"]
    if (len(cases) != 24 or sum(case["split"] == "development" for case in cases) != 4
            or sum(case["split"] == "heldout" for case in cases) != 20
            or sum(len(case["claims"]) for case in cases) != 39):
        raise ValueError("v2r2 frozen suite inventory changed")
    final_review = audit_final_review(ROOT / freeze["construction_review"]["path"])
    if final_review["status"] != "PASS_FOR_MEASUREMENT_TASK_FREEZE_ONLY":
        raise ValueError("v2r2 final reference review not accepted")
    gates = freeze["heldout_gates"]
    if (gates.get("heldout_case_count") != 20
            or gates.get("both_isolated_passes_must_individually_pass") is not True
            or gates.get("exact_stance_kind_polarity_per_atomic_claim_per_pass") is not True
            or gates.get("zero_missing_extra_or_reordered_claim_ids_per_pass") is not True
            or gates.get("zero_unresolved_roles_per_pass") is not True
            or gates.get("independent_project_semantic_review_required") is not True):
        raise ValueError("v2r2 held-out qualification gates changed")
    return {"schema": "crane-evidence-calibration-claim-role-v2r2-freeze-audit/v1",
            "status": "PASS_SEPARATE_MEASUREMENT_TASK_FROZEN_UNCALLED",
            "synthetic_cases": len(cases), "heldout_cases": 20,
            "pilot_role_annotation_authorized": False, "endpoint_scoring_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
