"""Prospective types for evidence-calibrated robot explanations.

Kept separate from legacy diagnostic/claim records. Public contracts contain no episode
answers, physical truth, intervention identity, or evaluator labels.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


ONTOLOGY_SCHEMA = "crane-evidence-calibration-ontology/v1"
CONDITION_SCHEMA = "crane-evidence-condition/v1"
RESULT_SCHEMA = "crane-evidence-calibrated-diagnostic-result/v1"
AUDIT_SCHEMA = "crane-explanation-audit/v1"


class DiagnosticState(str, Enum):
    KNOWN = "KNOWN"
    SUPPORTED_PARTIAL = "SUPPORTED_PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FALSE_PREMISE = "FALSE_PREMISE"
    NOT_TRIGGERED = "NOT_TRIGGERED"


class RequirementStatus(str, Enum):
    SATISFIED = "SATISFIED"
    ABSENT = "ABSENT"
    INVALID = "INVALID"
    CONTRADICTED = "CONTRADICTED"


class ClaimKind(str, Enum):
    OBSERVATION = "OBSERVATION"
    TASK_OUTCOME = "TASK_OUTCOME"
    SOFTWARE_ACTION = "SOFTWARE_ACTION"
    RECOVERY_MECHANISM = "RECOVERY_MECHANISM"
    EXECUTION_DISCREPANCY = "EXECUTION_DISCREPANCY"
    PHYSICAL_MECHANISM = "PHYSICAL_MECHANISM"
    SPECIFIC_PHYSICAL_CAUSE = "SPECIFIC_PHYSICAL_CAUSE"
    LIMITATION = "LIMITATION"
    FALSE_PREMISE_REJECTION = "FALSE_PREMISE_REJECTION"


class AuditStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REPAIRED = "REPAIRED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class Parameter:
    key: str
    value: bool | int | float | str


@dataclass(frozen=True)
class EvidenceRequirement:
    requirement_id: str
    evidence_roles: tuple[str, ...]
    predicate_id: str
    predicate_version: str
    description: str
    parameters: tuple[Parameter, ...] = ()


@dataclass(frozen=True)
class NumericSlot:
    slot_id: str
    unit: str
    tolerance: float | None = None


@dataclass(frozen=True)
class ClaimContract:
    claim_id: str
    proposition: str
    mechanism_family: str
    claim_kind: ClaimKind
    diagnostic_node_id: str
    required_evidence_ids: tuple[str, ...]
    optional_evidence_ids: tuple[str, ...] = ()
    non_entailment_ids: tuple[str, ...] = ()
    numeric_slots: tuple[NumericSlot, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class NonEntailment:
    non_entailment_id: str
    basis_claim_ids: tuple[str, ...]
    unsupported_consequent_claim_ids: tuple[str, ...]
    rationale: str
    additional_evidence_requirement_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiagnosticNode:
    node_id: str
    mechanism_family: str
    label: str
    rank_within_family: int
    parent_node_ids: tuple[str, ...]
    claim_ids: tuple[str, ...]
    required_evidence_ids: tuple[str, ...] = ()
    contradiction_claim_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceCalibrationOntology:
    schema: str
    catalog_id: str
    catalog_version: str
    evidence_requirements: tuple[EvidenceRequirement, ...]
    claim_contracts: tuple[ClaimContract, ...]
    non_entailments: tuple[NonEntailment, ...]
    diagnostic_nodes: tuple[DiagnosticNode, ...]


@dataclass(frozen=True)
class EvidenceCondition:
    schema: str
    episode_id: str
    configuration_id: str
    condition_id: str
    ladder_id: str
    level_index: int
    parent_condition_id: str | None
    source_packet_sha256: str
    method_packet_sha256: str
    source_configuration_sha256: str
    runtime_manifest_sha256: str
    condition_builder_id: str
    condition_builder_version: str
    condition_builder_sha256: str
    mask_id: str | None
    mask_version: str | None
    mask_sha256: str | None
    available_evidence_ids: tuple[str, ...]
    available_evidence_roles: tuple[str, ...]
    removed_json_pointers: tuple[str, ...]
    visibility: str = "robot_visible"
    evaluator_only_absent: bool = True


@dataclass(frozen=True)
class RequirementEvaluation:
    requirement_id: str
    status: RequirementStatus
    support_references: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class ClaimEvaluation:
    claim_id: str
    supported: bool
    requirement_evaluations: tuple[RequirementEvaluation, ...]
    support_references: tuple[str, ...] = ()
    contradiction_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class DiagnosticResult:
    schema: str
    episode_id: str
    configuration_id: str
    condition_id: str
    contract_catalog_id: str
    contract_catalog_sha256: str
    diagnostic_algorithm_id: str
    diagnostic_algorithm_version: str
    state: DiagnosticState
    maximal_node_ids: tuple[str, ...]
    approved_claim_ids: tuple[str, ...]
    claim_evaluations: tuple[ClaimEvaluation, ...]
    missing_requirement_ids: tuple[str, ...]
    contradicted_claim_ids: tuple[str, ...]
    ambiguity_node_ids: tuple[str, ...]
    required_non_entailment_ids: tuple[str, ...]


@dataclass(frozen=True)
class ClauseAudit:
    clause_id: str
    response_span: str
    approved_claim_ids: tuple[str, ...]
    support_references: tuple[str, ...]
    numeric_slots: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApprovedNumericValue:
    claim_id: str
    slot_id: str
    value: int | float
    unit: str
    support_reference: str


@dataclass(frozen=True)
class ExplanationAudit:
    schema: str
    response_id: str
    episode_id: str
    condition_id: str
    diagnostic_result_sha256: str
    status: AuditStatus
    clause_audits: tuple[ClauseAudit, ...]
    represented_required_claim_ids: tuple[str, ...]
    missing_required_claim_ids: tuple[str, ...]
    unapproved_claim_ids: tuple[str, ...]
    numeric_mismatches: tuple[str, ...]
    missing_limitation_ids: tuple[str, ...]
    highest_asserted_node_ids: tuple[str, ...]
    highest_asserted_rank_by_family: tuple[Parameter, ...]
    false_premise_preserved: bool | None
    final_response_sha256: str


def _unique(values: tuple[str, ...], field: str, allow_empty: bool = True) -> None:
    if not allow_empty and not values:
        raise ValueError(f"{field} must not be empty")
    if len(values) != len(set(values)):
        raise ValueError(f"{field} contains duplicates")
    if any(not value or value.strip() != value for value in values):
        raise ValueError(f"{field} contains an invalid identifier")


def _sha256(value: str, field: str) -> None:
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field} is not a lowercase SHA-256 digest")


def evidence_ids_by_role(method_packet: dict[str, Any]) -> dict[str, set[str]]:
    """Return evidence provenance without flattening away top-level role boundaries."""
    evidence = method_packet.get("evidence")
    if not isinstance(evidence, dict):
        raise ValueError("method packet lacks an evidence object")

    def collect(value: Any) -> set[str]:
        found: set[str] = set()
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "evidence_id" and isinstance(child, str) and child:
                    found.add(child)
                elif key == "evidence_ids" and isinstance(child, list):
                    if any(not isinstance(item, str) or not item for item in child):
                        raise ValueError("evidence_ids must contain nonempty strings")
                    found.update(child)
                else:
                    found.update(collect(child))
        elif isinstance(value, list):
            for child in value:
                found.update(collect(child))
        return found

    return {role: collect(value) for role, value in evidence.items()}


def validate_requirement_references(requirement: EvidenceRequirement, status: RequirementStatus,
                                    references: tuple[str, ...] | list[str],
                                    role_ids: dict[str, set[str]]) -> None:
    refs = set(references)
    available = set().union(*role_ids.values()) if role_ids else set()
    if not refs.issubset(available):
        raise ValueError("requirement references evidence unavailable to the method")
    if status in {RequirementStatus.SATISFIED, RequirementStatus.CONTRADICTED}:
        if not refs:
            raise ValueError("decisive requirement status needs visible evidence")
        for role in requirement.evidence_roles:
            if role not in role_ids or not refs.intersection(role_ids[role]):
                raise ValueError("decisive requirement status lacks evidence from a required role")


def validate_ontology(value: EvidenceCalibrationOntology) -> None:
    if value.schema != ONTOLOGY_SCHEMA:
        raise ValueError("unsupported ontology schema")
    req_ids = tuple(item.requirement_id for item in value.evidence_requirements)
    claim_ids = tuple(item.claim_id for item in value.claim_contracts)
    relation_ids = tuple(item.non_entailment_id for item in value.non_entailments)
    node_ids = tuple(item.node_id for item in value.diagnostic_nodes)
    for ids, label in ((req_ids, "requirement IDs"), (claim_ids, "claim IDs"),
                       (relation_ids, "non-entailment IDs"), (node_ids, "node IDs")):
        _unique(ids, label, allow_empty=False)
    requirements, claims = set(req_ids), {item.claim_id: item for item in value.claim_contracts}
    relations, nodes = set(relation_ids), {item.node_id: item for item in value.diagnostic_nodes}
    for item in value.evidence_requirements:
        _unique(item.evidence_roles, f"{item.requirement_id} roles", allow_empty=False)
        if any(role.startswith("evaluator_") for role in item.evidence_roles):
            raise ValueError("public requirements cannot use evaluator-only roles")
        if not item.predicate_id or not item.predicate_version:
            raise ValueError("requirements need registered predicate identities")
    for item in value.claim_contracts:
        if item.diagnostic_node_id not in nodes:
            raise ValueError("claim references an unknown diagnostic node")
        for ids, known, label, required in (
            (item.required_evidence_ids, requirements, "required evidence", True),
            (item.optional_evidence_ids, requirements, "optional evidence", False),
            (item.non_entailment_ids, relations, "non-entailments", False),
        ):
            _unique(ids, f"{item.claim_id} {label}", allow_empty=not required)
            if not set(ids).issubset(known):
                raise ValueError(f"claim has dangling {label}")
    for item in value.non_entailments:
        for ids, known, label, required in (
            (item.basis_claim_ids, set(claim_ids), "basis claims", True),
            (item.unsupported_consequent_claim_ids, set(claim_ids), "consequents", True),
            (item.additional_evidence_requirement_ids, requirements, "additional requirements", False),
        ):
            _unique(ids, f"{item.non_entailment_id} {label}", allow_empty=not required)
            if not set(ids).issubset(known):
                raise ValueError(f"non-entailment has dangling {label}")
    for item in value.diagnostic_nodes:
        if item.rank_within_family < 0:
            raise ValueError("node rank must be non-negative")
        for ids, known, label, required in (
            (item.parent_node_ids, set(node_ids), "parents", False),
            (item.claim_ids, set(claim_ids), "claims", True),
            (item.required_evidence_ids, requirements, "requirements", False),
            (item.contradiction_claim_ids, set(claim_ids), "contradictions", False),
        ):
            _unique(ids, f"{item.node_id} {label}", allow_empty=not required)
            if not set(ids).issubset(known):
                raise ValueError(f"node has dangling {label}")
        if item.node_id in item.parent_node_ids:
            raise ValueError("node cannot be its own parent")
        for parent_id in item.parent_node_ids:
            parent = nodes[parent_id]
            if parent.mechanism_family != item.mechanism_family:
                raise ValueError("v1 does not permit cross-family ancestry")
            if parent.rank_within_family >= item.rank_within_family:
                raise ValueError("child rank must exceed parent rank")
        for claim_id in item.claim_ids:
            if claims[claim_id].diagnostic_node_id != item.node_id:
                raise ValueError("claim and node disagree")
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node_id: str) -> None:
        if node_id in visiting:
            raise ValueError("diagnostic hierarchy contains a cycle")
        if node_id in visited:
            return
        visiting.add(node_id)
        for parent_id in nodes[node_id].parent_node_ids:
            visit(parent_id)
        visiting.remove(node_id)
        visited.add(node_id)
    for node_id in nodes:
        visit(node_id)


def validate_evidence_condition(value: EvidenceCondition) -> None:
    if value.schema != CONDITION_SCHEMA:
        raise ValueError("unsupported evidence-condition schema")
    if value.visibility != "robot_visible" or not value.evaluator_only_absent:
        raise ValueError("evaluator truth must be absent")
    if value.level_index < 0 or ((value.level_index == 0) != (value.parent_condition_id is None)):
        raise ValueError("invalid evidence-ladder level/parent")
    masks = (value.mask_id, value.mask_version, value.mask_sha256)
    mask_absent = all(item is None for item in masks)
    mask_complete = all(item is not None for item in masks)
    if not (mask_absent or mask_complete):
        raise ValueError("mask identity must be wholly present or absent")
    if mask_absent and value.removed_json_pointers:
        raise ValueError("a condition that removes evidence requires a mask identity")
    if mask_complete and not value.removed_json_pointers:
        raise ValueError("an unmasked condition must not declare a mask identity")
    for field in ("source_packet_sha256", "method_packet_sha256", "source_configuration_sha256",
                  "runtime_manifest_sha256", "condition_builder_sha256"):
        _sha256(getattr(value, field), field)
    if value.mask_sha256 is not None:
        _sha256(value.mask_sha256, "mask_sha256")
    _unique(value.available_evidence_ids, "available evidence IDs")
    _unique(value.available_evidence_roles, "available evidence roles")
    _unique(value.removed_json_pointers, "removed JSON pointers")
    if any(not item.startswith("/") for item in value.removed_json_pointers):
        raise ValueError("removed evidence needs absolute JSON pointers")


def _ancestor(ancestor: str, node: str, nodes: dict[str, DiagnosticNode]) -> bool:
    pending, seen = list(nodes[node].parent_node_ids), set()
    while pending:
        current = pending.pop()
        if current == ancestor:
            return True
        if current not in seen:
            seen.add(current)
            pending.extend(nodes[current].parent_node_ids)
    return False


def validate_diagnostic_result(result: DiagnosticResult, ontology: EvidenceCalibrationOntology) -> None:
    validate_ontology(ontology)
    if result.schema != RESULT_SCHEMA or result.contract_catalog_id != ontology.catalog_id:
        raise ValueError("result schema/catalog mismatch")
    claims = {item.claim_id: item for item in ontology.claim_contracts}
    nodes = {item.node_id: item for item in ontology.diagnostic_nodes}
    evaluations = {item.claim_id: item for item in result.claim_evaluations}
    _unique(tuple(item.claim_id for item in result.claim_evaluations), "claim evaluation IDs")
    for evaluation in result.claim_evaluations:
        contract = claims.get(evaluation.claim_id)
        if contract is None:
            raise ValueError("evaluation references an unknown claim")
        statuses = {item.requirement_id: item.status for item in evaluation.requirement_evaluations}
        required = set(contract.required_evidence_ids)
        if not required.issubset(statuses):
            raise ValueError("evaluation omits a required requirement")
        supported = all(statuses[item] is RequirementStatus.SATISFIED for item in required)
        if evaluation.supported is not supported:
            raise ValueError("claim support must be derived from requirement statuses")
    for ids, known, label in (
        (result.maximal_node_ids, set(nodes), "maximal nodes"),
        (result.ambiguity_node_ids, set(nodes), "ambiguity nodes"),
        (result.approved_claim_ids, set(claims), "approved claims"),
        (result.contradicted_claim_ids, set(claims), "contradicted claims"),
        (result.required_non_entailment_ids, {item.non_entailment_id for item in ontology.non_entailments}, "non-entailments"),
    ):
        _unique(ids, label)
        if not set(ids).issubset(known):
            raise ValueError(f"result has dangling {label}")
    if any(item not in evaluations or not evaluations[item].supported for item in result.approved_claim_ids):
        raise ValueError("approved claims require supported evaluations")
    if result.state is DiagnosticState.AMBIGUOUS:
        if len(result.ambiguity_node_ids) < 2:
            raise ValueError("AMBIGUOUS needs two alternatives")
        if any(left != right and _ancestor(left, right, nodes)
               for left in result.ambiguity_node_ids for right in result.ambiguity_node_ids):
            raise ValueError("ambiguity nodes must be incomparable")
    elif result.ambiguity_node_ids:
        raise ValueError("non-AMBIGUOUS result has ambiguity nodes")
    if result.state is DiagnosticState.FALSE_PREMISE:
        failure_kinds = {ClaimKind.EXECUTION_DISCREPANCY, ClaimKind.PHYSICAL_MECHANISM,
                         ClaimKind.SPECIFIC_PHYSICAL_CAUSE}
        if any(claims[item].claim_kind in failure_kinds for item in result.approved_claim_ids):
            raise ValueError("FALSE_PREMISE cannot approve a failure mechanism")


def validate_explanation_audit(audit: ExplanationAudit, result: DiagnosticResult,
                               ontology: EvidenceCalibrationOntology) -> None:
    if audit.schema != AUDIT_SCHEMA or audit.episode_id != result.episode_id \
            or audit.condition_id != result.condition_id:
        raise ValueError("audit schema/identity mismatch")
    approved = set(result.approved_claim_ids)
    if any(not set(clause.approved_claim_ids).issubset(approved) for clause in audit.clause_audits):
        raise ValueError("clause maps to an unapproved claim")
    represented = set(audit.represented_required_claim_ids)
    if not represented.issubset(approved) or represented & set(audit.missing_required_claim_ids):
        raise ValueError("inconsistent represented/missing claims")
    if set(audit.unapproved_claim_ids) & approved:
        raise ValueError("approved claim marked unapproved")
    node_ids = {item.node_id for item in ontology.diagnostic_nodes}
    if not set(audit.highest_asserted_node_ids).issubset(node_ids):
        raise ValueError("unknown highest asserted node")
    failures = (audit.missing_required_claim_ids, audit.unapproved_claim_ids,
                audit.numeric_mismatches, audit.missing_limitation_ids)
    if audit.status is AuditStatus.ACCEPTED and any(failures):
        raise ValueError("accepted audit retains verification failures")
