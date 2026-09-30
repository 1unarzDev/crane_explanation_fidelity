#!/usr/bin/env python3
"""Execute only prospectively bound never-launched development role identities."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from audit_b2_transport_readiness import audit as transport_audit
from audit_evidence_calibration_pilot_role_returns import audit as audit_retained
from run_evidence_calibration_pilot_claim_roles import CANARY, DECLARATION, ROOT, load_declared
from run_evidence_calibration_claim_role_v2r2_qualification import VALID_STATUS, call_once


CONTINUATION = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-pilot-role-v2r2-continuation-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_continuation() -> tuple[dict, list[tuple[str, dict]], dict, str, dict]:
    original, entries, freeze, prompt, schema = load_declared()
    continuation = json.loads(CONTINUATION.read_text())
    retained_path = ROOT / continuation["interruption"]["path"]
    retained = json.loads(retained_path.read_text())
    if audit_retained() != retained:
        raise ValueError("original interrupted role records differ from their snapshot")
    planned = [{"slot": row["slot"], "case_id": row["case_id"]}
               for row in retained["records"] if row["disposition"] == "NEVER_LAUNCHED"]
    quarantine = [row for row in retained["records"]
                  if row["disposition"] == "UNKNOWN_DISPOSITION_NO_RETRY"]
    if (
        continuation.get("schema") != "crane-evidence-calibration-pilot-role-continuation/v1-development"
        or continuation.get("status") != "DECLARED_BEFORE_CONTINUATION_CALLS"
        or continuation.get("original_declaration") != {"path": str(DECLARATION.relative_to(ROOT)),
                                                       "raw_sha256": digest(DECLARATION)}
        or continuation.get("interruption", {}).get("raw_sha256") != digest(retained_path)
        or continuation.get("runner") != {"path": str(Path(__file__).resolve().relative_to(ROOT)),
                                          "raw_sha256": digest(Path(__file__))}
        or continuation.get("tasks") != planned or len(planned) != 158
        or continuation.get("planned_pilot_call_count") != 158
        or continuation.get("quarantined_requests") != quarantine or len(quarantine) != 1
        or continuation.get("output_root") != "model_outputs/automated_annotations/evidence-calibration-b2-b4-pilot-v1-role-v2r2-continuation-v1"
        or continuation["output_root"] == original["output_root"]
        or any(continuation.get(key) != original[key] for key in ("model", "reasoning_effort", "transport", "tools"))
        or continuation.get("quality_driven_retries") != 0
        or continuation.get("development_role_calls_authorized") is not True
        or continuation.get("support_annotation_authorized") is not False
        or continuation.get("endpoint_scoring_authorized") is not False
        or continuation.get("p11_authorized") is not False
        or continuation.get("confirmation_independent_n") != 0
        or continuation.get("replication_independent_n") != 0
        or continuation.get("nonstudy_canary_required") is not True
        or continuation.get("incomplete_pass_disposition") != "QUARANTINED_A_RETURN_NOT_REPLACED_REQUIRE_PROSPECTIVE_MEASUREMENT_RULE_AND_WHOLE_EPISODE_SENSITIVITY"
    ):
        raise ValueError("continuation differs from the qualified uncalled identities or boundary")
    by_id = {entry["case_id"]: entry for entry in entries}
    return continuation, [(row["slot"], by_id[row["case_id"]]) for row in planned], freeze, prompt, schema


def run(mode: str) -> dict:
    declaration, tasks, freeze, prompt, schema = load_continuation()
    preflight = transport_audit(Path.home() / ".codex/config.toml", dict(os.environ))
    if preflight["status"] != "READY_FOR_SCHEMA_CANARY":
        raise RuntimeError(f"continuation transport not ready: {preflight['status']}")
    cli_version = subprocess.run(["codex", "--version"], capture_output=True,
                                 text=True, check=True).stdout.strip()
    if cli_version != declaration["cli_version"]:
        raise RuntimeError("CLI version changed from the prospective continuation binding")
    output_root = ROOT / declaration["output_root"]
    if mode not in {"canary", "pilot"}:
        raise ValueError("unknown continuation mode")
    if mode == "pilot" and not (output_root / "canary" / f"{CANARY['case_id']}.json").is_file():
        raise RuntimeError("continuation non-study schema canary has not run")
    canary = call_once(case=CANARY, slot="canary", freeze=freeze, prompt=prompt,
                       schema=schema, output_root=output_root, cli_version=cli_version)
    if canary["status"] != VALID_STATUS:
        return {"status": "STOPPED_ON_RETAINED_CANARY_FAILURE", "pilot_calls": 0}
    if mode == "canary":
        return {"status": "PASS_NON_STUDY_SCHEMA_CANARY", "pilot_calls": 0}
    valid = 0
    for slot, case in tasks:
        record = call_once(case=case, slot=slot, freeze=freeze, prompt=prompt,
                           schema=schema, output_root=output_root, cli_version=cli_version)
        print(json.dumps({"slot": slot, "case_id": case["case_id"], "status": record["status"]}), flush=True)
        if record["status"] != VALID_STATUS:
            return {"status": "STOPPED_ON_RETAINED_FAILURE", "valid_continuation_calls": valid,
                    "planned_continuation_calls": 158, "endpoint_scoring_authorized": False}
        valid += 1
    return {"status": "STRUCTURAL_CONTINUATION_COMPLETE_ONE_A_RETURN_STILL_UNKNOWN",
            "valid_continuation_calls": valid, "planned_continuation_calls": 158,
            "support_annotation_authorized": False, "endpoint_scoring_authorized": False,
            "p11_authorized": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("canary", "pilot"), required=True)
    args = parser.parse_args()
    result = run(args.mode)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"PASS_NON_STUDY_SCHEMA_CANARY",
                                    "STRUCTURAL_CONTINUATION_COMPLETE_ONE_A_RETURN_STILL_UNKNOWN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
