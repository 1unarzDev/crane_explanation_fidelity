#!/usr/bin/env python3
"""Run the separate frozen neutral-input qualification with durable no-retry intents."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

from adjudicate_evidence_calibration_annotations import validate_return
from audit_b2_transport_readiness import audit as transport_audit
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from evidence_calibration_neutral_level_qualification import aggregate, packet_for, score_return
from run_evidence_calibration_claim_role_v2r2_qualification import _write_once


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-neutral-level-support-v1-freeze.json"
VALID = "STRUCTURALLY_VALID_NEUTRAL_SUPPORT_RETURN_UNSCORED"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_bound() -> tuple[dict, dict, str, dict]:
    freeze = json.loads(FREEZE.read_text())
    if (freeze.get("schema") != "crane-evidence-calibration-neutral-level-support-freeze/v1"
            or freeze.get("status") != "FROZEN_BEFORE_INPUT_EXTENSION_MODEL_CALLS"
            or freeze.get("qualification_calls_authorized") is not True
            or freeze.get("quality_driven_retries") != 0
            or freeze.get("isolated_passes") != ["A", "B"]
            or freeze.get("planned_qualification_calls") != 40
            or freeze.get("timeout_s") != 300
            or freeze.get("tools") != "none"
            or freeze.get("highest_level_qualified") is not False
            or freeze.get("pilot_annotation_authorized") is not False
            or freeze.get("endpoint_scoring_authorized") is not False
            or freeze.get("p11_authorized") is not False
            or freeze.get("confirmation_independent_n") != 0
            or freeze.get("replication_independent_n") != 0):
        raise ValueError("neutral-input qualification scope changed")
    for item in freeze["bindings"].values():
        if digest(ROOT / item["path"]) != item["raw_sha256"]:
            raise ValueError(f"changed qualification component: {item['path']}")
    if freeze["bindings"]["runner"]["raw_sha256"] != digest(Path(__file__)):
        raise ValueError("qualification runner is not frozen")
    qualified = json.loads((ROOT / freeze["bindings"]["qualified_disposition"]["path"]).read_text())["qualified_binding"]
    candidate = freeze["candidate"]
    if (any(candidate.get(key) != qualified[key] for key in ("model", "reasoning_effort", "transport"))
            or freeze["bindings"]["prompt"] != {"path": qualified["prompt"]["path"], "raw_sha256": qualified["prompt"]["sha256"]}
            or freeze["bindings"]["return_schema"] != {"path": qualified["annotation_schema"]["path"], "raw_sha256": qualified["annotation_schema"]["sha256"]}):
        raise ValueError("input extension changed qualified configuration, prompt, or return schema")
    suite = json.loads((ROOT / freeze["bindings"]["suite"]["path"]).read_text())
    review = json.loads((ROOT / freeze["bindings"]["reference_review"]["path"]).read_text())
    if (review.get("status") != "ACCEPTED_PROJECT_CONSTRUCTION_REVIEW_NOT_MODEL_QUALIFICATION"
            or review.get("suite") != freeze["bindings"]["suite"]
            or [row["case_id"] for row in review["case_reviews"]] != [case["case_id"] for case in suite["cases"]]
            or any(row["disposition"] != "ACCEPT_CONSTRUCTION_REFERENCE" for row in review["case_reviews"])
            or suite.get("case_count") != 20
            or suite.get("split_counts") != {"development": 4, "heldout": 16}
            or len(suite["cases"]) != 20):
        raise ValueError("reviewed neutral-input reference scope changed")
    for case in suite["cases"]:
        packet_for(case, "A", canonical_sha256(suite))
    prompt = (ROOT / freeze["bindings"]["prompt"]["path"]).read_text()
    schema = json.loads((ROOT / freeze["bindings"]["return_schema"]["path"]).read_text())
    return freeze, suite, prompt, schema


def canary_case(suite: dict) -> dict:
    case = copy.deepcopy(suite["cases"][0])
    case["case_id"] = "non-study-neutral-input-schema-canary"
    case["split"] = "non-study"
    for index, item in enumerate(case["form"]["atomic_statements"], 1):
        item["item_id"] = f"neutral-canary-s{index}"
    for index, item in enumerate(case["expected"]["atomic_labels"], 1):
        item["item_id"] = f"neutral-canary-s{index}"
    return case


def call_once(*, case: dict, slot: str, suite_hash: str, freeze: dict, prompt: str,
              schema: dict, cli_version: str, runner=subprocess.run) -> dict:
    packet_slot = "A" if slot == "canary" else slot
    packet = packet_for(case, packet_slot, suite_hash)
    payload = {"task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION_QUALIFICATION",
               "annotation_origin": "automated_agent_qualification",
               "agent_identity": f"agent-{slot}-astra-neutral-input-v1",
               "packet_set_sha256": canonical_sha256(packet), "response_text": packet["response_text"],
               "form": packet["forms"][0], "required_attestation": "INDEPENDENT_BLINDED_COMPLETE"}
    full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN",
                             canonical_json_bytes(payload).decode(), "UNTRUSTED_ANNOTATION_DATA_END",
                             "Return only the object required by the output schema. Do not use tools."))
    identity = {"schema": "crane-neutral-support-request-identity/v1", "slot": slot,
                "case_id": case["case_id"], "candidate": freeze["candidate"], "cli_version": cli_version,
                "freeze_raw_sha256": digest(FREEZE), "payload_sha256": canonical_sha256(payload),
                "full_prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
                "schema_sha256": canonical_sha256(schema), "workspace": "empty-temporary-read-only",
                "tools": "none", "quality_driven_retries": 0}
    output = ROOT / freeze["output_root"] / slot / f"{case['case_id']}.json"
    intent = output.with_suffix(".intent")
    if output.exists():
        retained = json.loads(output.read_text())
        retained_intent = json.loads(intent.read_text()) if intent.exists() else {}
        if (retained_intent.get("schema") != "crane-neutral-support-call-intent/v1"
                or retained_intent.get("terminal_record_pending") is not True
                or retained_intent.get("request_identity") != identity
                or retained.get("schema") != "crane-neutral-support-call/v1"
                or retained.get("request_identity") != identity or retained.get("attempt_count") != 1
                or retained.get("quality_driven_retries") != 0
                or retained.get("status") not in {VALID, "FAILED_NO_RETRY"}):
            raise RuntimeError("retained qualification identity changed or terminal record is orphaned")
        if retained["status"] == VALID:
            parsed = json.loads(retained["raw_final"])
            validate_return(packet, parsed)
            if (retained.get("parsed_final") != parsed or retained.get("return_code") != 0
                    or retained.get("timed_out") is not False or retained.get("invalid_event") is not None):
                raise RuntimeError("retained valid qualification record differs from raw return")
        return retained
    if intent.exists():
        raise RuntimeError("qualification intent lacks terminal record; do not retry")
    if os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1":
        raise RuntimeError("outbound sockets disabled; no model request permitted")
    _write_once(intent, {"schema": "crane-neutral-support-call-intent/v1",
                         "request_identity": identity, "terminal_record_pending": True})
    started = time.time_ns()
    try:
        with tempfile.TemporaryDirectory(prefix="crane-neutral-support-") as directory:
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
    record = {"schema": "crane-neutral-support-call/v1", "request_identity": identity,
              "attempt_count": 1, "quality_driven_retries": 0, "return_code": return_code,
              "timed_out": timed_out, "latency_ms": (time.time_ns() - started) / 1_000_000,
              "stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
              "stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
              "invalid_event": invalid_event, "raw_final": raw_final,
              "credential_persisted": False, "method_key_accessed": False, "study_answers_included": False}
    try:
        if return_code or timed_out or invalid_event:
            raise ValueError("transport, timeout, or forbidden tool/event failure")
        parsed = json.loads(raw_final)
        validate_return(packet, parsed)
        record.update(status=VALID, parsed_final=parsed)
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
        record.update(status="FAILED_NO_RETRY", failure=str(error))
    _write_once(output, record)
    return record


def qualification_result(suite: dict, records: dict, freeze: dict) -> dict:
    passes = []
    for slot in ("A", "B"):
        rows = [score_return(case, records[(slot, case["case_id"])]["parsed_final"],
                             slot=slot, suite_hash=canonical_sha256(suite)) for case in suite["cases"]]
        metrics = aggregate(rows)
        gates = freeze["gates"]
        checks = {key: metrics[key] is not None and (metrics[key] <= value if key.endswith("rate") else metrics[key] >= value)
                  for key, value in gates.items()}
        critical = [row for row in rows if row["case_id"] in freeze["critical_reference_cases"]]
        checks["critical_reference_cases"] = (len(critical) == len(freeze["critical_reference_cases"])
            and all(all(item["correct"] for item in row["atomic"] + row["required_units"] + row["limitations"])
                    and row["false_premise_correct"] for row in critical))
        passes.append({"slot": slot, "metrics": metrics, "gate_checks": checks,
                       "passed": all(checks.values()), "case_scores": rows})
    return {"schema": "crane-neutral-support-qualification-result/v1", "freeze_raw_sha256": digest(FREEZE),
            "suite_sha256": canonical_sha256(suite), "passes": passes,
            "status": "PASS_INPUT_EXTENSION_PENDING_DISPOSITION" if all(row["passed"] for row in passes) else "FAILED_RETAIN_NO_RETRY",
            "pilot_annotation_authorized": False, "highest_level_qualified": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


def run(mode: str) -> dict:
    if mode not in {"canary", "qualification"}:
        raise ValueError("unknown qualification mode")
    freeze, suite, prompt, schema = load_bound()
    preflight = transport_audit(Path.home() / ".codex/config.toml", dict(os.environ))
    if preflight["status"] != "READY_FOR_SCHEMA_CANARY":
        raise RuntimeError(f"transport not ready: {preflight['status']}")
    cli_version = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=True).stdout.strip()
    if cli_version != freeze["cli_version"]:
        raise RuntimeError("CLI version differs from qualification declaration")
    kwargs = {"suite_hash": canonical_sha256(suite), "freeze": freeze, "prompt": prompt,
              "schema": schema, "cli_version": cli_version}
    if mode == "qualification":
        gate = json.loads((ROOT / freeze["canary_gate_manifest"]).read_text())
        canary_path = f"{freeze['output_root']}/canary/non-study-neutral-input-schema-canary"
        if (gate.get("status") != "PASS_NON_STUDY_NEUTRAL_INPUT_SCHEMA_CANARY"
                or gate.get("freeze_raw_sha256") != digest(FREEZE)
                or gate.get("artifact_retention") != "DVC_PUSH_VERIFIED"
                or set(gate.get("bindings", {})) != {"record", "intent"}
                or gate["bindings"]["record"]["path"] != canary_path + ".json"
                or gate["bindings"]["intent"]["path"] != canary_path + ".intent"):
            raise RuntimeError("qualification requires a separately bound passing canary")
        for item in gate["bindings"].values():
            if digest(ROOT / item["path"]) != item["raw_sha256"]:
                raise RuntimeError("canary gate binding changed")
    canary = call_once(case=canary_case(suite), slot="canary", **kwargs)
    if canary["status"] != VALID:
        return {"status": "STOPPED_ON_RETAINED_CANARY_FAILURE"}
    if mode == "canary":
        return {"status": "PASS_NON_STUDY_NEUTRAL_INPUT_SCHEMA_CANARY", "qualification_calls": 0}
    records = {}
    for slot in ("A", "B"):
        for case in suite["cases"]:
            record = call_once(case=case, slot=slot, **kwargs)
            print(json.dumps({"slot": slot, "case_id": case["case_id"], "status": record["status"]}), flush=True)
            if record["status"] != VALID:
                return {"status": "STOPPED_ON_RETAINED_FAILURE", "completed_valid_calls": len(records)}
            records[(slot, case["case_id"])] = record
    result = qualification_result(suite, records, freeze)
    output = ROOT / freeze["output_root"] / "qualification-result.json"
    if output.exists():
        if json.loads(output.read_text()) != result:
            raise RuntimeError("retained qualification result changed")
    else:
        _write_once(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("canary", "qualification"), required=True)
    args = parser.parse_args()
    result = run(args.mode)
    print(json.dumps({key: value for key, value in result.items() if key != "passes"}, indent=2))
    raise SystemExit(0 if result["status"].startswith("PASS_") else 1)
