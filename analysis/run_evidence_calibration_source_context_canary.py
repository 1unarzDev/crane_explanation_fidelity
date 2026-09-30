#!/usr/bin/env python3
"""Run a frozen synthetic canary for the source-augmented annotation form.

This extends measurement qualification only. It does not annotate a pilot
response or establish a B2/B4 effect.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from adjudicate_evidence_calibration_annotations import validate_return
from evidence_calibration_io import canonical_json_bytes, canonical_sha256
from run_evidence_calibration_agent_annotation import (
    AMENDMENT, StructuredCodexCliAgentCaller, _annotation_payload, _canonical,
)


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-source-context-canary-v1-freeze.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load() -> tuple[dict, dict, dict, str]:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    if freeze["schema"] != "crane-evidence-calibration-source-context-canary-freeze/v1":
        raise ValueError("unsupported source-context canary freeze")
    case_binding = freeze["case"]
    case_path = ROOT / case_binding["path"]
    if digest(case_path) != case_binding["raw_sha256"]:
        raise ValueError("synthetic source-context case changed")
    case = json.loads(case_path.read_text(encoding="utf-8"))
    if case["schema"] != "crane-evidence-calibration-source-context-canary/v1":
        raise ValueError("unsupported source-context canary case")
    assets = case["form"]["robot_visible_evidence"]["exact_source_assets"]
    if len(assets) != 1 or any(hashlib.sha256(asset["text"].encode()).hexdigest() != asset["sha256"] for asset in assets):
        raise ValueError("synthetic source asset hash mismatch")
    binding = freeze["qualified_annotator"]
    disposition = json.loads((ROOT / binding["disposition_path"]).read_text(encoding="utf-8"))
    qualified = disposition["qualified_binding"]
    for key in ("model", "reasoning_effort", "transport"):
        if binding[key] != qualified[key]:
            raise ValueError(f"canary differs from qualified annotation {key}")
    prompt_path = ROOT / binding["prompt_path"]
    schema_path = ROOT / binding["return_schema_path"]
    if (digest(prompt_path) != binding["prompt_raw_sha256"]
            or digest(schema_path) != binding["return_schema_raw_sha256"]
            or digest(prompt_path) != qualified["prompt"]["sha256"]
            or digest(schema_path) != qualified["annotation_schema"]["sha256"]):
        raise ValueError("canary prompt/schema differ from qualified binding")
    return freeze, case, json.loads(schema_path.read_text(encoding="utf-8")), prompt_path.read_text(encoding="utf-8")


def packet_for(case: dict, slot: str) -> dict:
    form = {key: value for key, value in case["form"].items() if key != "response_text"}
    form = {"form_id": f"{case['canary_id']}-{slot}", "annotator_slot": slot,
            "packet_id": case["canary_id"], **form}
    return {"schema": "crane-blinded-agent-atomic-annotation-packet-set/v1",
            "packet_count": 1, "annotation_origin": "automated_agent_measurement_canary",
            "response_text": case["form"]["response_text"],
            "forms": [form]}


def score(case: dict, returned: dict) -> dict:
    expected = case["expected"]
    actual_labels = {item["item_id"]: item["label"] for item in returned["atomic_labels"]}
    expected_labels = {item["item_id"]: item["label"] for item in expected["atomic_labels"]}
    units = {item["unit_prompt"]: item for item in returned["required_unit_coverage"]}
    limits = {item["limitation_prompt"]: item for item in returned["limitation_preservation"]}
    checks = {
        "atomic_labels": actual_labels == expected_labels,
        "required_units": all(
            units[item["unit_prompt"]]["communicated"] == item["communicated"]
            and (not item["communicated"] or item["response_span"] in units[item["unit_prompt"]]["response_span"])
            for item in expected["required_unit_coverage"]
        ),
        "highest_level": returned["highest_asserted_abstraction_level"] == expected["highest_asserted_abstraction_level"],
        "limitations": all(limits[item["limitation_prompt"]]["preserved"] == item["preserved"]
                           for item in expected["limitation_preservation"]),
        "false_premise": returned["false_premise_handling"] == expected["false_premise_handling"],
    }
    return {"checks": checks, "passed": all(checks.values())}


def _expected_intent(slot: str, packet: dict) -> dict:
    return {"slot": slot, "packet_sha256": canonical_sha256(packet),
            "freeze_raw_sha256": digest(FREEZE)}


def _retained_call(path: Path, *, freeze: dict, slot: str,
                   payload: dict, schema: dict, prompt: str) -> dict:
    record = json.loads(path.read_text(encoding="utf-8"))
    identity = record.get("request_identity", {})
    full_prompt = "\n".join((prompt, "UNTRUSTED_ANNOTATION_DATA_BEGIN", _canonical(payload),
                             "UNTRUSTED_ANNOTATION_DATA_END",
                             "Return only the object required by the output schema. Do not use tools."))
    prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()
    expected = {
        "transport": freeze["qualified_annotator"]["transport"],
        "logical_role": f"source-context-canary-{slot}",
        "model": freeze["qualified_annotator"]["model"],
        "effort": freeze["qualified_annotator"]["reasoning_effort"],
        "prompt_sha256": prompt_hash,
        "schema_sha256": hashlib.sha256(canonical_json_bytes(schema)).hexdigest(),
        "payload": payload,
        "amendment_sha256": digest(AMENDMENT),
        "workspace": "empty-temporary-read-only",
    }
    if (record.get("status") != "VALID" or record.get("attempt_count") != 1
            or record.get("quality_driven_retries") != 0
            or record.get("credential_persisted") is not False
            or not isinstance(identity, dict)
            or any(identity.get(key) != value for key, value in expected.items())
            or record.get("request_sha256") != prompt_hash
            or record.get("cache_key") != hashlib.sha256(_canonical(identity).encode()).hexdigest()
            or path.name != f"{record.get('cache_key')}.json"):
        raise RuntimeError(f"retained {slot} canary call does not match the frozen request; do not retry")
    return record


def run(output_root: Path) -> dict:
    freeze, case, schema, prompt = load()
    if os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1":
        raise RuntimeError("source-context canary must run from a network-enabled host")
    if (output_root / "canary-result.json").exists():
        raise RuntimeError("refusing to rerun a completed source-context canary")
    output_root.mkdir(parents=True, exist_ok=True)
    passes = []
    for slot in freeze["isolated_passes"]:
        packet = packet_for(case, slot)
        form = packet["forms"][0]
        payload = _annotation_payload(packet, form, slot)
        intent = output_root / f"{slot}.intent"
        expected_intent = _expected_intent(slot, packet)
        if intent.exists():
            records = list((output_root / slot).glob("*.json"))
            if len(records) != 1:
                raise RuntimeError(f"uncertain prior {slot} canary call; do not retry")
            if json.loads(intent.read_text(encoding="utf-8")) != expected_intent:
                raise RuntimeError(f"prior {slot} canary intent differs from the frozen request; do not retry")
            record = _retained_call(records[0], freeze=freeze,
                                    slot=slot, payload=payload, schema=schema, prompt=prompt)
        else:
            if list((output_root / slot).glob("*.json")):
                raise RuntimeError(f"orphaned prior {slot} canary call; do not retry")
            with intent.open("x", encoding="utf-8") as handle:
                handle.write(json.dumps(expected_intent, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            caller = StructuredCodexCliAgentCaller(output_root / slot, model=freeze["qualified_annotator"]["model"],
                                                    effort=freeze["qualified_annotator"]["reasoning_effort"])
            record = caller.call(logical_role=f"source-context-canary-{slot}", payload=payload, schema=schema, prompt=prompt)
        returned = validate_return(packet, record["parsed_final"])
        call_path = output_root / slot / f"{record['cache_key']}.json"
        passes.append({"slot": slot, "call_raw_sha256": digest(call_path),
                       **score(case, returned)})
    result = {"schema": "crane-evidence-calibration-source-context-canary-result/v1",
              "freeze_raw_sha256": digest(FREEZE), "case_raw_sha256": freeze["case"]["raw_sha256"],
              "passes": passes, "status": "PASS_MEASUREMENT_EXTENSION" if all(row["passed"] for row in passes)
              else "FAILED_RETAIN_NO_RETRY", "pilot_annotation_performed": False,
              "confirmation_independent_n": 0, "confirmatory_alpha_consumed": 0.0}
    result_path = output_root / "canary-result.json"
    if result_path.exists():
        raise RuntimeError("refusing to overwrite source-context canary result")
    result_path.write_bytes(canonical_json_bytes(result) + b"\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT / "model_outputs/automated_annotations/evidence-calibration-source-context-canary-v1")
    args = parser.parse_args()
    result = run(args.output_root)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS_MEASUREMENT_EXTENSION" else 1


if __name__ == "__main__":
    raise SystemExit(main())
