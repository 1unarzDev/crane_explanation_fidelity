"""Durable isolated support calls and explicit disagreement contexts; no method-key access."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile
import time

from adjudicate_evidence_calibration_annotations import _item_id, build_handoff, finalize, validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once


VALID = "STRUCTURALLY_VALID_SUPPORT_RETURN"


def annotation_payload(packet: dict, slot: str, agent_id: str) -> dict:
    if slot not in {"A", "B"} or not re.fullmatch(rf"agent-{slot}-[A-Za-z0-9._-]+", agent_id):
        raise ValueError("support identity must match the assigned isolated slot")
    forms = [form for form in packet["forms"] if form["annotator_slot"] == slot]
    if len(forms) != 1:
        raise ValueError("support slot does not identify exactly one form")
    return {"task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION", "annotation_origin": "automated_agent",
            "agent_identity": agent_id, "packet_set_sha256": canonical_sha256(packet),
            "response_text": packet["response_text"], "form": forms[0],
            "required_attestation": "INDEPENDENT_BLINDED_COMPLETE"}


def adjudication_payload(packet: dict, report: dict, agent_id: str) -> dict:
    if not re.fullmatch(r"agent-C-[A-Za-z0-9._-]+", agent_id) or agent_id in report["annotator_ids"]:
        raise ValueError("adjudicator must have a separate C identity")
    if report["packet_set_sha256"] != canonical_sha256(packet) or not report["disagreement_count"]:
        raise ValueError("adjudication requires actual disagreements for this packet")
    form = next(form for form in packet["forms"] if form["annotator_slot"] == "A")
    contexts = {f"claim:{item['item_id']}": {"kind": "atomic_label", "item_id": item["item_id"],
                "statement": item["statement"], "response_span": item["response_span"]}
                for item in form["atomic_statements"]}
    contexts.update({f"unit:{_item_id('u-', item['unit_prompt'])}":
                     {"kind": "required_unit_coverage", "unit_prompt": item["unit_prompt"]}
                     for item in form["required_unit_coverage"]})
    contexts.update({f"limitation:{_item_id('l-', item['limitation_prompt'])}":
                     {"kind": "limitation_preservation", "limitation_prompt": item["limitation_prompt"]}
                     for item in form["limitation_preservation"]})
    contexts["highest_asserted_abstraction_level"] = {
        "kind": "raw_highest_level_unqualified", "permitted_values": form["abstraction_level_options"],
        "endpoint_use_prohibited": True}
    contexts["false_premise_handling"] = {"kind": "false_premise_handling",
                                          "question_text": form["question_text"]}
    disagreements = report["disagreements"]
    if any(row["decision_key"] not in contexts for row in disagreements):
        raise ValueError("disagreement context cannot be resolved mechanically")
    return {"task": "BLINDED_DISAGREEMENT_ONLY_ADJUDICATION", "annotation_origin": "automated_agent",
            "agent_identity": agent_id, "response_text": packet["response_text"],
            "blinded_form": form, "handoff": build_handoff(report),
            "disagreement_contexts": [{"disagreement_id": row["disagreement_id"],
                                       "decision_key": row["decision_key"], **contexts[row["decision_key"]]}
                                      for row in disagreements],
            "required_attestation": "DISAGREEMENT_ONLY_BLINDED_COMPLETE"}


def validate_support(packet: dict, returned: dict, expected_agent_id: str, expected_slot: str) -> None:
    annotation_payload(packet, expected_slot, expected_agent_id)
    validate_return(packet, returned)
    if returned["annotator_id"] != expected_agent_id or returned["annotator_slot"] != expected_slot:
        raise ValueError("support return changed assigned opaque agent identity")
    if any(item["annotation_notes"] is not None and not isinstance(item["annotation_notes"], str)
           for item in returned["atomic_labels"]):
        raise ValueError("annotation notes must follow the qualified nullable string schema")
    for field in ("required_unit_coverage", "limitation_preservation"):
        if any(item["response_span"] is not None and not isinstance(item["response_span"], str)
               for item in returned[field]):
            raise ValueError("returned spans must follow the qualified nullable string schema")


def validate_adjudication(report: dict, returned: dict, expected_agent_id: str) -> None:
    if (not re.fullmatch(r"agent-C-[A-Za-z0-9._-]+", expected_agent_id)
            or returned["adjudicator_id"] != expected_agent_id):
        raise ValueError("adjudication changed assigned opaque agent identity")
    if any(item["selected_value"] is not None and not isinstance(item["selected_value"], (str, bool))
           for item in returned["decisions"]):
        raise ValueError("adjudication selection must follow the qualified string/boolean/null schema")
    finalize(report, returned)


def call_once(*, output: Path, payload: dict, schema: dict, prompt: str, freeze: dict,
              freeze_sha256: str, cli_version: str, validate, runner=subprocess.run) -> dict:
    full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN",
                             canonical_json_bytes(payload).decode(), "UNTRUSTED_ANNOTATION_DATA_END",
                             "Return only the object required by the output schema. Do not use tools."))
    identity = {"schema": "crane-durable-support-request/v1", "candidate": freeze["candidate"],
                "cli_version": cli_version, "freeze_raw_sha256": freeze_sha256,
                "payload_sha256": canonical_sha256(payload),
                "full_prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
                "schema_sha256": canonical_sha256(schema), "workspace": "empty-temporary-read-only",
                "timeout_s": freeze["timeout_s"],
                "tools": "none", "quality_driven_retries": 0}
    intent_path = output.with_suffix(".intent")
    if output.exists():
        record = json.loads(output.read_text())
        intent = json.loads(intent_path.read_text()) if intent_path.exists() else {}
        if (intent.get("request_identity") != identity or intent.get("terminal_record_pending") is not True
                or intent.get("schema") != "crane-durable-support-intent/v1"
                or record.get("schema") != "crane-durable-support-call/v1"
                or record.get("request_identity") != identity or record.get("attempt_count") != 1
                or record.get("quality_driven_retries") != 0
                or record.get("status") not in {VALID, "FAILED_NO_RETRY"}):
            raise RuntimeError("retained support call/intent identity changed")
        if record.get("raw_final_sha256") != hashlib.sha256(record["raw_final"].encode()).hexdigest():
            raise RuntimeError("retained support raw return hash changed")
        if record["status"] == VALID:
            parsed = json.loads(record["raw_final"])
            validate(parsed)
            if (record.get("parsed_final") != parsed or record.get("return_code") != 0
                    or record.get("timed_out") is not False or record.get("invalid_event") is not None):
                raise RuntimeError("retained support parsed return differs from raw/execution facts")
        return record
    if intent_path.exists():
        raise RuntimeError("unknown support-call intent; quarantine without retry")
    if os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1":
        raise RuntimeError("outbound sockets disabled; no support call allowed")
    _write_once(intent_path, {"schema": "crane-durable-support-intent/v1",
                              "request_identity": identity, "terminal_record_pending": True})
    started = time.time_ns()
    try:
        with tempfile.TemporaryDirectory(prefix="crane-support-call-") as directory:
            temporary = Path(directory)
            schema_path, final_path = temporary / "schema.json", temporary / "final.json"
            schema_path.write_bytes(canonical_json_bytes(schema) + b"\n")
            command = ["codex", "exec", "--json", "--ephemeral", "--skip-git-repo-check",
                       "--sandbox", "read-only", "--cd", str(temporary), "--model", freeze["candidate"]["model"],
                       "--config", f'model_reasoning_effort="{freeze["candidate"]["reasoning_effort"]}"',
                       "--output-schema", str(schema_path), "--output-last-message", str(final_path), "-"]
            try:
                done = runner(command, input=full_prompt, text=True, capture_output=True, check=False,
                              env={**os.environ, "NO_COLOR": "1"}, timeout=freeze["timeout_s"])
                return_code, stdout, stderr, timed_out = done.returncode, done.stdout, done.stderr, False
            except subprocess.TimeoutExpired as error:
                return_code, timed_out = 124, True
                stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else (error.stdout or "")
                stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else (error.stderr or "")
            raw_final = final_path.read_text() if final_path.exists() else ""
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
    record = {"schema": "crane-durable-support-call/v1", "request_identity": identity,
              "attempt_count": 1, "quality_driven_retries": 0, "return_code": return_code,
              "timed_out": timed_out, "latency_ms": (time.time_ns() - started) / 1_000_000,
              "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
              "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(), "invalid_event": invalid_event,
              "raw_final": raw_final, "raw_final_sha256": hashlib.sha256(raw_final.encode()).hexdigest(),
              "credential_persisted": False, "method_key_accessed": False}
    try:
        if return_code or timed_out or invalid_event:
            raise ValueError("transport, timeout, or forbidden tool/event failure")
        parsed = json.loads(raw_final)
        validate(parsed)
        record.update(status=VALID, parsed_final=parsed)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        record.update(status="FAILED_NO_RETRY", failure=str(error))
    _write_once(output, record)
    return record
