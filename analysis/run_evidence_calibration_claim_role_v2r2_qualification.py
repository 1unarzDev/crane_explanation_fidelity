#!/usr/bin/env python3
"""Run the separately frozen v2r2 synthetic role qualification with no retry.

Only structurally valid returns are produced here. A distinct project review must compare
both isolated passes to the frozen reference before any pilot role use.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

from audit_evidence_calibration_claim_role_v2r2_freeze import FREEZE, ROOT, audit
from audit_b2_transport_readiness import audit as transport_audit
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, validate as validate_claim_roles


DEFAULT_OUTPUT = ROOT / "model_outputs/automated_annotations/evidence-calibration-claim-role-v2r2-synthetic"
VALID_STATUS = "STRUCTURALLY_VALID_ROLE_QUALIFICATION_UNSCORED"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _payload(case: dict, slot: str) -> dict:
    return {"schema": INPUT_SCHEMA, "opaque_response_id": f"{case['case_id']}-{slot}",
            "response_text": case["response_text"], "claims": case["claims"]}


def _prompt(prompt: str, payload: dict) -> str:
    return "\n".join((prompt, "UNTRUSTED_ROLE_INPUT_BEGIN", _canonical(payload).decode("utf-8"),
                      "UNTRUSTED_ROLE_INPUT_END", "Return only the schema object. Do not use tools."))


def _write_once(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def load_bound_freeze(freeze_path: Path = FREEZE) -> tuple[dict, list[dict], str, dict]:
    audit(freeze_path)
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    suite = json.loads((ROOT / freeze["suite"]["path"]).read_text(encoding="utf-8"))
    prompt = (ROOT / freeze["candidate"]["prompt"]["path"]).read_text(encoding="utf-8")
    schema = json.loads((ROOT / freeze["candidate"]["return_schema"]["path"]).read_text(encoding="utf-8"))
    return freeze, suite["cases"], prompt, schema


def call_once(*, case: dict, slot: str, freeze: dict, prompt: str, schema: dict,
              output_root: Path = DEFAULT_OUTPUT, freeze_path: Path = FREEZE,
              cli_version: str, runner: Any = subprocess.run) -> dict:
    if slot not in {"canary", "A", "B"}:
        raise ValueError("unknown isolated role slot")
    payload = _payload(case, slot)
    full_prompt = _prompt(prompt, payload)
    candidate = freeze["candidate"]
    identity = {
        "schema": "crane-evidence-calibration-claim-role-v2r2-request-identity/v1",
        "slot": slot, "opaque_response_id": payload["opaque_response_id"],
        "model": candidate["model"], "reasoning_effort": candidate["reasoning_effort"],
        "transport": candidate["transport"], "cli_version": cli_version,
        "freeze_raw_sha256": _sha256(freeze_path.read_bytes()),
        "payload_sha256": _sha256(_canonical(payload)),
        "full_prompt_sha256": _sha256(full_prompt.encode("utf-8")),
        "schema_sha256": _sha256(_canonical(schema)),
        "workspace": "empty-temporary-read-only", "tools": "none", "quality_driven_retries": 0,
    }
    output = output_root / slot / f"{case['case_id']}.json"
    intent = output.with_suffix(".intent")
    if output.exists():
        if not intent.exists():
            raise RuntimeError(f"orphan role call record without intent: {output}")
        retained_intent = json.loads(intent.read_text(encoding="utf-8"))
        retained = json.loads(output.read_text(encoding="utf-8"))
        if (retained_intent.get("schema") != "crane-evidence-calibration-claim-role-v2r2-call-intent/v1"
                or retained_intent.get("terminal_record_pending") is not True
                or retained_intent.get("request_identity") != identity
                or retained.get("schema") != "crane-evidence-calibration-claim-role-v2r2-call/v1"
                or retained.get("request_identity") != identity
                or retained.get("attempt_count") != 1
                or retained.get("quality_driven_retries") != 0
                or retained.get("status") not in {VALID_STATUS, "FAILED_NO_RETRY"}):
            raise RuntimeError(f"retained role request differs from the frozen request: {output}")
        if retained["status"] == VALID_STATUS:
            try:
                parsed = json.loads(retained["raw_final"])
                structural = validate_claim_roles(payload, parsed)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                raise RuntimeError(f"retained valid role return no longer validates: {output}") from error
            if (retained.get("return_code") != 0 or retained.get("timed_out") is not False
                    or retained.get("invalid_event") is not None
                    or retained.get("parsed_final") != parsed
                    or retained.get("structural_validation") != structural):
                raise RuntimeError(f"retained valid role record differs from its raw return: {output}")
        return retained
    if intent.exists():
        raise RuntimeError(f"role call intent lacks a terminal record; do not retry: {intent}")
    if os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1":
        raise RuntimeError("managed shell disables outbound sockets; run on a network-enabled host")
    _write_once(intent, {"schema": "crane-evidence-calibration-claim-role-v2r2-call-intent/v1",
                         "request_identity": identity, "terminal_record_pending": True})
    started = time.time_ns()
    try:
        with tempfile.TemporaryDirectory(prefix="crane-claim-role-") as directory:
            temporary = Path(directory)
            schema_path = temporary / "schema.json"
            final_path = temporary / "final.json"
            schema_path.write_bytes(_canonical(schema) + b"\n")
            command = [
                "codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--cd", str(temporary), "--model", candidate["model"],
                "--config", f'model_reasoning_effort="{candidate["reasoning_effort"]}"',
                "--output-schema", str(schema_path), "--output-last-message", str(final_path), "-",
            ]
            try:
                done = runner(command, input=full_prompt, text=True, capture_output=True,
                              check=False, env={**os.environ, "NO_COLOR": "1"}, timeout=300)
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
    record = {
        "schema": "crane-evidence-calibration-claim-role-v2r2-call/v1",
        "request_identity": identity, "attempt_count": 1, "quality_driven_retries": 0,
        "return_code": return_code, "timed_out": timed_out,
        "latency_ms": (time.time_ns() - started) / 1_000_000,
        "stdout_sha256": _sha256(stdout.encode("utf-8")),
        "stderr_sha256": _sha256(stderr.encode("utf-8")),
        "invalid_event": invalid_event, "raw_final": raw_final,
        "credential_persisted": False, "method_key_accessed": False,
    }
    try:
        if return_code or timed_out or invalid_event:
            raise ValueError("transport, timeout, or forbidden tool/event failure")
        parsed = json.loads(raw_final)
        structural = validate_claim_roles(payload, parsed)
        record.update(status=VALID_STATUS, parsed_final=parsed, structural_validation=structural)
    except (ValueError, json.JSONDecodeError, TypeError, KeyError) as error:
        record.update(status="FAILED_NO_RETRY", failure=str(error))
    _write_once(output, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("canary", "qualification"), required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    freeze, cases, prompt, schema = load_bound_freeze()
    preflight = transport_audit(Path.home() / ".codex/config.toml", dict(os.environ))
    if preflight["status"] != "READY_FOR_SCHEMA_CANARY":
        raise RuntimeError(f"role model transport is not ready: {preflight['status']}")
    cli_version = subprocess.run(["codex", "--version"], check=True,
                                 capture_output=True, text=True).stdout.strip()
    canary = {"case_id": "non-study-schema-canary", "response_text": "The recorded action succeeded.",
              "claims": [{"item_id": "c1", "response_span": "The recorded action succeeded.",
                          "claim_text": "The recorded action succeeded."}]}
    if args.mode == "canary":
        tasks = [("canary", canary)]
    else:
        canary_path = args.output_root / "canary" / "non-study-schema-canary.json"
        if not canary_path.is_file():
            raise RuntimeError("non-study role schema canary has not run")
        prior = call_once(case=canary, slot="canary", freeze=freeze, prompt=prompt,
                          schema=schema, output_root=args.output_root, cli_version=cli_version)
        if prior["status"] != VALID_STATUS:
            raise RuntimeError("retained non-study role schema canary did not pass")
        tasks = [(slot, case) for slot in ("A", "B") for case in cases]
    summary = []
    for slot, case in tasks:
        record = call_once(case=case, slot=slot, freeze=freeze, prompt=prompt,
                           schema=schema, output_root=args.output_root, cli_version=cli_version)
        summary.append({"slot": slot, "case_id": case["case_id"], "status": record["status"]})
        if record["status"] != VALID_STATUS:
            print(json.dumps({"status": "STOPPED_ON_RETAINED_FAILURE", "calls": summary}, indent=2))
            return 1
    print(json.dumps({"status": "STRUCTURAL_RETURNS_ONLY_INDEPENDENT_SEMANTIC_REVIEW_REQUIRED",
                      "calls": summary, "pilot_role_annotation_authorized": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
