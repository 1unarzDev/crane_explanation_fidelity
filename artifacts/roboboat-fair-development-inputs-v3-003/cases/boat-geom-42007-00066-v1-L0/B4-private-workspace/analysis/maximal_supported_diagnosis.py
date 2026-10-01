#!/usr/bin/env python3
"""Select the maximal diagnostic claim set justified by robot-visible evidence."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from evidence_calibration import (
    ClaimEvaluation,
    DiagnosticResult,
    DiagnosticState,
    RequirementEvaluation,
    RequirementStatus,
    RESULT_SCHEMA,
    evidence_ids_by_role,
    validate_requirement_references,
    validate_diagnostic_result,
)
from evidence_calibration_io import canonical_json_bytes, canonical_sha256, ontology_from_dict


FACT_SCHEMA = "crane-visible-evidence-requirement-facts/v1"
ALGORITHM_ID = "maximal-supported-diagnosis"
ALGORITHM_VERSION = "v1-development"


def _closed(value: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    if required - set(value) or set(value) - required - optional:
        raise ValueError(f"{label} has missing or unknown fields")


def _ancestor(ancestor: str, node: str, nodes: dict[str, Any]) -> bool:
    pending, seen = list(nodes[node].parent_node_ids), set()
    while pending:
        current = pending.pop()
        if current == ancestor:
            return True
        if current not in seen:
            seen.add(current)
            pending.extend(nodes[current].parent_node_ids)
    return False


def _descendants(node_id: str, nodes: dict[str, Any]) -> set[str]:
    return {candidate for candidate in nodes if candidate != node_id and _ancestor(node_id, candidate, nodes)}


def _supported_nodes(supported_claims: set[str], nodes: dict[str, Any]) -> set[str]:
    candidates = {identifier for identifier, node in nodes.items() if set(node.claim_ids).issubset(supported_claims)}
    return {
        identifier for identifier in candidates
        if all(parent in candidates for parent in _all_ancestors(identifier, nodes))
    }


def _all_ancestors(node_id: str, nodes: dict[str, Any]) -> set[str]:
    result, pending = set(), list(nodes[node_id].parent_node_ids)
    while pending:
        current = pending.pop()
        if current not in result:
            result.add(current)
            pending.extend(nodes[current].parent_node_ids)
    return result


def _maximal(nodes_supported: set[str], nodes: dict[str, Any]) -> tuple[str, ...]:
    nonmaximal = {
        identifier for identifier in nodes_supported
        if any(_ancestor(identifier, other, nodes) for other in nodes_supported if other != identifier)
    }
    return tuple(sorted(nodes_supported - nonmaximal))


def diagnose(ontology_dict: dict[str, Any], condition_entry: dict[str, Any],
             facts: dict[str, Any]) -> dict[str, Any]:
    ontology = ontology_from_dict(ontology_dict)
    _closed(condition_entry, {"condition", "method_packet"}, set(), "condition entry")
    condition, method_packet = condition_entry["condition"], condition_entry["method_packet"]
    if condition.get("method_packet_sha256") != canonical_sha256(method_packet):
        raise ValueError("condition packet hash mismatch")
    _closed(facts, {"schema", "condition_id", "method_packet_sha256", "question_contract",
                    "requirement_evaluations", "ambiguity_node_ids"}, set(), "fact packet")
    if facts["schema"] != FACT_SCHEMA or facts["condition_id"] != condition["condition_id"] \
            or facts["method_packet_sha256"] != condition["method_packet_sha256"]:
        raise ValueError("fact packet does not bind the evidence condition")
    question = facts["question_contract"]
    _closed(question, {"question_id", "failure_premise", "required_mechanism_families"}, set(),
            "question contract")
    required_families = tuple(question["required_mechanism_families"])
    if not required_families or len(required_families) != len(set(required_families)):
        raise ValueError("question needs unique required mechanism families")
    known_families = {item.mechanism_family for item in ontology.diagnostic_nodes}
    if not set(required_families).issubset(known_families):
        raise ValueError("question references an unknown mechanism family")

    requirements_by_id = {item.requirement_id: item for item in ontology.evidence_requirements}
    requirements = set(requirements_by_id)
    available_ids = set(condition["available_evidence_ids"])
    role_ids = evidence_ids_by_role(method_packet)
    evaluations: dict[str, RequirementEvaluation] = {}
    for item in facts["requirement_evaluations"]:
        _closed(item, {"requirement_id", "status", "support_references", "detail"}, set(),
                "requirement evaluation")
        identifier = item["requirement_id"]
        if identifier not in requirements or identifier in evaluations:
            raise ValueError("requirement evaluation is unknown or duplicated")
        status = RequirementStatus(item["status"])
        references = tuple(item["support_references"])
        if len(references) != len(set(references)) or not set(references).issubset(available_ids):
            raise ValueError("requirement references evidence unavailable to the method")
        validate_requirement_references(requirements_by_id[identifier], status, references, role_ids)
        evaluations[identifier] = RequirementEvaluation(identifier, status, references, item["detail"])
    if set(evaluations) != requirements:
        raise ValueError("fact packet must evaluate every registered requirement")

    claims = {item.claim_id: item for item in ontology.claim_contracts}
    claim_evaluations = []
    supported_claims, contradicted_claims = set(), set()
    missing_requirements = set()
    for contract in ontology.claim_contracts:
        rows = tuple(evaluations[item] for item in contract.required_evidence_ids)
        supported = all(item.status is RequirementStatus.SATISFIED for item in rows)
        contradicted = any(item.status is RequirementStatus.CONTRADICTED for item in rows)
        if supported:
            supported_claims.add(contract.claim_id)
        if contradicted:
            contradicted_claims.add(contract.claim_id)
        missing_requirements.update(
            item.requirement_id for item in rows
            if item.status in {RequirementStatus.ABSENT, RequirementStatus.INVALID}
        )
        claim_evaluations.append(ClaimEvaluation(
            claim_id=contract.claim_id, supported=supported, requirement_evaluations=rows,
            support_references=tuple(sorted({ref for item in rows for ref in item.support_references})),
            contradiction_references=tuple(sorted({ref for item in rows if item.status is RequirementStatus.CONTRADICTED for ref in item.support_references})),
            limitations=contract.limitations,
        ))

    nodes = {item.node_id: item for item in ontology.diagnostic_nodes}
    supported_nodes = _supported_nodes(supported_claims, nodes)
    maximal = _maximal(supported_nodes, nodes)
    ambiguity = tuple(facts["ambiguity_node_ids"])
    if len(ambiguity) != len(set(ambiguity)) or len(ambiguity) == 1 or not set(ambiguity).issubset(nodes):
        raise ValueError("ambiguity must be empty or contain known unique alternatives")
    if ambiguity:
        families = {nodes[item].mechanism_family for item in ambiguity}
        if len(families) != 1 or any(_ancestor(left, right, nodes) for left in ambiguity for right in ambiguity if left != right):
            raise ValueError("ambiguity alternatives must be incomparable within one family")
        if any(item in supported_nodes for item in ambiguity):
            raise ValueError("a definitively supported node cannot remain an ambiguity alternative")

    family_nodes = {family: [item for item in maximal if nodes[item].mechanism_family == family]
                    for family in required_families}
    false_premise = "claim-false-premise-success" in supported_claims
    no_required_diagnosis = any(not family_nodes[family] for family in required_families)
    partial = False
    for family in required_families:
        for node_id in family_nodes[family]:
            possible_deeper = _descendants(node_id, nodes)
            if any(not set(nodes[item].claim_ids).issubset(contradicted_claims) for item in possible_deeper):
                partial = True
    if false_premise:
        state = DiagnosticState.FALSE_PREMISE
    elif ambiguity:
        state = DiagnosticState.AMBIGUOUS
    elif no_required_diagnosis:
        state = DiagnosticState.INSUFFICIENT_EVIDENCE
    elif partial:
        state = DiagnosticState.SUPPORTED_PARTIAL
    elif not question["failure_premise"] and "claim-task-success" in supported_claims:
        state = DiagnosticState.NOT_TRIGGERED
    else:
        state = DiagnosticState.KNOWN

    required_non_entailments = tuple(sorted({
        relation_id for claim_id in supported_claims for relation_id in claims[claim_id].non_entailment_ids
    }))
    result = DiagnosticResult(
        schema=RESULT_SCHEMA, episode_id=condition["episode_id"],
        configuration_id=condition["configuration_id"], condition_id=condition["condition_id"],
        contract_catalog_id=ontology.catalog_id, contract_catalog_sha256=canonical_sha256(ontology),
        diagnostic_algorithm_id=ALGORITHM_ID, diagnostic_algorithm_version=ALGORITHM_VERSION,
        state=state, maximal_node_ids=maximal, approved_claim_ids=tuple(sorted(supported_claims)),
        claim_evaluations=tuple(claim_evaluations),
        missing_requirement_ids=tuple(sorted(missing_requirements)),
        contradicted_claim_ids=tuple(sorted(contradicted_claims)), ambiguity_node_ids=ambiguity,
        required_non_entailment_ids=required_non_entailments,
    )
    validate_diagnostic_result(result, ontology)
    return asdict(result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", type=Path, required=True)
    parser.add_argument("--condition-entry", type=Path, required=True)
    parser.add_argument("--facts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = diagnose(
        json.loads(args.ontology.read_text(encoding="utf-8")),
        json.loads(args.condition_entry.read_text(encoding="utf-8")),
        json.loads(args.facts.read_text(encoding="utf-8")),
    )
    args.output.write_bytes(canonical_json_bytes(result) + b"\n")


if __name__ == "__main__":
    main()
