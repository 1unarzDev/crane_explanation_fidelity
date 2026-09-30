#!/usr/bin/env python3
"""Run the prospectively declared development-only pilot role task without retry."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from audit_b2_transport_readiness import audit as transport_audit
from audit_evidence_calibration_pilot_role_inputs import audit as audit_inputs
from build_evidence_calibration_pilot_role_inputs import OUTPUT as INPUTS, ROOT
from run_evidence_calibration_claim_role_v2r2_qualification import (
    VALID_STATUS, call_once, load_bound_freeze,
)


DECLARATION = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-pilot-claim-role-v2r2-use-v1.json"
CANARY = {
    "case_id": "pilot-role-schema-canary-v1",
    "response_text": "The recorded action succeeded.",
    "claims": [{"item_id": "c1", "response_span": "The recorded action succeeded.",
                "claim_text": "The recorded action succeeded."}],
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_declared() -> tuple[dict, list[dict], dict, str, dict]:
    audit_inputs()
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze, _, prompt, schema = load_bound_freeze()
    qualification_path = ROOT / declaration["qualification"]["path"]
    bundle = json.loads(INPUTS.read_text(encoding="utf-8"))
    if (
        declaration.get("schema") != "crane-evidence-calibration-pilot-claim-role-use/v1-development"
        or declaration.get("status") != "DECLARED_BEFORE_PILOT_ROLE_CALLS"
        or declaration.get("freeze") != {"path": str(Path("research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-claim-role-v2r2-freeze.json")),
                                          "raw_sha256": digest(ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-claim-role-v2r2-freeze.json")}
        or declaration.get("qualification", {}).get("raw_sha256") != digest(qualification_path)
        or declaration.get("runner") != {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                                          "raw_sha256": digest(Path(__file__).resolve())}
        or json.loads(qualification_path.read_text(encoding="utf-8"))["status"] != "PASS_SYNTHETIC_STANCE_KIND_POLARITY_ONLY"
        or declaration.get("input_bundle") != {"path": str(INPUTS.relative_to(ROOT)),
                                                 "raw_sha256": digest(INPUTS),
                                                 "response_count": 114, "atomic_claim_count": 1084}
        or declaration.get("output_root") != "model_outputs/automated_annotations/evidence-calibration-b2-b4-pilot-v1-role-v2r2"
        or declaration.get("planned_call_count") != 228
        or declaration.get("isolated_passes") != ["A", "B"]
        or declaration.get("quality_driven_retries") != 0
        or declaration.get("model") != freeze["candidate"]["model"]
        or declaration.get("reasoning_effort") != freeze["candidate"]["reasoning_effort"]
        or declaration.get("transport") != freeze["candidate"]["transport"]
        or declaration.get("tools") != "none"
        or declaration.get("canary") != CANARY
        or declaration.get("development_pilot_role_calls_authorized") is not True
        or declaration.get("support_annotation_authorized") is not False
        or declaration.get("endpoint_scoring_authorized") is not False
        or declaration.get("p11_authorized") is not False
        or declaration.get("confirmation_independent_n") != 0
        or declaration.get("replication_independent_n") != 0
        or bundle["response_count"] != 114
        or bundle["atomic_claim_count"] != 1084
    ):
        raise ValueError("pilot role-use declaration differs from qualified inputs or boundary")
    return declaration, bundle["entries"], freeze, prompt, schema


def run(mode: str) -> dict:
    declaration, entries, freeze, prompt, schema = load_declared()
    preflight = transport_audit(Path.home() / ".codex/config.toml", dict(os.environ))
    if preflight["status"] != "READY_FOR_SCHEMA_CANARY":
        raise RuntimeError(f"pilot role transport not ready: {preflight['status']}")
    cli_version = subprocess.run(["codex", "--version"], capture_output=True,
                                 text=True, check=True).stdout.strip()
    output_root = ROOT / declaration["output_root"]
    if mode == "canary":
        record = call_once(case=CANARY, slot="canary", freeze=freeze, prompt=prompt,
                           schema=schema, output_root=output_root, cli_version=cli_version)
        return {"status": record["status"], "scope": "NON_STUDY_SCHEMA_CANARY",
                "study_calls": 0, "pilot_role_annotation_completed": False}
    if mode != "pilot":
        raise ValueError("unknown mode")
    canary_path = output_root / "canary" / f"{CANARY['case_id']}.json"
    if not canary_path.is_file():
        raise RuntimeError("non-study role schema canary is absent")
    canary = call_once(case=CANARY, slot="canary", freeze=freeze, prompt=prompt,
                       schema=schema, output_root=output_root, cli_version=cli_version)
    if canary["status"] != VALID_STATUS:
        raise RuntimeError("non-study role schema canary did not pass")
    valid = 0
    for slot in declaration["isolated_passes"]:
        for case in entries:
            record = call_once(case=case, slot=slot, freeze=freeze, prompt=prompt,
                               schema=schema, output_root=output_root, cli_version=cli_version)
            print(json.dumps({"slot": slot, "case_id": case["case_id"],
                              "status": record["status"]}), flush=True)
            if record["status"] != VALID_STATUS:
                return {"status": "STOPPED_ON_RETAINED_FAILURE", "valid_calls": valid,
                        "planned_calls": 228, "pilot_role_annotation_completed": False}
            valid += 1
    return {"status": "STRUCTURAL_RETURNS_PENDING_BLIND_SEMANTIC_REVIEW",
            "valid_calls": valid, "planned_calls": 228,
            "pilot_role_annotation_completed": False, "endpoint_scoring_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("canary", "pilot"), required=True)
    args = parser.parse_args()
    result = run(args.mode)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {VALID_STATUS, "STRUCTURAL_RETURNS_PENDING_BLIND_SEMANTIC_REVIEW"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
