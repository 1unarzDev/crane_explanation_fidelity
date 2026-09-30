"""Pure fair tool-agent request and verbatim return helpers; no caller or study activation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_evidence_calibration_method_packets import _scan
from evidence_calibration_io import canonical_sha256
from prepare_evidence_calibration_b3_ordinary import ANSWER_SCHEMA
from stage_evidence_calibration_workspace import prepare_files, staged_workspace

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "research/explanation_fidelity/prompts/evidence_calibration_b2_development_v1.txt"
REQUEST_SCHEMA = "crane-b2-agent-request/v1-development"
ACCESS_INSTRUCTION = """The governed job files are:
- robot_visible/evidence.json
- source/behavior_tree.xml
- source/nav2.yaml
- source/diagnostic_config.json
- tools/inspect_evidence_calibration_packet.py

Read the evidence file and relevant source/configuration. You may run the supplied primitive tool
and perform local computations over the supplied records, including delivered command and measured
speed, synchronized intervals, discrepancy thresholds, response recovery and non-trigger checks.
Use the supplied diagnostic configuration for its registered thresholds. You may inspect full
retained samples and source details; the inventory tool is a convenience, not the only computation
permitted. No diagnostic contract or approved diagnosis is supplied to this agent.
Return the answer object required by the output schema.
"""


def prepare(entry: dict, packet_set: dict) -> dict:
    _scan(packet_set)
    packets = packet_set["method_packets"]
    by_id = {packet["method_id"]: packet for packet in packets}
    if len(packets) != 5 or set(by_id) != {"B0", "B1", "B2", "B3", "B4"}:
        raise ValueError("B2 requires the complete paired method-packet set")
    for method in ("B2", "B3", "B4"):
        prepare_files(entry, by_id[method])
    for field in ("source_assets", "primitive_tools", "evidence_basis_sha256"):
        if not by_id["B2"][field] == by_id["B3"][field] == by_id["B4"][field]:
            raise ValueError("B2/B3/B4 information or tool parity changed")
    if (by_id["B2"]["method_class"] != "TOOL_ENABLED_AGENT"
            or by_id["B2"]["final_claim_verification"] is not False
            or by_id["B2"]["contract_assets"]):
        raise ValueError("B2 cannot receive contracts or final claim verification")
    with staged_workspace(entry, by_id["B2"]) as (_, identity):
        workspace_identity = identity
    question = entry["method_packet"]["question"]
    request = {"schema": REQUEST_SCHEMA, "method": "B2", "episode_id": by_id["B2"]["episode_id"],
               "condition_id": by_id["B2"]["condition_id"],
               "method_packet_sha256": by_id["B2"]["method_packet_sha256"],
               "source_method_packet_sha256": by_id["B2"]["packet_sha256"],
               "packet_set_sha256": canonical_sha256(packet_set), "workspace_identity": workspace_identity,
               "prompt": PROMPT.read_text() + "\n\n" + ACCESS_INSTRUCTION + "\nQuestion:\n" + question,
               "prompt_template_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest(),
               "output_schema": ANSWER_SCHEMA, "access_instruction_version": "visible-local-computation/v1-development",
               "harness_permissions_enforced": False, "model_calls_authorized": False}
    request["request_sha256"] = canonical_sha256(request)
    return request


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("B2 duplicate JSON key")
        result[key] = value
    return result


def retain_answer(entry: dict, packet_set: dict, request: dict, record: dict) -> dict:
    """Preserve ordinary answers after technical checks; no verifier, fallback or retry."""
    if request != prepare(entry, packet_set):
        raise ValueError("B2 request/input binding changed")
    if (record.get("schema") != "crane-explain-model-call/v1" or type(record.get("return_code")) is not int
            or record["return_code"] != 0 or record.get("timed_out") is not False):
        raise ValueError("B2 technical failure must remain retained without retry")
    if (record["request"]["prompt"] != request["prompt"]
            or record["request"]["schema"] != request["output_schema"]):
        raise ValueError("B2 call prompt/schema identity mismatch")
    raw = record.get("raw_final")
    if not isinstance(raw, str):
        raise ValueError("B2 raw final must be retained text")
    parsed = json.loads(raw, object_pairs_hook=_unique_object)
    if (parsed != record.get("parsed_final") or not isinstance(parsed, dict)
            or set(parsed) != {"answer"} or not isinstance(parsed["answer"], str)):
        raise ValueError("B2 raw/parsed answer envelope mismatch")
    return {"schema": "crane-b2-agent-return/v1-development", "method": "B2",
            "episode_id": request["episode_id"], "condition_id": request["condition_id"],
            "request_sha256": request["request_sha256"], "method_packet_sha256": request["method_packet_sha256"],
            "answer": parsed["answer"], "raw_call_record_sha256": canonical_sha256(record),
            "raw_final_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "semantic_verification_executed": False, "answer_repaired": False, "fallback_executed": False,
            "harness_event_audit_required": True, "endpoint_scoring_authorized": False}
