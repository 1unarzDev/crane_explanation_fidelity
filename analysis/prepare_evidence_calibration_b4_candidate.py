"""Pure B4 candidate request/return interface; no execution, retries or endpoint scoring."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from evidence_calibration_io import canonical_sha256
from maximal_supported_diagnosis import diagnose
from prepare_evidence_calibration_b3_ordinary import prepare as validate_shared_inputs
from realize_evidence_calibrated_explanation_v2 import CANDIDATE_SCHEMA, REALIZER_VERSION, realize

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT / "research/explanation_fidelity/prompts/evidence_calibration_b4_candidate_development_v1.txt"
REQUEST_SCHEMA = "crane-b4-candidate-request/v1-development"


def output_schema(response_id: str, plan_sha256: str) -> dict:
    numeric = {"type": "object", "properties": {"slot_id": {"type": "string"},
               "value": {"type": "number"}, "unit": {"type": "string"}},
               "required": ["slot_id", "value", "unit"], "additionalProperties": False}
    clause = {"type": "object", "properties": {"clause_id": {"type": "string", "minLength": 1},
              "kind": {"type": "string", "enum": ["CLAIM", "NON_ENTAILMENT"]},
              "contract_id": {"type": "string"}, "numeric_values": {"type": "array", "items": numeric}},
              "required": ["clause_id", "kind", "contract_id", "numeric_values"], "additionalProperties": False}
    return {"type": "object", "properties": {
        "schema": {"type": "string", "enum": [CANDIDATE_SCHEMA]},
        "response_id": {"type": "string", "enum": [response_id]},
        "plan_sha256": {"type": "string", "enum": [plan_sha256]},
        "clauses": {"type": "array", "items": clause}},
        "required": ["schema", "response_id", "plan_sha256", "clauses"], "additionalProperties": False}


def validate_candidate(candidate: dict, request: dict) -> None:
    """Check the exact output envelope; semantic contract/quantity errors reach the realizer."""
    if (not isinstance(candidate, dict) or set(candidate) != {"schema", "response_id", "plan_sha256", "clauses"}
            or candidate["schema"] != CANDIDATE_SCHEMA or candidate["response_id"] != request["response_id"]
            or candidate["plan_sha256"] != request["plan_sha256"] or not isinstance(candidate["clauses"], list)):
        raise ValueError("B4 candidate envelope mismatch")
    for clause in candidate["clauses"]:
        if (not isinstance(clause, dict) or set(clause) != {"clause_id", "kind", "contract_id", "numeric_values"}
                or not isinstance(clause["clause_id"], str) or not clause["clause_id"]
                or clause["kind"] not in ("CLAIM", "NON_ENTAILMENT")
                or not isinstance(clause["contract_id"], str) or not isinstance(clause["numeric_values"], list)):
            raise ValueError("B4 candidate clause structure mismatch")
        for value in clause["numeric_values"]:
            if (not isinstance(value, dict) or set(value) != {"slot_id", "value", "unit"}
                    or not isinstance(value["slot_id"], str) or not isinstance(value["unit"], str)
                    or type(value["value"]) not in (int, float)
                    or (isinstance(value["value"], float) and not math.isfinite(value["value"]))):
                raise ValueError("B4 candidate numeric structure mismatch")


def prepare(ontology: dict, entry: dict, facts: dict, plan: dict, packet_set: dict) -> dict:
    # Reuse the frozen shared input checks without modifying or executing the B3 path.
    shared = validate_shared_inputs(ontology, entry, facts, plan, packet_set)
    result = diagnose(ontology, entry, facts)
    response_id = "B4-candidate-" + canonical_sha256({"condition_id": result["condition_id"],
                                                   "plan_sha256": shared["plan_sha256"]})
    selected = plan["required_claim_ids"] + plan["optional_claim_ids"]
    claims = {row["claim_id"]: row for row in ontology["claim_contracts"]}
    relations = {row["non_entailment_id"]: row for row in ontology["non_entailments"]}
    context = {"response_id": response_id, "plan_sha256": shared["plan_sha256"],
               "robot_visible_evidence": entry["method_packet"], "diagnostic_plan": plan,
               "approved_propositions": [{"claim_id": identifier, "proposition": claims[identifier]["proposition"]}
                                         for identifier in selected],
               "required_limitations": [{"non_entailment_id": identifier, "text": relations[identifier]["rationale"]}
                                        for identifier in plan["required_non_entailment_ids"]],
               "state": result["state"], "ambiguity_node_ids": result["ambiguity_node_ids"],
               "missing_requirement_ids": result["missing_requirement_ids"]}
    request = {"schema": REQUEST_SCHEMA, "method": "B4", "response_id": response_id,
               **{key: shared[key] for key in ("episode_id", "condition_id", "method_packet_sha256",
                    "packet_set_sha256", "ontology_sha256", "facts_sha256", "diagnostic_result_sha256", "plan_sha256")},
               "realizer_version": REALIZER_VERSION,
               "prompt": PROMPT.read_text() + "\n\nGoverned candidate data:\n" + json.dumps(context, indent=2, sort_keys=True, allow_nan=False),
               "output_schema": output_schema(response_id, shared["plan_sha256"]),
               "prompt_template_sha256": hashlib.sha256(PROMPT.read_bytes()).hexdigest()}
    request["request_sha256"] = canonical_sha256(request)
    return request


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("B4 duplicate JSON key")
        result[key] = value
    return result


def retain_and_realize(ontology: dict, entry: dict, facts: dict, plan: dict, packet_set: dict,
                       request: dict, record: dict) -> dict:
    """Bind a successful technical return and apply the unchanged v2 local realizer once.

    The enclosing caller must persist raw/failed records before invoking this helper. Structural
    failures raise; they do not fabricate a candidate or authorize another provider invocation.
    """
    if request != prepare(ontology, entry, facts, plan, packet_set):
        raise ValueError("B4 request/input binding changed")
    if (record.get("schema") != "crane-explain-model-call/v1" or type(record.get("return_code")) is not int
            or record["return_code"] != 0 or record.get("timed_out") is not False):
        raise ValueError("B4 technical failure must remain retained without retry")
    if (record["request"]["prompt"] != request["prompt"]
            or record["request"]["schema"] != request["output_schema"]):
        raise ValueError("B4 call prompt/schema identity mismatch")
    raw = record.get("raw_final")
    if not isinstance(raw, str):
        raise ValueError("B4 raw final must be retained text")
    candidate = json.loads(raw, object_pairs_hook=_unique_object)
    validate_candidate(candidate, request)
    candidate_sha = canonical_sha256(candidate)
    if candidate != record.get("parsed_final"):
        raise ValueError("B4 raw/parsed candidate mismatch")
    result = diagnose(ontology, entry, facts)
    output = realize(ontology, result, plan, candidate)
    return {"schema": "crane-b4-candidate-return/v1-development", "method": "B4",
            "request_sha256": request["request_sha256"], "episode_id": request["episode_id"],
            "condition_id": request["condition_id"], "method_packet_sha256": request["method_packet_sha256"],
            "candidate": candidate, "candidate_sha256": candidate_sha,
            "raw_final_sha256": hashlib.sha256(raw.encode()).hexdigest(),
            "raw_call_record_sha256": canonical_sha256(record), "realization": output,
            "model_retry_authorized": False, "endpoint_scoring_authorized": False}
