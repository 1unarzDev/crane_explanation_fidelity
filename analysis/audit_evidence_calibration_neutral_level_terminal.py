#!/usr/bin/env python3
"""Audit the retained stopped qualification without calling a model or scoring accuracy."""

from __future__ import annotations

import hashlib
import json

from adjudicate_evidence_calibration_annotations import validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from evidence_calibration_neutral_level_qualification import packet_for
from run_evidence_calibration_neutral_level_qualification import ROOT, FREEZE, VALID, digest, load_bound


def audit() -> dict:
    freeze, suite, prompt, schema = load_bound()
    rows = []
    stopped = False
    valid = 0
    unlaunched = 0
    root = ROOT / freeze["output_root"]
    expected_paths = set()
    for slot in ("A", "B"):
        for case in suite["cases"]:
            path = root / slot / f"{case['case_id']}.json"
            intent = path.with_suffix(".intent")
            row = {"slot": slot, "case_id": case["case_id"]}
            if not path.exists() and not intent.exists():
                if not stopped:
                    raise ValueError("gap before retained stop frontier")
                row["status"] = "NEVER_LAUNCHED_NOT_AUTHORIZED_TO_RESUME"
                unlaunched += 1
                rows.append(row)
                continue
            if stopped or not path.exists() or not intent.exists():
                raise ValueError("record after stop or unknown/orphan intent")
            expected_paths.update((path, intent))
            record = json.loads(path.read_text())
            identity = record["request_identity"]
            if (json.loads(intent.read_text()).get("request_identity") != identity
                    or identity["freeze_raw_sha256"] != digest(FREEZE)
                    or identity["case_id"] != case["case_id"] or identity["slot"] != slot
                    or identity["candidate"] != freeze["candidate"]
                    or identity["cli_version"] != freeze["cli_version"]
                    or record["attempt_count"] != 1 or record["quality_driven_retries"] != 0
                    or record["return_code"] != 0 or record["timed_out"] is not False
                    or record["invalid_event"] is not None):
                raise ValueError("retained identity or execution facts changed")
            returned = json.loads(record["raw_final"])
            packet = packet_for(case, slot, canonical_sha256(suite))
            payload = {"task": "BLINDED_ATOMIC_EVIDENCE_ANNOTATION_QUALIFICATION",
                       "annotation_origin": "automated_agent_qualification",
                       "agent_identity": f"agent-{slot}-astra-neutral-input-v1",
                       "packet_set_sha256": canonical_sha256(packet),
                       "response_text": packet["response_text"], "form": packet["forms"][0],
                       "required_attestation": "INDEPENDENT_BLINDED_COMPLETE"}
            full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN",
                                     canonical_json_bytes(payload).decode(),
                                     "UNTRUSTED_ANNOTATION_DATA_END",
                                     "Return only the object required by the output schema. Do not use tools."))
            if (identity["payload_sha256"] != canonical_sha256(payload)
                    or identity["full_prompt_sha256"] != hashlib.sha256(full_prompt.encode()).hexdigest()
                    or identity["schema_sha256"] != canonical_sha256(schema)
                    or identity["workspace"] != "empty-temporary-read-only"
                    or identity["tools"] != "none" or identity["quality_driven_retries"] != 0):
                raise ValueError("retained request differs from frozen reconstruction")
            try:
                validate_return(packet, returned)
            except ValueError as error:
                if (record["status"] != "FAILED_NO_RETRY"
                        or str(error) != record["failure"]
                        or case["case_id"] != "nl-dev-04" or slot != "A"
                        or returned["highest_asserted_abstraction_level"] != "UNINTERPRETABLE"):
                    raise ValueError("retained validation failure changed") from error
                stopped = True
                row["failure"] = str(error)
                row["failure_class"] = "LOCAL_PACKET_VALIDATION_ABSTRACTION_OPTION"
            else:
                if record["status"] != VALID or record["parsed_final"] != returned:
                    raise ValueError("valid record differs from raw return")
                valid += 1
            row["status"] = record["status"]
            for key, source in (("record", path), ("intent", intent)):
                row[key] = {"path": str(source.relative_to(ROOT)), "raw_sha256": digest(source)}
            rows.append(row)
    actual_paths = {p for slot in ("A", "B") for p in (root / slot).glob("*") if p.is_file()}
    if actual_paths != expected_paths or not stopped or valid != 3 or unlaunched != 36:
        raise ValueError("retained terminal inventory differs from 3-valid/1-failed frontier")
    return {"schema": "crane-neutral-support-terminal-audit/v1",
            "status": "STOPPED_ON_RETAINED_VALIDATION_FAILURE_NOT_QUALIFIED",
            "freeze": {"path": str(FREEZE.relative_to(ROOT)), "raw_sha256": digest(FREEZE)},
            "structurally_valid_calls": valid, "failed_calls": 1, "never_launched_calls": unlaunched,
            "records": rows, "accuracy_scored": False, "pilot_annotation_authorized": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
