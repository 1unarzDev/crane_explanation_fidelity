"""Structural checks for contextual attachment proposals; no semantic or endpoint qualification."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from evidence_calibration_io import canonical_sha256, ontology_from_dict
from validate_evidence_calibration_claim_roles_v2 import POLARITIES, STANCES

INPUT_SCHEMA = "crane-contextual-claim-attachment-input/v1-development"
RETURN_SCHEMA = "crane-contextual-claim-attachment-return/v1-development"
SCOPES = {"EPISODE_EVENT", "SOURCE_OR_CONFIG_FACT", "EVIDENTIAL_LIMITATION",
          "GENERAL_OR_HYPOTHETICAL", "UNRESOLVED"}
STATUSES = {"PROPOSED_MATCH", "OUT_OF_CATALOG", "NOT_APPLICABLE", "UNRESOLVED"}
ROOT = Path(__file__).resolve().parents[1]
DECLARATION = ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-contextual-attachment-v1.json"


def _fields(value: Any, fields: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(f"{label} has missing or unknown fields")


def _text(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonempty text")


def _span(value: dict, source: str, label: str) -> None:
    start, end = value["start"], value["end"]
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source)
            or not isinstance(value["text"], str) or source[start:end] != value["text"]):
        raise ValueError(f"{label} must match exact Unicode character offsets")


def validate(payload: dict, returned: dict, ontology: dict) -> dict:
    """Validate a supplied proposal without reading evidence, keys or assigning meaning.

    A structurally valid proposed match remains unqualified. The function cannot verify
    equivalence, endorsement, referents or polarity; those require semantic qualification.
    """
    ontology_from_dict(ontology)
    _fields(payload, {"schema", "opaque_response_id", "question_text", "response_text", "claims"}, "input")
    if payload["schema"] != INPUT_SCHEMA:
        raise ValueError("unsupported contextual input schema")
    for key in ("opaque_response_id", "question_text", "response_text"):
        _text(payload[key], key)
    claims = payload["claims"]
    if not isinstance(claims, list) or not claims:
        raise ValueError("input requires a nonempty atomic inventory")
    ids = []
    for claim in claims:
        _fields(claim, {"item_id", "claim_text", "response_span"}, "claim")
        _text(claim["item_id"], "item ID")
        _text(claim["claim_text"], "unchanged claim text")
        _fields(claim["response_span"], {"start", "end", "text"}, "response span")
        _span(claim["response_span"], payload["response_text"], "response span")
        ids.append(claim["item_id"])
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate atomic item ID")

    _fields(returned, {"schema", "opaque_response_id", "input_sha256", "ontology_sha256",
                       "claim_attachments", "attestation"}, "return")
    if (returned["schema"] != RETURN_SCHEMA or returned["opaque_response_id"] != payload["opaque_response_id"]
            or returned["input_sha256"] != canonical_sha256(payload)
            or returned["ontology_sha256"] != canonical_sha256(ontology)
            or returned["attestation"] != "UNQUALIFIED_CONTEXTUAL_ATTACHMENT_PROPOSAL"):
        raise ValueError("return identity, context/ontology binding or attestation mismatch")
    proposals = returned["claim_attachments"]
    if not isinstance(proposals, list) or [item.get("item_id") if isinstance(item, dict) else None
                                           for item in proposals] != ids:
        raise ValueError("one proposal per atom is required exactly and in order")
    contracts = {item["claim_id"]: item for item in ontology["claim_contracts"]}
    counts = {status: 0 for status in sorted(STATUSES)}
    for claim, proposal in zip(claims, proposals, strict=True):
        _fields(proposal, {"item_id", "contextual_proposition", "stance", "polarity", "scope",
                           "referent_status", "attachment_status", "proposed_contract_id",
                           "context_quotes", "scope_note"}, "proposal")
        _text(proposal["contextual_proposition"], "contextual proposition")
        _text(proposal["scope_note"], "scope note")
        stance, polarity, scope = (proposal[key] for key in ("stance", "polarity", "scope"))
        status, contract_id = proposal["attachment_status"], proposal["proposed_contract_id"]
        if (any(not isinstance(proposal[key], str) for key in
                ("stance", "polarity", "scope", "attachment_status", "referent_status"))
                or stance not in STANCES or polarity not in POLARITIES or scope not in SCOPES
                or status not in STATUSES or proposal["referent_status"] not in {"RESOLVED", "UNRESOLVED"}):
            raise ValueError("unknown contextual proposal category")
        unresolved = (stance == "UNRESOLVED" or scope == "UNRESOLVED"
                      or proposal["referent_status"] == "UNRESOLVED")
        if unresolved and (status != "UNRESOLVED" or contract_id is not None):
            raise ValueError("unresolved context cannot select a proposed contract")
        if status == "UNRESOLVED" and not unresolved:
            raise ValueError("unresolved proposal must preserve an unresolved semantic field")
        if stance not in {"ASSERTED_FACT", "HEDGED_CURRENT_EPISODE"} and polarity != "NOT_APPLICABLE":
            raise ValueError("nonasserted material cannot carry episode polarity")
        if status == "PROPOSED_MATCH":
            if (not isinstance(contract_id, str) or contract_id not in contracts
                    or stance not in {"ASSERTED_FACT", "HEDGED_CURRENT_EPISODE"}
                    or scope != "EPISODE_EVENT" or polarity != "POSITIVE"):
                raise ValueError("current positive episode contracts cannot attach to this proposal")
        elif contract_id is not None:
            raise ValueError("unmatched, unendorsed or unresolved proposals must retain null contracts")
        # Do not silently discard a concrete unmatched assertion as nonapplicable.
        if (not unresolved and stance in {"ASSERTED_FACT", "HEDGED_CURRENT_EPISODE"}
                and status == "NOT_APPLICABLE"):
            raise ValueError("asserted unmatched propositions must remain OUT_OF_CATALOG")
        quotes = proposal["context_quotes"]
        if not isinstance(quotes, list) or not quotes:
            raise ValueError("proposal requires exact contextual quotes")
        own_span_quoted = False
        for quote in quotes:
            _fields(quote, {"source", "start", "end", "text"}, "context quote")
            if quote["source"] not in {"QUESTION", "ANSWER"}:
                raise ValueError("context quote must use question or answer")
            source = payload["question_text"] if quote["source"] == "QUESTION" else payload["response_text"]
            _span(quote, source, "context quote")
            atom_span = claim["response_span"]
            if (quote["source"] == "ANSWER" and atom_span["start"] <= quote["start"]
                    and quote["end"] <= atom_span["end"]):
                own_span_quoted = True
        if not own_span_quoted:
            raise ValueError("proposal must quote its own retained atom span")
        counts[status] += 1
    return {"schema": "crane-contextual-claim-attachment-validation/v1-development",
            "status": "STRUCTURALLY_VALID_SEMANTIC_ATTACHMENT_UNQUALIFIED",
            "input_sha256": canonical_sha256(payload), "ontology_sha256": canonical_sha256(ontology),
            "return_sha256": canonical_sha256(returned), "atom_count": len(ids), "proposal_counts": counts,
            "semantic_equivalence_verified": False, "semantic_attachment_qualified": False,
            "mechanistic_flag_authorized": False, "response_rank_authorized": False,
            "endpoint_scoring_authorized": False, "pilot_annotation_authorized": False}


def audit_candidate(path: Path = DECLARATION) -> dict:
    """Read-only declaration integrity check; never accepts a pilot packet or launches a call."""
    declaration = json.loads(path.read_text())
    if (declaration.get("schema") != "crane-contextual-claim-attachment-candidate/v1-development"
            or declaration.get("status") != "STRUCTURAL_INTERFACE_ONLY_SEMANTIC_QUALIFICATION_OPEN"
            or type(declaration.get("authorized_model_calls")) is not int
            or declaration["authorized_model_calls"] != 0
            or any(declaration.get(key) is not False for key in
                   ("semantic_attachment_qualified", "endpoint_mapping_bound", "pilot_packet_construction_authorized",
                    "pilot_annotation_authorized", "method_key_join_authorized", "p11_authorized"))):
        raise ValueError("contextual attachment candidate cannot authorize measurement or endpoint use")
    expected = {
        "validator": "analysis/validate_evidence_calibration_claim_attachment.py",
        "tests": "tests/test_evidence_calibration_claim_attachment.py",
        "role_categories": "analysis/validate_evidence_calibration_claim_roles_v2.py",
        "input_schema": "research/explanation_fidelity/schemas/evidence-calibration-contextual-attachment-input-v1-development.schema.json",
        "return_schema": "research/explanation_fidelity/schemas/evidence-calibration-contextual-attachment-return-v1-development.schema.json",
        "ontology": "configs/evidence_calibration_claim_contracts_v2_development.json",
        "boundary_inventory": "manifests/annotation/evidence-calibration-attachment-boundary-v1-development.json",
        "failed_measurement_gate": "manifests/operations/evidence-calibration-combined-support-canary-disposition-v1.json",
        "note": "docs/CONTEXTUAL_ATTACHMENT_RECORDS_2026-09-30.md",
    }
    bindings = declaration.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != set(expected):
        raise ValueError("contextual attachment candidate bindings are incomplete")
    for key, relative in expected.items():
        binding = bindings[key]
        if (binding.get("path") != relative or binding.get("raw_sha256")
                != hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()):
            raise ValueError("contextual attachment candidate component hash mismatch")
    failed = json.loads((ROOT / expected["failed_measurement_gate"]).read_text())
    if (failed["status"] != "FAILED_COMBINED_CANARY_PILOT_GATE_CLOSED"
            or failed["constructed_C_calls"] != 0 or failed["pilot_annotation_authorized"] is not False
            or failed["further_candidate_cycles_authorized"] is not False):
        raise ValueError("retained failed measurement boundary changed")
    return {"schema": "crane-contextual-claim-attachment-candidate-audit/v1-development",
            "status": "PASS_STRUCTURE_ONLY_SEMANTIC_ATTACHMENT_OPEN", "bound_components": len(bindings),
            "authorized_model_calls": 0, "semantic_attachment_qualified": False,
            "endpoint_mapping_bound": False, "method_key_join_authorized": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit_candidate(), indent=2, sort_keys=True))
