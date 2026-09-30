"""Lossless raw-summary/structured B0/B1 request preparation; no model execution or scoring."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_evidence_calibration_method_packets import _scan
from evidence_calibration_io import canonical_sha256
from prepare_evidence_calibration_b3_ordinary import ANSWER_SCHEMA

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "research/explanation_fidelity/prompts/evidence_calibration_baseline_ordinary_development_v1.txt"
REQUEST_SCHEMA = "crane-baseline-ordinary-request/v1-development"


def raw_summary(packet: dict) -> str:
    """Describe retained fields/roles without selecting facts or inferring new propositions."""
    if not isinstance(packet, dict) or not isinstance(packet.get("evidence"), dict):
        raise ValueError("raw summary needs a structured runtime record")
    _scan(packet)
    lines = []
    for key in sorted(packet):
        if key != "evidence":
            lines.append(f"Episode field {json.dumps(key)}: {json.dumps(packet[key], sort_keys=True, allow_nan=False)}.")
    for role in sorted(packet["evidence"]):
        lines.append(f"Retained record {json.dumps(role)}: {json.dumps(packet['evidence'][role], sort_keys=True, allow_nan=False)}.")
    text = "\n".join(lines)
    if decode_raw_summary(text) != packet:
        raise ValueError("raw summary did not preserve every retained value")
    return text


def decode_raw_summary(text: str) -> dict:
    """Mechanical round-trip check; never treats summaries as generated diagnoses."""
    output = {"evidence": {}}
    decoder = json.JSONDecoder()
    for line in text.splitlines():
        if line.startswith("Episode field "):
            target, remainder = output, line[len("Episode field "):]
        elif line.startswith("Retained record "):
            target, remainder = output["evidence"], line[len("Retained record "):]
        else:
            raise ValueError("unregistered raw-summary record line")
        key, index = decoder.raw_decode(remainder)
        if not isinstance(key, str) or key in target or remainder[index:index + 2] != ": ":
            raise ValueError("duplicate or malformed raw-summary key")
        value, end = decoder.raw_decode(remainder, index + 2)
        if remainder[end:] != ".":
            raise ValueError("raw-summary record has an unregistered suffix")
        target[key] = value
    return output


def prepare(method: str, entry: dict, packet_set: dict) -> dict:
    if method not in {"B0", "B1"}:
        raise ValueError("ordinary baseline helper accepts only B0/B1")
    condition, runtime = entry["condition"], entry["method_packet"]
    if (condition.get("visibility") != "robot_visible" or condition.get("evaluator_only_absent") is not True
            or condition["method_packet_sha256"] != canonical_sha256(runtime)):
        raise ValueError("baseline runtime identity or visibility changed")
    _scan(runtime)
    _scan(packet_set)
    packets = packet_set["method_packets"]
    by_id = {packet["method_id"]: packet for packet in packets}
    if len(packets) != 5 or set(by_id) != {"B0", "B1", "B2", "B3", "B4"}:
        raise ValueError("baseline request requires the complete method-packet set")
    for baseline in ("B0", "B1"):
        packet = by_id[baseline]
        visible = json.loads(packet["presentation"]) if baseline == "B0" else packet["presentation"]
        if (packet["packet_sha256"] != canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})
                or visible != runtime or packet["method_packet_sha256"] != condition["method_packet_sha256"]
                or packet["condition_id"] != condition["condition_id"] or packet["episode_id"] != condition["episode_id"]
                or packet["question_instruction"] != runtime["question"]):
            raise ValueError("baseline packet or same-evidence binding mismatch")
        if (packet["source_assets"] or packet["primitive_tools"] or packet["contract_assets"]
                or packet["final_claim_verification"] is not False):
            raise ValueError("B0/B1 baseline cannot receive source, tools, contracts or verification")
    if by_id["B0"]["evidence_basis_sha256"] != by_id["B1"]["evidence_basis_sha256"]:
        raise ValueError("baseline evidence basis differs")
    presentation = raw_summary(runtime) if method == "B0" else json.dumps(runtime, indent=2, sort_keys=True, allow_nan=False)
    label = "Ordinary retained runtime summary" if method == "B0" else "Structured retained runtime record"
    prompt = PROMPT.read_text() + f"\n\n{label}:\n" + presentation
    request = {"schema": REQUEST_SCHEMA, "method": method, "episode_id": condition["episode_id"],
               "condition_id": condition["condition_id"], "method_packet_sha256": condition["method_packet_sha256"],
               "source_method_packet_sha256": by_id[method]["packet_sha256"],
               "packet_set_sha256": canonical_sha256(packet_set),
               "presentation_version": "lossless-retained-role-summary/v1" if method == "B0" else "structured-json/v1",
               "presentation_sha256": hashlib.sha256(presentation.encode()).hexdigest(),
               "prompt_template_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest(),
               "prompt": prompt, "output_schema": ANSWER_SCHEMA}
    request["request_sha256"] = canonical_sha256(request)
    return request


def retain_answer(request: dict, record: dict) -> dict:
    if (request.get("schema") != REQUEST_SCHEMA or request.get("method") not in {"B0", "B1"}
            or request.get("request_sha256") != canonical_sha256({k: v for k, v in request.items() if k != "request_sha256"})):
        raise ValueError("baseline request integrity changed")
    if (record.get("schema") != "crane-explain-model-call/v1" or type(record.get("return_code")) is not int
            or record["return_code"] != 0 or record.get("timed_out") is not False):
        raise ValueError("baseline technical failure must remain retained without semantic repair")
    if record["request"]["prompt"] != request["prompt"] or record["request"]["schema"] != request["output_schema"]:
        raise ValueError("baseline call prompt or output-schema identity mismatch")
    parsed = json.loads(record["raw_final"])
    if (parsed != record.get("parsed_final") or not isinstance(parsed, dict)
            or set(parsed) != {"answer"} or not isinstance(parsed["answer"], str)):
        raise ValueError("baseline raw/parsed answer envelope mismatch")
    return {"schema": "crane-baseline-ordinary-output/v1-development", "method": request["method"],
            "episode_id": request["episode_id"], "condition_id": request["condition_id"],
            "request_sha256": request["request_sha256"], "method_packet_sha256": request["method_packet_sha256"],
            "answer": parsed["answer"], "raw_call_record_sha256": canonical_sha256(record),
            "raw_final_sha256": hashlib.sha256(record["raw_final"].encode()).hexdigest(),
            "semantic_verification_executed": False, "answer_repaired": False,
            "fallback_executed": False, "endpoint_scoring_authorized": False}
