#!/usr/bin/env python3
"""Reproduce frozen request identities and retained scoring without model execution."""

from __future__ import annotations

import argparse
import hashlib
import json

from adjudicate_evidence_calibration_annotations import validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from evidence_calibration_neutral_level_qualification_v2 import packet_for
from run_evidence_calibration_neutral_level_qualification_v2 import (
    FREEZE, ROOT, VALID, digest, load_bound, qualification_result,
)


def request_identity(case: dict, slot: str, freeze: dict, suite: dict, prompt: str, schema: dict) -> dict:
    packet = packet_for(case, slot, canonical_sha256(suite))
    payload = {"task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION_QUALIFICATION",
               "annotation_origin": "automated_agent_qualification",
               "agent_identity": f"agent-{slot}-astra-neutral-input-v2",
               "packet_set_sha256": canonical_sha256(packet), "response_text": packet["response_text"],
               "form": packet["forms"][0], "required_attestation": "INDEPENDENT_BLINDED_COMPLETE"}
    full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN",
                             canonical_json_bytes(payload).decode(), "UNTRUSTED_ANNOTATION_DATA_END",
                             "Return only the object required by the output schema. Do not use tools."))
    return {"schema": "crane-neutral-support-request-identity/v2", "slot": slot,
            "case_id": case["case_id"], "candidate": freeze["candidate"], "cli_version": freeze["cli_version"],
            "freeze_raw_sha256": digest(FREEZE), "payload_sha256": canonical_sha256(payload),
            "full_prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
            "schema_sha256": canonical_sha256(schema), "workspace": "empty-temporary-read-only",
            "tools": "none", "quality_driven_retries": 0}


def audit(*, process_terminal: bool = False) -> dict:
    freeze, suite, prompt, schema = load_bound()
    root = ROOT / freeze["output_root"]
    rows, records, expected_paths = [], {}, set()
    frontier = False
    counts = {"valid": 0, "failed": 0, "unknown_terminal": 0, "pending_live": 0, "never_launched": 0}
    for slot in ("A", "B"):
        for case in suite["cases"]:
            path = root / slot / f"{case['case_id']}.json"
            intent_path = path.with_suffix(".intent")
            row = {"slot": slot, "case_id": case["case_id"]}
            if not path.exists() and not intent_path.exists():
                frontier = True
                row["status"] = "NEVER_LAUNCHED"
                counts["never_launched"] += 1
                rows.append(row)
                continue
            if frontier or not intent_path.exists():
                raise ValueError("orphan record or request after sequential stop frontier")
            expected_paths.add(intent_path)
            identity = request_identity(case, slot, freeze, suite, prompt, schema)
            intent = json.loads(intent_path.read_text())
            if (intent.get("schema") != "crane-neutral-support-call-intent/v2"
                    or intent.get("terminal_record_pending") is not True
                    or intent.get("request_identity") != identity):
                raise ValueError("retained intent differs from frozen reconstruction")
            row["intent"] = {"path": str(intent_path.relative_to(ROOT)), "raw_sha256": digest(intent_path)}
            if not path.exists():
                frontier = True
                row["status"] = "UNKNOWN_TERMINAL_QUARANTINE_NO_RETRY" if process_terminal else "PENDING_INTENT_PROCESS_STATUS_UNASSERTED"
                counts["unknown_terminal" if process_terminal else "pending_live"] += 1
                rows.append(row)
                continue
            expected_paths.add(path)
            record = json.loads(path.read_text())
            if (record.get("schema") != "crane-neutral-support-call/v2"
                    or record.get("request_identity") != identity
                    or record.get("attempt_count") != 1 or record.get("quality_driven_retries") != 0
                    or any(record.get(key) is not False for key in (
                        "credential_persisted", "method_key_accessed", "study_answers_included"))):
                raise ValueError("retained terminal execution boundary changed")
            row["record"] = {"path": str(path.relative_to(ROOT)), "raw_sha256": digest(path)}
            row["status"] = record["status"]
            if record["status"] == VALID:
                parsed = json.loads(record["raw_final"])
                validate_return(packet_for(case, slot, canonical_sha256(suite)), parsed)
                if (record.get("parsed_final") != parsed or record.get("return_code") != 0
                        or record.get("timed_out") is not False or record.get("invalid_event") is not None):
                    raise ValueError("valid record differs from raw return or execution facts")
                records[(slot, case["case_id"])] = record
                counts["valid"] += 1
            elif record["status"] == "FAILED_NO_RETRY":
                frontier = True
                counts["failed"] += 1
                row["failure"] = record["failure"]
                if not record.get("return_code") and not record.get("timed_out") and record.get("invalid_event") is None:
                    try:
                        validate_return(packet_for(case, slot, canonical_sha256(suite)), json.loads(record["raw_final"]))
                    except (ValueError, TypeError, KeyError) as error:
                        if str(error) != record["failure"]:
                            raise ValueError("local validation failure no longer reproduces") from error
                    else:
                        raise ValueError("retained local failure unexpectedly validates")
                row["failure_class"] = "TRANSPORT_TIMEOUT_OR_FORBIDDEN_EVENT" if (
                    record.get("return_code") or record.get("timed_out") or record.get("invalid_event")) else "LOCAL_RETURN_VALIDATION"
            else:
                raise ValueError("unknown terminal disposition")
            rows.append(row)
    actual_paths = {p for slot in ("A", "B") for p in (root / slot).glob("*") if p.is_file()}
    if actual_paths != expected_paths:
        raise ValueError("undeclared output or intent present")
    result_path = root / "qualification-result.json"
    binding = None
    scored_status = None
    if result_path.exists():
        if counts["valid"] != freeze["planned_qualification_calls"]:
            raise ValueError("accuracy result exists for an incomplete qualification")
        retained = json.loads(result_path.read_text())
        if qualification_result(suite, records, freeze) != retained:
            raise ValueError("retained qualification score differs from exact frozen reproduction")
        scored_status = retained["status"]
        binding = {"path": str(result_path.relative_to(ROOT)), "raw_sha256": digest(result_path)}
    elif process_terminal and counts["valid"] == freeze["planned_qualification_calls"]:
        raise ValueError("complete terminal qualification lacks retained score")
    status = (scored_status or "TERMINAL_INCOMPLETE_NOT_QUALIFIED") if process_terminal else "PROCESS_STATUS_UNASSERTED"
    return {"schema": "crane-neutral-support-qualification-audit/v2", "status": status,
            "process_terminal_asserted": process_terminal,
            "freeze": {"path": str(FREEZE.relative_to(ROOT)), "raw_sha256": digest(FREEZE)},
            "counts": counts, "records": rows, "qualification_result": binding,
            "accuracy_reproduced": binding is not None, "highest_level_qualified": False,
            "pilot_annotation_authorized": False, "endpoint_scoring_authorized": False,
            "p11_authorized": False, "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--process-terminal", action="store_true",
                        help="Use only after the actual process handle has proven termination.")
    args = parser.parse_args()
    print(json.dumps(audit(process_terminal=args.process_terminal), indent=2, sort_keys=True))
