#!/usr/bin/env python3
"""Run one no-retry synthetic reference critique after a non-study schema canary."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from audit_b2_transport_readiness import audit as transport_audit


ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / "manifests/annotation/evidence-calibration-claim-role-v2-reference-review-request.json"
OUTPUT = ROOT / "model_outputs/automated_annotations/evidence-calibration-claim-role-v2-reference-review"
VALID = "STRUCTURALLY_VALID_REFERENCE_REVIEW_UNADJUDICATED"


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_once(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_request() -> tuple[dict, dict, str, dict, str]:
    request = json.loads(REQUEST.read_text(encoding="utf-8"))
    if (request.get("schema") != "crane-evidence-calibration-claim-role-v2-reference-review-request/v1"
            or request.get("status") != "FROZEN_SYNTHETIC_REVIEW_REQUEST_BEFORE_CALLS"
            or request.get("model_calls_before_freeze") != 0
            or request.get("study_output_authorized") is not False
            or request.get("quality_driven_retries") != 0):
        raise ValueError("synthetic review request is not bound and closed")
    contents = {}
    for key in ("suite", "candidate_prompt", "review_prompt", "return_schema", "runner"):
        item = request[key]
        raw = (ROOT / item["path"]).read_bytes()
        if sha256(raw) != item["raw_sha256"]:
            raise ValueError(f"synthetic review component changed: {key}")
        contents[key] = raw
    suite = json.loads(contents["suite"])
    if suite.get("status") != "UNCALLED_CONSTRUCTION_DRAFT_NOT_FROZEN" or len(suite["cases"]) != 24:
        raise ValueError("unexpected synthetic role suite")
    return (request, suite, contents["candidate_prompt"].decode("utf-8"),
            json.loads(contents["return_schema"]), contents["review_prompt"].decode("utf-8"))


def payload_for(mode: str, suite: dict, codebook: str) -> dict:
    if mode == "canary":
        case = {"case_id": "non-study-schema-canary", "response_text": "The recorded goal succeeded.",
                "claims": [{"item_id": "c1", "response_span": "The recorded goal succeeded.",
                            "claim_text": "The recorded goal succeeded."}],
                "expected": [{"item_id": "c1", "stance": "ASSERTED_FACT", "claim_kind": "TASK_OUTCOME",
                              "polarity": "POSITIVE", "rationale_span": "The recorded goal succeeded."}]}
        cases = [case]
    elif mode == "review":
        cases = suite["cases"]
    else:
        raise ValueError("unknown synthetic review mode")
    return {"schema": "crane-evidence-calibration-claim-role-v2-reference-review-input/v1",
            "codebook_under_review": codebook, "cases": cases,
            "synthetic_only": True, "method_identity_visible": False, "pilot_answers_included": False}


def validate_return(parsed: dict, case_ids: list[str]) -> None:
    if (not isinstance(parsed, dict)
            or set(parsed) != {"schema", "case_reviews", "global_issues", "attestation"}
            or parsed["schema"] != "crane-evidence-calibration-claim-role-v2-reference-review/v1"
            or parsed["attestation"] != "SYNTHETIC_REFERENCE_REVIEW_ONLY_NO_STUDY_LABELS"):
        raise ValueError("reference review return schema or attestation mismatch")
    rows = parsed["case_reviews"]
    if not isinstance(rows, list) or [row.get("case_id") if isinstance(row, dict) else None for row in rows] != case_ids:
        raise ValueError("reference review cases must match exactly in order")
    if not isinstance(parsed["global_issues"], list) or not all(isinstance(x, str) and x for x in parsed["global_issues"]):
        raise ValueError("reference review global issues malformed")
    for row in rows:
        if (set(row) != {"case_id", "status", "issues"} or row["status"] not in {"ACCEPT", "ISSUE"}
                or not isinstance(row["issues"], list)
                or not all(isinstance(x, str) and x for x in row["issues"])
                or (row["status"] == "ACCEPT") != (len(row["issues"]) == 0)):
            raise ValueError("reference review case row malformed")


def call(mode: str) -> dict:
    request, suite, codebook, schema, review_prompt = load_request()
    payload = payload_for(mode, suite, codebook)
    case_ids = [case["case_id"] for case in payload["cases"]]
    full_prompt = "\n".join((review_prompt, "UNTRUSTED_SYNTHETIC_REFERENCE_BEGIN",
                             canonical(payload).decode("utf-8"),
                             "UNTRUSTED_SYNTHETIC_REFERENCE_END", "Return only the review schema object. Do not use tools."))
    cli_version = subprocess.run(["codex", "--version"], check=True, text=True,
                                 capture_output=True).stdout.strip()
    identity = {"schema": "crane-role-v2-reference-review-request-identity/v1",
                "mode": mode, "model": request["model"], "reasoning_effort": request["reasoning_effort"],
                "transport": request["transport"], "cli_version": cli_version,
                "request_raw_sha256": sha256(REQUEST.read_bytes()),
                "payload_sha256": sha256(canonical(payload)),
                "prompt_sha256": sha256(full_prompt.encode("utf-8")),
                "schema_sha256": sha256(canonical(schema)),
                "workspace": "empty-temporary-read-only", "tools": "none", "quality_driven_retries": 0}
    output = OUTPUT / f"{mode}.json"
    intent = OUTPUT / f"{mode}.intent"
    if output.exists():
        if not intent.exists():
            raise RuntimeError(f"orphan reference review record: {output}")
        prior_intent = json.loads(intent.read_text(encoding="utf-8"))
        retained = json.loads(output.read_text(encoding="utf-8"))
        if (prior_intent.get("schema") != "crane-role-v2-reference-review-call-intent/v1"
                or prior_intent.get("terminal_record_pending") is not True
                or prior_intent.get("request_identity") != identity
                or retained.get("schema") != "crane-role-v2-reference-review-call/v1"
                or retained.get("request_identity") != identity
                or retained.get("attempt_count") != 1
                or retained.get("quality_driven_retries") != 0
                or retained.get("status") not in {VALID, "FAILED_NO_RETRY"}):
            raise RuntimeError("retained reference review request changed")
        if retained["status"] == VALID:
            parsed = json.loads(retained["raw_final"])
            validate_return(parsed, case_ids)
            if (retained["parsed_final"] != parsed or retained.get("return_code") != 0
                    or retained.get("timed_out") is not False or retained.get("invalid_event") is not None):
                raise RuntimeError("retained reference review raw return changed")
        return retained
    if intent.exists():
        raise RuntimeError(f"reference review intent lacks terminal record; do not retry: {intent}")
    if mode == "review":
        if call("canary")["status"] != VALID:
            raise RuntimeError("non-study review schema canary has not passed")
    preflight = transport_audit(Path.home() / ".codex/config.toml", dict(os.environ))
    if preflight["status"] != "READY_FOR_SCHEMA_CANARY":
        raise RuntimeError(f"model transport not ready: {preflight['status']}")
    write_once(intent, {"schema": "crane-role-v2-reference-review-call-intent/v1",
                        "request_identity": identity, "terminal_record_pending": True})
    started = time.time_ns()
    try:
        with tempfile.TemporaryDirectory(prefix="crane-role-v2-review-") as directory:
            temporary = Path(directory)
            schema_path = temporary / "schema.json"
            final_path = temporary / "final.json"
            schema_path.write_bytes(canonical(schema) + b"\n")
            command = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                       "--sandbox", "read-only", "--cd", str(temporary),
                       "--model", request["model"],
                       "--config", f'model_reasoning_effort="{request["reasoning_effort"]}"',
                       "--output-schema", str(schema_path), "--output-last-message", str(final_path), "-"]
            try:
                done = subprocess.run(command, input=full_prompt, text=True, capture_output=True,
                                      check=False, timeout=600, env={**os.environ, "NO_COLOR": "1"})
                return_code, stdout, stderr, timed_out = done.returncode, done.stdout, done.stderr, False
            except subprocess.TimeoutExpired as error:
                return_code, timed_out = 124, True
                stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
                stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
            raw_final = final_path.read_text(encoding="utf-8") if final_path.exists() else ""
    except OSError as error:
        return_code, stdout, stderr, timed_out, raw_final = 125, "", type(error).__name__, False, ""
    invalid_event = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_event = "unparsed_stdout"
            break
        item = event.get("item") if isinstance(event, dict) else None
        if isinstance(item, dict) and item.get("type") not in {"agent_message", "reasoning"}:
            invalid_event = item.get("type")
        if isinstance(event, dict) and event.get("type") in {"error", "turn.failed"}:
            invalid_event = event.get("type")
    record = {"schema": "crane-role-v2-reference-review-call/v1",
              "request_identity": identity, "attempt_count": 1, "quality_driven_retries": 0,
              "return_code": return_code, "timed_out": timed_out,
              "latency_ms": (time.time_ns() - started) / 1_000_000,
              "stdout_sha256": sha256(stdout.encode("utf-8")),
              "stderr_sha256": sha256(stderr.encode("utf-8")),
              "invalid_event": invalid_event, "raw_final": raw_final,
              "credential_persisted": False, "method_key_accessed": False,
              "pilot_answers_included": False}
    try:
        if return_code or timed_out or invalid_event:
            raise ValueError("transport, timeout, or forbidden event failure")
        parsed = json.loads(raw_final)
        validate_return(parsed, case_ids)
        record.update(status=VALID, parsed_final=parsed)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        record.update(status="FAILED_NO_RETRY", failure=str(error))
    write_once(output, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("canary", "review"), required=True)
    args = parser.parse_args()
    record = call(args.mode)
    print(json.dumps({"mode": args.mode, "status": record["status"],
                      "case_count": len(record.get("parsed_final", {}).get("case_reviews", [])),
                      "pilot_role_annotation_authorized": False}, indent=2))
    return 0 if record["status"] == VALID else 1


if __name__ == "__main__":
    raise SystemExit(main())
