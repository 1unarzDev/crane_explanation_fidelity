#!/usr/bin/env python3
"""Verify a retained neutral-input schema canary without launching a model call."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from adjudicate_evidence_calibration_annotations import validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from evidence_calibration_neutral_level_qualification_v2 import packet_for
from run_evidence_calibration_neutral_level_qualification_v2 import (
    ROOT, FREEZE, VALID, canary_case, digest, load_bound,
)


MANIFEST = ROOT / "manifests/operations/evidence-calibration-neutral-level-support-canary-v2.json"


def audit(manifest_path: Path = MANIFEST) -> dict:
    manifest = json.loads(manifest_path.read_text())
    freeze, suite, prompt, schema = load_bound()
    output_root = ROOT / freeze["output_root"]
    case = canary_case(suite)
    record_path = output_root / "canary" / f"{case['case_id']}.json"
    intent_path = record_path.with_suffix(".intent")
    record = json.loads(record_path.read_text())
    intent = json.loads(intent_path.read_text())
    packet = packet_for(case, "A", canonical_sha256(suite))
    payload = {"task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION_QUALIFICATION",
               "annotation_origin": "automated_agent_qualification",
               "agent_identity": "agent-canary-astra-neutral-input-v2",
               "packet_set_sha256": canonical_sha256(packet), "response_text": packet["response_text"],
               "form": packet["forms"][0], "required_attestation": "INDEPENDENT_BLINDED_COMPLETE"}
    full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN",
                             canonical_json_bytes(payload).decode(), "UNTRUSTED_ANNOTATION_DATA_END",
                             "Return only the object required by the output schema. Do not use tools."))
    identity = {"schema": "crane-neutral-support-request-identity/v2", "slot": "canary",
                "case_id": case["case_id"], "candidate": freeze["candidate"], "cli_version": freeze["cli_version"],
                "freeze_raw_sha256": digest(FREEZE), "payload_sha256": canonical_sha256(payload),
                "full_prompt_sha256": hashlib.sha256(full_prompt.encode()).hexdigest(),
                "schema_sha256": canonical_sha256(schema), "workspace": "empty-temporary-read-only",
                "tools": "none", "quality_driven_retries": 0}
    bindings = {key: {"path": str(path.relative_to(ROOT)), "raw_sha256": digest(path)}
                for key, path in (("record", record_path), ("intent", intent_path))}
    retention = manifest.get("artifact_retention")
    expected_status = {"PENDING_DVC_PUSH": "PASS_SCHEMA_CANARY_PENDING_ARTIFACT_PUSH",
                       "DVC_PUSH_VERIFIED": "PASS_NON_STUDY_NEUTRAL_INPUT_SCHEMA_CANARY"}.get(retention)
    if (manifest.get("schema") != "crane-neutral-support-schema-canary/v2"
            or expected_status is None or manifest.get("status") != expected_status
            or manifest.get("freeze_raw_sha256") != digest(FREEZE)
            or manifest.get("bindings") != bindings
            or any(manifest.get(key) is not False for key in (
                "scientific_sample", "highest_level_qualified", "pilot_annotation_authorized",
                "endpoint_scoring_authorized", "p11_authorized"))
            or manifest.get("confirmation_independent_n") != 0
            or manifest.get("replication_independent_n") != 0):
        raise ValueError("canary manifest identity, retention, or authorization boundary changed")
    if (intent.get("schema") != "crane-neutral-support-call-intent/v2"
            or intent.get("terminal_record_pending") is not True or intent.get("request_identity") != identity
            or record.get("schema") != "crane-neutral-support-call/v2"
            or record.get("request_identity") != identity or record.get("status") != VALID
            or record.get("attempt_count") != 1 or record.get("quality_driven_retries") != 0
            or record.get("return_code") != 0 or record.get("timed_out") is not False
            or record.get("invalid_event") is not None
            or record.get("credential_persisted") is not False
            or record.get("method_key_accessed") is not False or record.get("study_answers_included") is not False):
        raise ValueError("retained canary is not the bound one-shot isolated return")
    parsed = json.loads(record["raw_final"])
    validate_return(packet, parsed)
    if parsed != record["parsed_final"]:
        raise ValueError("retained canary parsed return differs from raw bytes")
    return {"status": expected_status, "artifact_retention": retention,
            "qualification_launch_gate_passed": retention == "DVC_PUSH_VERIFIED",
            "highest_level_qualified": False, "pilot_annotation_authorized": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
