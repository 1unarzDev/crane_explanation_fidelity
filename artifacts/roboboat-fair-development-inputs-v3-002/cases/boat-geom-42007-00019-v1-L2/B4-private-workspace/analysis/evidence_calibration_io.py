"""Strict, deterministic JSON transport for evidence-calibration records."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Mapping

from evidence_calibration import (
    ClaimContract,
    ClaimKind,
    DiagnosticNode,
    EvidenceCalibrationOntology,
    EvidenceRequirement,
    NonEntailment,
    NumericSlot,
    ONTOLOGY_SCHEMA,
    Parameter,
    validate_ontology,
)


def _json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _json_value(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(_json_value(value), sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _closed(value: Mapping[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise ValueError(f"{label} is missing fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"{label} has unknown fields: {sorted(unknown)}")


def ontology_from_dict(value: Mapping[str, Any]) -> EvidenceCalibrationOntology:
    _closed(
        value,
        {"schema", "catalog_id", "catalog_version", "evidence_requirements", "claim_contracts",
         "non_entailments", "diagnostic_nodes"},
        set(),
        "ontology",
    )
    if value["schema"] != ONTOLOGY_SCHEMA:
        raise ValueError("unsupported ontology schema")

    requirements = []
    for item in value["evidence_requirements"]:
        _closed(item, {"requirement_id", "evidence_roles", "predicate_id", "predicate_version",
                       "description"}, {"parameters"}, "evidence requirement")
        parameters = []
        for parameter in item.get("parameters", []):
            _closed(parameter, {"key", "value"}, set(), "requirement parameter")
            parameters.append(Parameter(parameter["key"], parameter["value"]))
        requirements.append(EvidenceRequirement(
            item["requirement_id"], tuple(item["evidence_roles"]), item["predicate_id"],
            item["predicate_version"], item["description"], tuple(parameters)
        ))

    claims = []
    for item in value["claim_contracts"]:
        _closed(item, {"claim_id", "proposition", "mechanism_family", "claim_kind",
                       "diagnostic_node_id", "required_evidence_ids"},
                {"optional_evidence_ids", "non_entailment_ids", "numeric_slots", "limitations"},
                "claim contract")
        slots = []
        for slot in item.get("numeric_slots", []):
            _closed(slot, {"slot_id", "unit"}, {"tolerance"}, "numeric slot")
            slots.append(NumericSlot(slot["slot_id"], slot["unit"], slot.get("tolerance")))
        claims.append(ClaimContract(
            item["claim_id"], item["proposition"], item["mechanism_family"],
            ClaimKind(item["claim_kind"]), item["diagnostic_node_id"],
            tuple(item["required_evidence_ids"]), tuple(item.get("optional_evidence_ids", [])),
            tuple(item.get("non_entailment_ids", [])), tuple(slots),
            tuple(item.get("limitations", [])),
        ))

    relations = []
    for item in value["non_entailments"]:
        _closed(item, {"non_entailment_id", "basis_claim_ids", "unsupported_consequent_claim_ids",
                       "rationale"}, {"additional_evidence_requirement_ids"}, "non-entailment")
        relations.append(NonEntailment(
            item["non_entailment_id"], tuple(item["basis_claim_ids"]),
            tuple(item["unsupported_consequent_claim_ids"]), item["rationale"],
            tuple(item.get("additional_evidence_requirement_ids", [])),
        ))

    nodes = []
    for item in value["diagnostic_nodes"]:
        _closed(item, {"node_id", "mechanism_family", "label", "rank_within_family",
                       "parent_node_ids", "claim_ids"},
                {"required_evidence_ids", "contradiction_claim_ids"}, "diagnostic node")
        nodes.append(DiagnosticNode(
            item["node_id"], item["mechanism_family"], item["label"], item["rank_within_family"],
            tuple(item["parent_node_ids"]), tuple(item["claim_ids"]),
            tuple(item.get("required_evidence_ids", [])),
            tuple(item.get("contradiction_claim_ids", [])),
        ))

    ontology = EvidenceCalibrationOntology(
        value["schema"], value["catalog_id"], value["catalog_version"], tuple(requirements),
        tuple(claims), tuple(relations), tuple(nodes)
    )
    validate_ontology(ontology)
    return ontology
