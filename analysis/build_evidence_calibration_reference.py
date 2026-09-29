#!/usr/bin/env python3
"""Build evaluator-only maximum-defensible-diagnosis references.

Visible-evidence support is derived exclusively from requirement evaluations tied to IDs present
in each method packet. Physical truth is joined only after support is computed and is never copied
into a method-visible artifact.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evidence_calibration import (
    ClaimKind, DiagnosticState, RequirementStatus, evidence_ids_by_role,
    validate_requirement_references,
)
from evidence_calibration_io import canonical_json_bytes, canonical_sha256, ontology_from_dict


INPUT_SCHEMA = "crane-evidence-calibration-reference-input/v1"
OUTPUT_SCHEMA = "crane-evidence-calibration-reference/v1"
SUPPORT_LABELS = {
    "supported": "SUPPORTED_BY_VISIBLE_EVIDENCE",
    "contradicted": "CONTRADICTED_BY_VISIBLE_EVIDENCE",
    "insufficient": "INSUFFICIENT_VISIBLE_EVIDENCE",
    "true_unsupported": "PHYSICALLY_TRUE_BUT_UNSUPPORTED",
}


def _validate_closed(value: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    if set(value) - required - optional or required - set(value):
        raise ValueError(f"{label} has missing or unknown fields")


def _condition_records(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if bundle.get("schema") != "crane-nested-evidence-condition-bundle/v1":
        raise ValueError("unsupported condition bundle")
    records: dict[str, dict[str, Any]] = {}
    for entry in bundle.get("conditions", []):
        condition, packet = entry.get("condition"), entry.get("method_packet")
        if not isinstance(condition, dict) or not isinstance(packet, dict):
            raise ValueError("condition bundle entry is incomplete")
        condition_id = condition.get("condition_id")
        if not isinstance(condition_id, str) or not condition_id or condition_id in records:
            raise ValueError("condition IDs are missing or duplicated")
        if condition.get("method_packet_sha256") != canonical_sha256(packet):
            raise ValueError("condition method-packet hash does not match")
        records[condition_id] = entry
    if not records:
        raise ValueError("condition bundle is empty")
    return records


def _ancestors_supported(node_id: str, supported_nodes: set[str], nodes: dict[str, Any]) -> bool:
    pending = list(nodes[node_id].parent_node_ids)
    while pending:
        current = pending.pop()
        if current not in supported_nodes:
            return False
        pending.extend(nodes[current].parent_node_ids)
    return True


def _maximal_nodes(supported_nodes: set[str], nodes: dict[str, Any]) -> list[str]:
    parents = {parent for node_id in supported_nodes for parent in nodes[node_id].parent_node_ids}
    return sorted(supported_nodes - parents)


def build_reference(ontology_dict: dict[str, Any], bundle: dict[str, Any],
                    reference_input: dict[str, Any]) -> dict[str, Any]:
    ontology = ontology_from_dict(ontology_dict)
    conditions = _condition_records(bundle)
    _validate_closed(
        reference_input,
        {"schema", "reference_id", "physical_truth", "condition_assessments",
         "reference_builder_id", "reference_builder_version", "reference_builder_sha256"},
        set(), "reference input",
    )
    if reference_input["schema"] != INPUT_SCHEMA:
        raise ValueError("unsupported reference-input schema")
    truth = reference_input["physical_truth"]
    _validate_closed(truth, {"physical_true_claim_ids", "physical_false_claim_ids",
                             "truth_assertions", "truth_source_references"}, set(), "physical truth")
    claims = {item.claim_id: item for item in ontology.claim_contracts}
    nodes = {item.node_id: item for item in ontology.diagnostic_nodes}
    requirements_by_id = {item.requirement_id: item for item in ontology.evidence_requirements}
    requirements = set(requirements_by_id)
    true_claims, false_claims = set(truth["physical_true_claim_ids"]), set(truth["physical_false_claim_ids"])
    if true_claims & false_claims or not (true_claims | false_claims).issubset(claims):
        raise ValueError("physical-truth claim sets overlap or reference unknown claims")
    if not isinstance(truth["truth_assertions"], list) or not truth["truth_assertions"]:
        raise ValueError("physical truth needs at least one explicit truth assertion")
    truth_ids = []
    for assertion in truth["truth_assertions"]:
        _validate_closed(assertion, {"truth_id", "description"}, set(), "truth assertion")
        if not isinstance(assertion["truth_id"], str) or not assertion["truth_id"]:
            raise ValueError("truth assertions need identifiers")
        if not isinstance(assertion["description"], str) or not assertion["description"]:
            raise ValueError("truth assertions need descriptions")
        truth_ids.append(assertion["truth_id"])
    if len(truth_ids) != len(set(truth_ids)):
        raise ValueError("truth assertion IDs are duplicated")
    if (not isinstance(truth["truth_source_references"], list)
            or not truth["truth_source_references"]
            or len(truth["truth_source_references"]) != len(set(truth["truth_source_references"]))):
        raise ValueError("physical truth needs unique source references")
    assessments = reference_input["condition_assessments"]
    if not isinstance(assessments, list) or len(assessments) != len(conditions):
        raise ValueError("every evidence condition needs one evaluator assessment")
    assessment_ids = [item.get("condition_id") for item in assessments]
    if len(assessment_ids) != len(set(assessment_ids)) or set(assessment_ids) != set(conditions):
        raise ValueError("condition assessments do not match the condition bundle")

    outputs = []
    for assessment in sorted(assessments, key=lambda item: conditions[item["condition_id"]]["condition"]["level_index"]):
        _validate_closed(assessment, {"condition_id", "requirement_evaluations",
                                     "optional_supported_claim_ids", "ambiguity_claim_ids",
                                     "independent_computation_references"}, set(), "condition assessment")
        condition = conditions[assessment["condition_id"]]["condition"]
        method_packet = conditions[assessment["condition_id"]]["method_packet"]
        available_ids = set(condition["available_evidence_ids"])
        role_ids = evidence_ids_by_role(method_packet)
        requirement_values: dict[str, dict[str, Any]] = {}
        for item in assessment["requirement_evaluations"]:
            _validate_closed(item, {"requirement_id", "status", "support_references", "detail"}, set(),
                             "requirement evaluation")
            requirement_id = item["requirement_id"]
            if requirement_id not in requirements or requirement_id in requirement_values:
                raise ValueError("requirement evaluation is unknown or duplicated")
            status = RequirementStatus(item["status"])
            references = item["support_references"]
            if len(references) != len(set(references)) or not set(references).issubset(available_ids):
                raise ValueError("requirement support references are not visible in this condition")
            validate_requirement_references(
                requirements_by_id[requirement_id], status, references, role_ids
            )
            requirement_values[requirement_id] = {**item, "status": status}
        if set(requirement_values) != requirements:
            raise ValueError("reference must evaluate every registered requirement")

        claim_rows = []
        supported_claims: set[str] = set()
        contradicted_claims: set[str] = set()
        for claim in ontology.claim_contracts:
            rows = [requirement_values[item] for item in claim.required_evidence_ids]
            supported = all(item["status"] is RequirementStatus.SATISFIED for item in rows)
            contradicted = any(item["status"] is RequirementStatus.CONTRADICTED for item in rows)
            if supported:
                label = SUPPORT_LABELS["supported"]
                supported_claims.add(claim.claim_id)
            elif contradicted:
                label = SUPPORT_LABELS["contradicted"]
                contradicted_claims.add(claim.claim_id)
            elif claim.claim_id in true_claims:
                label = SUPPORT_LABELS["true_unsupported"]
            else:
                label = SUPPORT_LABELS["insufficient"]
            claim_rows.append({
                "claim_id": claim.claim_id,
                "support_label": label,
                "physically_true": claim.claim_id in true_claims,
                "physically_false": claim.claim_id in false_claims,
                "required_evidence_ids": list(claim.required_evidence_ids),
                "missing_requirement_ids": sorted(item["requirement_id"] for item in rows if item["status"] is RequirementStatus.ABSENT),
                "invalid_requirement_ids": sorted(item["requirement_id"] for item in rows if item["status"] is RequirementStatus.INVALID),
                "contradicted_requirement_ids": sorted(item["requirement_id"] for item in rows if item["status"] is RequirementStatus.CONTRADICTED),
                "support_references": sorted({reference for item in rows for reference in item["support_references"]}),
            })

        supported_nodes = {
            node.node_id for node in ontology.diagnostic_nodes
            if set(node.claim_ids).issubset(supported_claims)
        }
        supported_nodes = {node_id for node_id in supported_nodes if _ancestors_supported(node_id, supported_nodes, nodes)}
        maximal = _maximal_nodes(supported_nodes, nodes)
        ambiguity_claims = set(assessment["ambiguity_claim_ids"])
        if len(assessment["ambiguity_claim_ids"]) != len(ambiguity_claims):
            raise ValueError("ambiguity claim IDs are duplicated")
        if not ambiguity_claims.issubset(claims) or ambiguity_claims & supported_claims or ambiguity_claims & contradicted_claims:
            raise ValueError("ambiguity claims must be known and neither supported nor contradicted")
        families: dict[str, list[str]] = {}
        for node_id in maximal:
            families.setdefault(nodes[node_id].mechanism_family, []).append(node_id)
        inferred_ambiguity = any(len(values) > 1 for values in families.values()) or bool(ambiguity_claims)
        false_premise = "claim-false-premise-success" in supported_claims
        physically_true_but_unsupported = sorted(
            item for item in true_claims if item not in supported_claims and item not in contradicted_claims
        )
        deeper_truth_withheld = any(
            claims[item].claim_kind in {ClaimKind.PHYSICAL_MECHANISM, ClaimKind.SPECIFIC_PHYSICAL_CAUSE,
                                        ClaimKind.EXECUTION_DISCREPANCY, ClaimKind.RECOVERY_MECHANISM}
            for item in physically_true_but_unsupported
        )
        if false_premise:
            state = DiagnosticState.FALSE_PREMISE
        elif inferred_ambiguity:
            state = DiagnosticState.AMBIGUOUS
        elif not maximal:
            state = DiagnosticState.INSUFFICIENT_EVIDENCE
        elif deeper_truth_withheld:
            state = DiagnosticState.SUPPORTED_PARTIAL
        else:
            state = DiagnosticState.KNOWN

        optional = set(assessment["optional_supported_claim_ids"])
        if len(assessment["optional_supported_claim_ids"]) != len(optional):
            raise ValueError("optional supported claim IDs are duplicated")
        if not optional.issubset(supported_claims):
            raise ValueError("optional supported claims must actually be supported")
        required_supported = supported_claims - optional
        computation_references = assessment["independent_computation_references"]
        if (not isinstance(computation_references, list) or not computation_references
                or len(computation_references) != len(set(computation_references))
                or any(not isinstance(item, str) or not item for item in computation_references)):
            raise ValueError("independent computation references must be unique identifiers")
        outputs.append({
            "condition_id": assessment["condition_id"],
            "level_index": condition["level_index"],
            "method_packet_sha256": condition["method_packet_sha256"],
            "reference_state": state.value,
            "highest_defensible_node_ids": maximal,
            "supported_required_claim_ids": sorted(required_supported),
            "optional_supported_claim_ids": sorted(optional),
            "explicitly_unsupported_claim_ids": sorted(set(claims) - supported_claims - contradicted_claims),
            "contradicted_claim_ids": sorted(contradicted_claims),
            "ambiguous_claim_ids": sorted(ambiguity_claims),
            "physically_true_but_unsupported_claim_ids": physically_true_but_unsupported,
            "false_premise": false_premise,
            "decisive_evidence_ids": sorted({reference for item in claim_rows if item["claim_id"] in supported_claims for reference in item["support_references"]}),
            "missing_decisive_requirement_ids": sorted({identifier for item in claim_rows for identifier in item["missing_requirement_ids"]}),
            "independent_computation_references": sorted(computation_references),
            "claim_evaluations": claim_rows,
        })

    return {
        "schema": OUTPUT_SCHEMA,
        "reference_id": reference_input["reference_id"],
        "episode_id": next(iter(conditions.values()))["condition"]["episode_id"],
        "configuration_id": next(iter(conditions.values()))["condition"]["configuration_id"],
        "contract_catalog_id": ontology.catalog_id,
        "contract_catalog_sha256": canonical_sha256(ontology),
        "condition_bundle_sha256": canonical_sha256(bundle),
        "reference_builder_id": reference_input["reference_builder_id"],
        "reference_builder_version": reference_input["reference_builder_version"],
        "reference_builder_sha256": reference_input["reference_builder_sha256"],
        "physical_truth": truth,
        "conditions": outputs,
        "method_visible": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ontology", type=Path, required=True)
    parser.add_argument("--condition-bundle", type=Path, required=True)
    parser.add_argument("--reference-input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_reference(
        json.loads(args.ontology.read_text(encoding="utf-8")),
        json.loads(args.condition_bundle.read_text(encoding="utf-8")),
        json.loads(args.reference_input.read_text(encoding="utf-8")),
    )
    args.output.write_bytes(canonical_json_bytes(result) + b"\n")


if __name__ == "__main__":
    main()
