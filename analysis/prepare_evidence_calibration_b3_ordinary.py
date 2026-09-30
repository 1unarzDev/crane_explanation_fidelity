"""Prepare ordinary B3 realization and retain its answer without semantic checking or repair.

Pure development helpers: no provider call, workspace staging, retry, pilot activation or key join.
The enclosing prospective runner must bind model/transport/budgets and retain one-shot records.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from build_evidence_calibration_method_packets import _scan
from evidence_calibration_io import canonical_sha256, ontology_from_dict
from maximal_supported_diagnosis import diagnose
from realize_evidence_calibrated_explanation import _validate_plan

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "research/explanation_fidelity/prompts/evidence_calibration_b3_ordinary_development_v1.txt"
DECLARATION = ROOT / "manifests/study/evidence-calibration-b3-ordinary-interface-v1-development.json"
ANSWER_SCHEMA = {"type": "object", "properties": {"answer": {"type": "string"}},
                 "required": ["answer"], "additionalProperties": False}
REQUEST_SCHEMA = "crane-b3-ordinary-realization-request/v1-development"


def prepare(ontology: dict, entry: dict, facts: dict, plan: dict, packet_set: dict) -> dict:
    """Export the existing planner's supported content to an ordinary language request.

    `facts` must come from the governed robot-visible computation in the enclosing runner.
    The diagnostic engine verifies their binding to `entry`; no evaluator reference is accepted.
    """
    if (entry["condition"].get("visibility") != "robot_visible"
            or entry["condition"].get("evaluator_only_absent") is not True):
        raise ValueError("B3 condition must be certified robot-visible")
    _scan(entry["method_packet"])
    _scan(facts)
    _scan(packet_set)
    result = diagnose(ontology, entry, facts)
    _validate_plan(plan, result, ontology_from_dict(ontology))
    packets = packet_set["method_packets"]
    by_id = {packet["method_id"]: packet for packet in packets}
    if len(packets) != 5 or set(by_id) != {"B0", "B1", "B2", "B3", "B4"}:
        raise ValueError("B3 request requires the complete paired method-packet set")
    for method in ("B2", "B3", "B4"):
        packet = by_id[method]
        hashed = {key: value for key, value in packet.items() if key != "packet_sha256"}
        if (packet["packet_sha256"] != canonical_sha256(hashed)
                or packet["method_packet_sha256"] != entry["condition"]["method_packet_sha256"]
                or packet["condition_id"] != result["condition_id"]
                or packet["episode_id"] != result["episode_id"]
                or packet["presentation"] != entry["method_packet"]
                or packet["question_instruction"] != entry["method_packet"]["question"]):
            raise ValueError("B3 request packet identity or visible-evidence binding mismatch")
    if (by_id["B3"]["method_class"] != "DIAGNOSTIC_CONTRACT_UNVERIFIED"
            or by_id["B3"]["final_claim_verification"] is not False
            or by_id["B4"]["final_claim_verification"] is not True):
        raise ValueError("B3 must retain ordinary realization without final verification")
    for field in ("source_assets", "primitive_tools", "evidence_basis_sha256"):
        if not by_id["B2"][field] == by_id["B3"][field] == by_id["B4"][field]:
            raise ValueError("B2/B3/B4 source, primitive-tool or evidence parity changed")
    if by_id["B3"]["contract_assets"] != by_id["B4"]["contract_assets"]:
        raise ValueError("B3 and B4 must share the diagnostic contract assets")
    contracts = {claim["claim_id"]: claim for claim in ontology["claim_contracts"]}
    relations = {relation["non_entailment_id"]: relation for relation in ontology["non_entailments"]}
    selected = plan["required_claim_ids"] + plan["optional_claim_ids"]
    context = {
        "question": entry["method_packet"]["question"], "robot_visible_evidence": entry["method_packet"],
        "source_assets": by_id["B3"]["source_assets"], "primitive_tools": by_id["B3"]["primitive_tools"],
        "diagnostic_plan": {
            "state": result["state"], "ambiguity_node_ids": list(result["ambiguity_node_ids"]),
            "approved_claims": [{"claim_id": identifier, "proposition": contracts[identifier]["proposition"],
                                 "required": identifier in plan["required_claim_ids"]} for identifier in selected],
            "approved_numeric_values": plan["approved_numeric_values"],
            "required_limitations": [{"non_entailment_id": identifier, "text": relations[identifier]["rationale"]}
                                     for identifier in plan["required_non_entailment_ids"]],
            "missing_requirement_ids": list(result["missing_requirement_ids"]),
        },
    }
    _scan(context)
    prompt = PROMPT.read_text() + "\n\nGoverned realization data:\n" + json.dumps(context, indent=2, sort_keys=True, allow_nan=False)
    request = {"schema": REQUEST_SCHEMA, "method": "B3", "episode_id": result["episode_id"],
               "condition_id": result["condition_id"], "method_packet_sha256": entry["condition"]["method_packet_sha256"],
               "packet_set_sha256": canonical_sha256(packet_set), "ontology_sha256": canonical_sha256(ontology),
               "facts_sha256": canonical_sha256(facts), "diagnostic_result_sha256": canonical_sha256(result),
               "plan_sha256": canonical_sha256(plan), "prompt": prompt, "output_schema": ANSWER_SCHEMA,
               "prompt_template_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest()}
    request["request_sha256"] = canonical_sha256(request)
    return request


def retain_answer(request: dict, record: dict) -> dict:
    """Check transport/envelope identity only and preserve the complete answer verbatim.

    Empty strings, unsupported claims, omitted limits and wrong numbers are semantic behavior,
    not technical grounds for fallback or retry. Measurement remains a separate gated process.
    """
    if (request.get("schema") != REQUEST_SCHEMA or request.get("method") != "B3"
            or request.get("request_sha256") != canonical_sha256(
                {key: value for key, value in request.items() if key != "request_sha256"})):
        raise ValueError("B3 request integrity changed")
    if (record.get("schema") != "crane-explain-model-call/v1" or type(record.get("return_code")) is not int
            or record["return_code"] != 0 or record.get("timed_out") is not False):
        raise ValueError("B3 technical failure must remain retained without semantic repair")
    if (record["request"]["prompt"] != request["prompt"]
            or record["request"]["schema"] != request["output_schema"]):
        raise ValueError("B3 call prompt or output-schema identity mismatch")
    raw = record.get("raw_final")
    if not isinstance(raw, str):
        raise ValueError("B3 raw final must be retained text")
    parsed = json.loads(raw)
    if (parsed != record.get("parsed_final") or not isinstance(parsed, dict)
            or set(parsed) != {"answer"} or not isinstance(parsed["answer"], str)):
        raise ValueError("B3 raw/parsed answer envelope mismatch")
    return {"schema": "crane-b3-ordinary-realization-output/v1-development", "method": "B3",
            "episode_id": request["episode_id"], "condition_id": request["condition_id"],
            "request_sha256": request["request_sha256"], "method_packet_sha256": request["method_packet_sha256"],
            "answer": parsed["answer"], "raw_call_record_sha256": canonical_sha256(record),
            "raw_final_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "semantic_verification_executed": False, "answer_repaired": False,
            "fallback_executed": False, "endpoint_scoring_authorized": False}


def audit_candidate() -> dict:
    declaration = json.loads(DECLARATION.read_text())
    if (declaration.get("schema") != "crane-b3-ordinary-interface/v1-development"
            or declaration.get("status") != "ORDINARY_REQUEST_RETENTION_HELPERS_READY_EXECUTION_UNBOUND"
            or any(declaration.get(key) is not False for key in
                   ("model_calls_authorized", "pilot_annotation_authorized", "p11_authorized",
                    "pure_verifier_only_ablation_claimed", "model_backed_execution_complete"))):
        raise ValueError("B3 interface cannot activate execution or a pure-verifier claim")
    bindings = declaration["bindings"]
    required = {"helper", "prompt", "tests", "ontology", "planner", "plan_validator", "packet_builder",
                "failed_measurement_gate", "note"}
    if set(bindings) != required:
        raise ValueError("B3 interface bindings incomplete")
    for item in bindings.values():
        if hashlib.sha256((ROOT / item["path"]).read_bytes()).hexdigest() != item["raw_sha256"]:
            raise ValueError("B3 interface component hash mismatch")
    return {"schema": "crane-b3-ordinary-interface-audit/v1-development",
            "status": "PASS_INTERFACE_ONLY_EXECUTION_UNBOUND", "bound_components": len(bindings),
            "model_calls_authorized": False, "model_backed_execution_complete": False,
            "pure_verifier_only_ablation_claimed": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit_candidate(), indent=2, sort_keys=True))
