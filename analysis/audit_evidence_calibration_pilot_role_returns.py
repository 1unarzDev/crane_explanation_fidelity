#!/usr/bin/env python3
"""Inventory retained pilot role calls without semantic scoring or model execution."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from run_evidence_calibration_claim_role_v2r2_qualification import (
    VALID_STATUS, _canonical, _payload, _prompt,
)
from validate_evidence_calibration_claim_roles_v2 import validate


ROOT = Path(__file__).resolve().parents[1]
DECLARATION = "research/explanation_fidelity/experiment_configs/development/evidence-calibration-pilot-claim-role-v2r2-use-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(root: Path = ROOT) -> dict:
    declaration = json.loads((root / DECLARATION).read_text())
    if (declaration.get("schema") != "crane-evidence-calibration-pilot-claim-role-use/v1-development"
            or declaration.get("planned_call_count") != 228
            or declaration.get("isolated_passes") != ["A", "B"]
            or declaration.get("quality_driven_retries") != 0
            or declaration.get("support_annotation_authorized") is not False
            or declaration.get("endpoint_scoring_authorized") is not False
            or declaration.get("p11_authorized") is not False
            or declaration.get("development_pilot_role_calls_authorized") is not True
            or declaration.get("confirmation_independent_n") != 0
            or declaration.get("replication_independent_n") != 0):
        raise ValueError("pilot declaration scope differs from the retained task")
    for key in ("freeze", "qualification", "input_bundle", "runner"):
        binding = declaration[key]
        if digest(root / binding["path"]) != binding["raw_sha256"]:
            raise ValueError(f"changed declared {key}")
    freeze = json.loads((root / declaration["freeze"]["path"]).read_text())
    candidate = freeze["candidate"]
    qualification = json.loads((root / declaration["qualification"]["path"]).read_text())
    if (qualification.get("status") != "PASS_SYNTHETIC_STANCE_KIND_POLARITY_ONLY"
            or any(declaration.get(key) != candidate[key] for key in ("model", "reasoning_effort", "transport"))
            or declaration.get("tools") != "none"):
        raise ValueError("pilot task differs from its qualified configuration")
    prompt_binding, schema_binding = candidate["prompt"], candidate["return_schema"]
    for binding in (prompt_binding, schema_binding):
        if digest(root / binding["path"]) != binding["raw_sha256"]:
            raise ValueError("changed qualified prompt or return schema")
    prompt = (root / prompt_binding["path"]).read_text()
    schema = json.loads((root / schema_binding["path"]).read_text())
    bundle = json.loads((root / declaration["input_bundle"]["path"]).read_text())
    entries = bundle["entries"]
    ids = [entry["case_id"] for entry in entries]
    if (bundle.get("response_count") != 114 or bundle.get("atomic_claim_count") != 1084
            or len(entries) != 114 or sum(len(x["claims"]) for x in entries) != 1084
            or ids != sorted(set(ids))):
        raise ValueError("reviewed input bundle counts differ")
    output_root = root / declaration["output_root"]
    canary_intent = output_root / "canary" / f"{declaration['canary']['case_id']}.intent"
    cli_version = json.loads(canary_intent.read_text())["request_identity"]["cli_version"]
    expected_paths: set[Path] = set()

    def inspect(case: dict, slot: str) -> dict:
        record_path = output_root / slot / f"{case['case_id']}.json"
        intent_path = record_path.with_suffix(".intent")
        expected_paths.update((record_path, intent_path))
        row = {"slot": slot, "case_id": case["case_id"]}
        if not intent_path.exists():
            if record_path.exists():
                raise ValueError("orphan terminal record without durable intent")
            return {**row, "disposition": "NEVER_LAUNCHED"}
        intent = json.loads(intent_path.read_text())
        payload = _payload(case, slot)
        identity = {
            "schema": "crane-evidence-calibration-claim-role-v2r2-request-identity/v1",
            "slot": slot, "opaque_response_id": payload["opaque_response_id"],
            "model": candidate["model"], "reasoning_effort": candidate["reasoning_effort"],
            "transport": candidate["transport"], "cli_version": cli_version,
            "freeze_raw_sha256": declaration["freeze"]["raw_sha256"],
            "payload_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
            "full_prompt_sha256": hashlib.sha256(_prompt(prompt, payload).encode()).hexdigest(),
            "schema_sha256": hashlib.sha256(_canonical(schema)).hexdigest(),
            "workspace": "empty-temporary-read-only", "tools": "none", "quality_driven_retries": 0,
        }
        if (intent.get("schema") != "crane-evidence-calibration-claim-role-v2r2-call-intent/v1"
                or intent.get("terminal_record_pending") is not True
                or intent.get("request_identity") != identity):
            raise ValueError("durable intent differs from qualified request")
        row["intent"] = {"path": str(intent_path.relative_to(root)), "raw_sha256": digest(intent_path)}
        if not record_path.exists():
            return {**row, "disposition": "UNKNOWN_DISPOSITION_NO_RETRY"}
        record = json.loads(record_path.read_text())
        if (record.get("schema") != "crane-evidence-calibration-claim-role-v2r2-call/v1"
                or record.get("request_identity") != identity
                or record.get("attempt_count") != 1
                or record.get("quality_driven_retries") != 0
                or record.get("method_key_accessed") is not False
                or record.get("status") not in {VALID_STATUS, "FAILED_NO_RETRY"}):
            raise ValueError("terminal record identity or no-retry boundary differs")
        if record["status"] == VALID_STATUS:
            parsed = json.loads(record["raw_final"])
            if (record.get("return_code") != 0 or record.get("timed_out") is not False
                    or record.get("invalid_event") is not None
                    or record.get("parsed_final") != parsed
                    or record.get("structural_validation") != validate(payload, parsed)):
                raise ValueError("retained valid raw role return no longer validates")
        return {**row, "disposition": record["status"],
                "terminal_record": {"path": str(record_path.relative_to(root)),
                                    "raw_sha256": digest(record_path)}}

    canary = inspect(declaration["canary"], "canary")
    if canary["disposition"] != VALID_STATUS:
        raise ValueError("retained non-study canary is not structurally valid")
    rows = [inspect(case, slot) for slot in ("A", "B") for case in entries]
    unexpected = {p for p in output_root.rglob("*") if p.is_file()} - expected_paths
    if unexpected:
        raise ValueError("unexpected file in immutable pilot role output root")
    stopped = False
    counts = {VALID_STATUS: 0, "FAILED_NO_RETRY": 0,
              "UNKNOWN_DISPOSITION_NO_RETRY": 0, "NEVER_LAUNCHED": 0}
    for row in rows:
        state = row["disposition"]
        counts[state] += 1
        if stopped and state != "NEVER_LAUNCHED":
            raise ValueError("call after first failure, ambiguous intent, or unlaunched gap")
        if state != VALID_STATUS:
            stopped = True
    return {
        "schema": "crane-evidence-calibration-pilot-role-retained-audit/v1",
        "recorded_date": "2026-09-30",
        "status": "INCOMPLETE_RETAINED_ROLE_CALL_SET" if stopped else "COMPLETE_STRUCTURAL_RETURNS_PENDING_REVIEW",
        "declaration": {"path": DECLARATION, "raw_sha256": digest(root / DECLARATION)},
        "auditor": {"path": "analysis/audit_evidence_calibration_pilot_role_returns.py",
                    "raw_sha256": digest(Path(__file__))},
        "canary": canary, "planned_pilot_calls": 228, "pilot_disposition_counts": counts,
        "records": rows, "method_key_opened": False, "support_labels_generated": False,
        "endpoint_scores_generated": False, "resume_authorized_by_audit": False,
        "p11_authorized": False, "confirmation_independent_n": 0, "replication_independent_n": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    if args.manifest and json.loads(args.manifest.read_text()) != result:
        raise ValueError("retained role audit differs from its bound manifest")
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
