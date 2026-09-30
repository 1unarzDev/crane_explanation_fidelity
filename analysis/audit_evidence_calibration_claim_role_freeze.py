#!/usr/bin/env python3
"""Audit the pre-call synthetic assertion-role qualification freeze without model access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from validate_evidence_calibration_claim_roles import INPUT_SCHEMA, RETURN_SCHEMA, validate_claim_roles


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-claim-role-v1-freeze.json"


def _bound(binding: dict) -> dict | str:
    path = ROOT / binding["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != binding["raw_sha256"]:
        raise ValueError(f"frozen component hash mismatch: {binding['path']}")
    if path.suffix in {".md", ".py"}:
        return path.read_text(encoding="utf-8")
    return json.loads(path.read_text(encoding="utf-8"))


def audit(freeze_path: Path = FREEZE) -> dict:
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("schema") != "crane-evidence-calibration-claim-role-qualification-freeze/v1" or freeze.get("status") != "FROZEN_BEFORE_ANY_ROLE_MODEL_CALL":
        raise ValueError("role qualification freeze is absent or invalid")
    suite = _bound(freeze["suite"])
    review = _bound(freeze["construction_review"])
    prompt = _bound(freeze["candidate"]["prompt"])
    return_schema = _bound(freeze["candidate"]["return_schema"])
    runner = _bound(freeze["candidate"]["runner"])
    if (suite["status"] != "FROZEN_SYNTHETIC_ROLE_QUALIFICATION_INPUT_BEFORE_CALLS"
            or review["status"] != "PROJECT_CONSTRUCTION_REVIEW_COMPLETE_BEFORE_ROLE_MODEL_CALLS"
            or review["model_calls_observed"] != 0
            or review["suite"] != freeze["suite"]
            or review["prompt"] != freeze["candidate"]["prompt"]
            or review["return_schema"] != freeze["candidate"]["return_schema"]):
        raise ValueError("pre-call construction review or bindings are inconsistent")
    candidate = freeze["candidate"]
    if (candidate["model"] != "gpt-6-astra" or candidate["reasoning_effort"] != "high"
            or candidate["transport"] != "codex-cli-chatgpt-login-ephemeral/v1"
            or candidate["isolated_passes"] != 2 or candidate["tools"] != "none"
            or candidate["quality_driven_retries"] != 0
            or candidate["method_visible_input"] != ["opaque_response_id", "response_text", "claims"]):
        raise ValueError("role candidate model or input boundary changed")
    if not isinstance(prompt, str) or not prompt.startswith("# Method-blind claim-role classification"):
        raise ValueError("role prompt binding is invalid")
    if not isinstance(runner, str) or "def call_once(" not in runner:
        raise ValueError("role qualification runner binding is invalid")
    if return_schema["properties"]["schema"]["const"] != RETURN_SCHEMA:
        raise ValueError("role return schema binding is invalid")
    cases = suite["cases"]
    if (len(cases) != 24 or len({case["case_id"] for case in cases}) != 24
            or sum(case["split"] == "development" for case in cases) != 4
            or sum(case["split"] == "heldout" for case in cases) != 20
            or [item["case_id"] for item in review["cases"]] != [item["case_id"] for item in cases]):
        raise ValueError("synthetic role case count, split, or construction review changed")
    for case, reviewed in zip(cases, review["cases"], strict=True):
        if (reviewed["atomic_meaning_count"] != len(case["claims"])
                or reviewed["reference_review"] != "ACCEPTED_PRE_CALL"):
            raise ValueError(f"unreviewed atomic reference: {case['case_id']}")
        payload = {"schema": INPUT_SCHEMA, "opaque_response_id": case["case_id"],
                   "response_text": case["response_text"], "claims": case["claims"]}
        if len(case["expected"]) != len(case["claims"]):
            raise ValueError(f"incomplete role reference: {case['case_id']}")
        result = {"schema": RETURN_SCHEMA, "opaque_response_id": case["case_id"],
                  "claim_roles": [{**gold, "rationale_span": claim["response_span"]}
                                  for claim, gold in zip(case["claims"], case["expected"], strict=True)],
                  "attestation": "METHOD_BLIND_ASSERTION_ROLE_ATTEMPT"}
        validate_claim_roles(payload, result)
    gates = freeze["heldout_gates"]
    if (gates["heldout_case_count"] != 20
            or not gates["exact_role_and_level_for_every_reviewed_atomic_claim_per_pass"]
            or not gates["zero_missing_extra_or_reordered_claim_ids_per_pass"]
            or not gates["zero_unresolved_roles_per_pass"]
            or not gates["both_isolated_passes_must_individually_pass"]
            or not gates["independent_project_semantic_review_required"]):
        raise ValueError("role qualification gates were weakened")
    if freeze["pilot_role_annotation_authorized"] or freeze["endpoint_mapping_frozen"] or freeze["independent_episode_n"] != 0 or freeze["confirmatory_alpha_consumed"] != 0:
        raise ValueError("synthetic role freeze claims study authorization")
    return {"schema": "crane-evidence-calibration-claim-role-freeze-audit/v1",
            "status": "PASS_SYNTHETIC_TASK_FROZEN_NO_MODEL_QUALIFICATION",
            "freeze_raw_sha256": hashlib.sha256(freeze_path.read_bytes()).hexdigest(),
            "synthetic_cases": 24, "heldout_cases": 20,
            "model_calls_made_by_audit": 0,
            "pilot_role_annotation_authorized": False,
            "endpoint_scoring_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
