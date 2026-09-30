#!/usr/bin/env python3
"""Inventory continuation records without executing models or retrying unknown intents."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_role_continuation_canary import audit as audit_canary
from continue_evidence_calibration_pilot_claim_roles import CONTINUATION, ROOT, digest, load_continuation
from run_evidence_calibration_claim_role_v2r2_qualification import FREEZE, VALID_STATUS, _canonical, _payload, _prompt
from validate_evidence_calibration_claim_roles_v2 import validate


def audit(*, process_terminal: bool = False) -> dict:
    declaration, tasks, freeze, prompt, schema = load_continuation()
    canary = audit_canary()
    output_root = ROOT / declaration["output_root"]
    expected_paths = {ROOT / canary[key]["path"] for key in ("call_record", "intent")}
    rows = []
    for slot, case in tasks:
        output = output_root / slot / f"{case['case_id']}.json"
        intent_path = output.with_suffix(".intent")
        expected_paths.update((output, intent_path))
        row = {"slot": slot, "case_id": case["case_id"]}
        if not intent_path.exists():
            if output.exists():
                raise ValueError("orphan continuation terminal record")
            rows.append({**row, "disposition": "NEVER_LAUNCHED"})
            continue
        payload = _payload(case, slot)
        identity = {"schema": "crane-evidence-calibration-claim-role-v2r2-request-identity/v1",
                    "slot": slot, "opaque_response_id": payload["opaque_response_id"],
                    "model": freeze["candidate"]["model"],
                    "reasoning_effort": freeze["candidate"]["reasoning_effort"],
                    "transport": freeze["candidate"]["transport"],
                    "cli_version": declaration["cli_version"], "freeze_raw_sha256": digest(FREEZE),
                    "payload_sha256": hashlib.sha256(_canonical(payload)).hexdigest(),
                    "full_prompt_sha256": hashlib.sha256(_prompt(prompt, payload).encode()).hexdigest(),
                    "schema_sha256": hashlib.sha256(_canonical(schema)).hexdigest(),
                    "workspace": "empty-temporary-read-only", "tools": "none", "quality_driven_retries": 0}
        intent = json.loads(intent_path.read_text())
        if (intent.get("schema") != "crane-evidence-calibration-claim-role-v2r2-call-intent/v1"
                or intent.get("request_identity") != identity or intent.get("terminal_record_pending") is not True):
            raise ValueError("continuation intent differs from its qualified uncalled identity")
        row["intent"] = {"path": str(intent_path.relative_to(ROOT)), "raw_sha256": digest(intent_path)}
        if not output.exists():
            state = "UNKNOWN_DISPOSITION_NO_RETRY" if process_terminal else "PENDING_INTENT_PROCESS_STATE_NOT_INFERRED"
            rows.append({**row, "disposition": state})
            continue
        record = json.loads(output.read_text())
        if (record.get("schema") != "crane-evidence-calibration-claim-role-v2r2-call/v1"
                or record.get("request_identity") != identity or record.get("attempt_count") != 1
                or record.get("quality_driven_retries") != 0 or record.get("method_key_accessed") is not False
                or record.get("status") not in {VALID_STATUS, "FAILED_NO_RETRY"}):
            raise ValueError("continuation terminal identity or no-retry boundary changed")
        if record["status"] == VALID_STATUS:
            parsed = json.loads(record["raw_final"])
            structural = validate(payload, parsed)
            if (record.get("parsed_final") != parsed or record.get("structural_validation") != structural
                    or record.get("return_code") != 0 or record.get("timed_out") is not False
                    or record.get("invalid_event") is not None):
                raise ValueError("continuation raw structural return changed")
        rows.append({**row, "disposition": record["status"],
                     "terminal_record": {"path": str(output.relative_to(ROOT)), "raw_sha256": digest(output)}})
    unexpected = {path for path in output_root.rglob("*") if path.is_file()} - expected_paths
    if unexpected:
        raise ValueError("unexpected artifact in continuation output root")
    stopped = False
    counts = {key: 0 for key in (VALID_STATUS, "FAILED_NO_RETRY", "UNKNOWN_DISPOSITION_NO_RETRY",
                               "PENDING_INTENT_PROCESS_STATE_NOT_INFERRED", "NEVER_LAUNCHED")}
    for row in rows:
        state = row["disposition"]
        counts[state] += 1
        if stopped and state != "NEVER_LAUNCHED":
            raise ValueError("continuation call after failure, unknown intent, or unlaunched gap")
        if state != VALID_STATUS:
            stopped = True
    complete = not stopped
    return {"schema": "crane-evidence-calibration-pilot-role-continuation-audit/v1",
            "recorded_date": "2026-09-30",
            "status": "STRUCTURAL_CONTINUATION_COMPLETE_ORIGINAL_A_STILL_UNKNOWN" if complete else
                      ("TERMINAL_INCOMPLETE_CONTINUATION_RETAINED" if process_terminal else "INCOMPLETE_PROCESS_STATE_NOT_INFERRED"),
            "process_terminal_asserted_by_invoker": process_terminal,
            "declaration": {"path": str(CONTINUATION.relative_to(ROOT)), "raw_sha256": digest(CONTINUATION)},
            "auditor": {"path": "analysis/audit_evidence_calibration_pilot_role_continuation.py",
                        "raw_sha256": digest(Path(__file__))},
            "canary": canary, "planned_continuation_calls": len(tasks), "continuation_disposition_counts": counts,
            "combined_known_valid_returns": 69 + counts[VALID_STATUS],
            "original_quarantined_requests": declaration["quarantined_requests"], "records": rows,
            "complete_two_pass_bank": False, "method_key_opened": False,
            "support_labels_generated": False, "endpoint_scores_generated": False,
            "resume_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-terminal", action="store_true",
                        help="Use only after the process handle or direct process inspection proves termination.")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if args.output and not args.process_terminal:
        raise ValueError("do not bind a changing live-output snapshot as terminal evidence")
    result = audit(process_terminal=args.process_terminal)
    if args.manifest and json.loads(args.manifest.read_text()) != result:
        raise ValueError("continuation differs from its bound terminal manifest")
    if args.output:
        with args.output.open("x") as handle:
            json.dump(result, handle, indent=2, sort_keys=True)
            handle.write("\n")
    print(json.dumps({key: value for key, value in result.items() if key not in {"records", "canary"}}, indent=2))
