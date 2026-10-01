#!/usr/bin/env python3
"""Constrained claim-ID realization with local, deterministic repair.

This is a development implementation for B4.  It never infers propositions from free text:
candidate clauses identify a registered claim or non-entailment and use a closed template.
Invalid clauses are removed, while missing required content is reconstructed independently.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from evidence_calibration import (
    AUDIT_SCHEMA,
    AuditStatus,
    ClauseAudit,
    DiagnosticState,
    ExplanationAudit,
    Parameter,
)
from evidence_calibration_io import canonical_json_bytes, canonical_sha256, ontology_from_dict


PLAN_SCHEMA = "crane-claim-realization-plan/v1"
CANDIDATE_SCHEMA = "crane-claim-realization-candidate/v1"
OUTPUT_SCHEMA = "crane-claim-aware-realization/v1"
REALIZER_ID = "claim-aware-constrained-realizer"
REALIZER_VERSION = "v1-development"


def _closed(value: dict[str, Any], required: set[str], optional: set[str], label: str) -> None:
    missing, unknown = required - set(value), set(value) - required - optional
    if missing:
        raise ValueError(f"{label} is missing fields: {sorted(missing)}")
    if unknown:
        raise ValueError(f"{label} has unknown fields: {sorted(unknown)}")


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)) or any(not item for item in values):
        raise ValueError(f"{label} must contain unique nonempty identifiers")


def _format_number(value: int | float) -> str:
    if isinstance(value, bool):
        raise ValueError("numeric slot cannot contain a Boolean")
    return str(value) if isinstance(value, int) else format(value, ".12g")


def _claim_text(contract: Any, values: list[dict[str, Any]]) -> str:
    text = contract.proposition.rstrip()
    if values:
        rendered = "; ".join(
            f"{item['slot_id'].replace('_', ' ')}: {_format_number(item['value'])} {item['unit']}"
            for item in sorted(values, key=lambda row: row["slot_id"])
        )
        text = f"{text.rstrip('.')} ({rendered})."
    elif not text.endswith((".", "!", "?")):
        text += "."
    return text


def _limitation_text(relation: Any) -> str:
    text = relation.rationale.strip()
    return text if text.endswith((".", "!", "?")) else text + "."


def _validate_plan(plan: dict[str, Any], result: dict[str, Any], ontology: Any) -> None:
    _closed(plan, {"schema", "plan_id", "diagnostic_result_sha256", "required_claim_ids",
                   "optional_claim_ids", "required_non_entailment_ids", "approved_numeric_values"},
            set(), "realization plan")
    if plan["schema"] != PLAN_SCHEMA or plan["diagnostic_result_sha256"] != canonical_sha256(result):
        raise ValueError("realization plan is not bound to the diagnostic result")
    approved = set(result["approved_claim_ids"])
    required, optional = plan["required_claim_ids"], plan["optional_claim_ids"]
    _unique(required, "required claim IDs")
    _unique(optional, "optional claim IDs")
    if set(required) & set(optional) or not set(required + optional).issubset(approved):
        raise ValueError("plan claims must be disjoint subsets of approved claims")
    registered_relations = {item.non_entailment_id for item in ontology.non_entailments}
    required_relations = plan["required_non_entailment_ids"]
    _unique(required_relations, "required non-entailment IDs")
    if set(required_relations) != set(result["required_non_entailment_ids"]):
        raise ValueError("plan must preserve every diagnostic-result non-entailment")
    claims = {item.claim_id: item for item in ontology.claim_contracts}
    if not set(required_relations).issubset(registered_relations):
        raise ValueError("plan references an unknown non-entailment")
    if result["state"] == DiagnosticState.FALSE_PREMISE.value and \
            "claim-false-premise-success" not in required:
        raise ValueError("false-premise result must require the rejection claim")
    evaluations = {item["claim_id"]: item for item in result["claim_evaluations"]}
    seen_slots: set[tuple[str, str]] = set()
    for item in plan["approved_numeric_values"]:
        _closed(item, {"claim_id", "slot_id", "value", "unit", "support_reference"}, set(),
                "approved numeric value")
        key = item["claim_id"], item["slot_id"]
        if key in seen_slots or item["claim_id"] not in approved:
            raise ValueError("numeric value is duplicated or attached to an unapproved claim")
        seen_slots.add(key)
        slots = {slot.slot_id: slot for slot in claims[item["claim_id"]].numeric_slots}
        if item["slot_id"] not in slots or item["unit"] != slots[item["slot_id"]].unit:
            raise ValueError("numeric value does not match a registered slot")
        if not isinstance(item["value"], (int, float)) or isinstance(item["value"], bool):
            raise ValueError("numeric slot needs a finite numeric value")
        if item["value"] != item["value"] or abs(item["value"]) == float("inf"):
            raise ValueError("numeric slot needs a finite numeric value")
        if item["support_reference"] not in evaluations[item["claim_id"]]["support_references"]:
            raise ValueError("numeric value lacks claim-level visible support")
    expected_slots = {
        (identifier, slot.slot_id)
        for identifier in required + optional for slot in claims[identifier].numeric_slots
    }
    if seen_slots != expected_slots:
        raise ValueError("plan must bind every numeric slot for every selected claim")


def realize(ontology_dict: dict[str, Any], result: dict[str, Any], plan: dict[str, Any],
            candidate: dict[str, Any]) -> dict[str, Any]:
    ontology = ontology_from_dict(ontology_dict)
    _validate_plan(plan, result, ontology)
    _closed(candidate, {"schema", "response_id", "plan_sha256", "clauses"}, set(),
            "realization candidate")
    if candidate["schema"] != CANDIDATE_SCHEMA or candidate["plan_sha256"] != canonical_sha256(plan):
        raise ValueError("candidate is not bound to the realization plan")
    claims = {item.claim_id: item for item in ontology.claim_contracts}
    relations = {item.non_entailment_id: item for item in ontology.non_entailments}
    approved = set(result["approved_claim_ids"])
    required = set(plan["required_claim_ids"])
    required_relations = set(plan["required_non_entailment_ids"])
    approved_values = {
        (item["claim_id"], item["slot_id"]): item for item in plan["approved_numeric_values"]
    }
    clause_ids: set[str] = set()
    accepted: list[dict[str, Any]] = []
    represented_claims: set[str] = set()
    represented_relations: set[str] = set()
    unapproved: set[str] = set()
    mismatches: set[str] = set()
    repaired = False

    for clause in candidate["clauses"]:
        _closed(clause, {"clause_id", "kind", "contract_id", "numeric_values"}, set(),
                "candidate clause")
        clause_id = clause["clause_id"]
        if not clause_id or clause_id in clause_ids:
            raise ValueError("candidate clause IDs must be unique and nonempty")
        clause_ids.add(clause_id)
        kind, identifier = clause["kind"], clause["contract_id"]
        values = clause["numeric_values"]
        if kind == "CLAIM":
            if identifier not in approved:
                unapproved.add(identifier)
                repaired = True
                continue
            expected = {key[1]: value for key, value in approved_values.items() if key[0] == identifier}
            supplied: dict[str, dict[str, Any]] = {}
            valid = True
            for value in values:
                _closed(value, {"slot_id", "value", "unit"}, set(), "candidate numeric value")
                slot_id = value["slot_id"]
                if slot_id in supplied or slot_id not in expected:
                    mismatches.add(f"{identifier}:{slot_id}")
                    valid = False
                else:
                    supplied[slot_id] = value
            if set(supplied) != set(expected):
                mismatches.update(f"{identifier}:{slot}" for slot in set(supplied) ^ set(expected))
                valid = False
            for slot_id in set(supplied) & set(expected):
                slot = next(item for item in claims[identifier].numeric_slots if item.slot_id == slot_id)
                tolerance = 0.0 if slot.tolerance is None else slot.tolerance
                if supplied[slot_id]["unit"] != expected[slot_id]["unit"] or \
                        not isinstance(supplied[slot_id]["value"], (int, float)) or \
                        isinstance(supplied[slot_id]["value"], bool) or \
                        abs(supplied[slot_id]["value"] - expected[slot_id]["value"]) > tolerance:
                    mismatches.add(f"{identifier}:{slot_id}")
                    valid = False
            if not valid:
                repaired = True
                continue
            accepted.append({"clause_id": clause_id, "kind": kind, "contract_id": identifier,
                             "text": _claim_text(claims[identifier], list(expected.values())),
                             "numeric_slot_ids": sorted(expected)})
            represented_claims.add(identifier)
        elif kind == "NON_ENTAILMENT":
            if identifier not in required_relations or values:
                unapproved.add(identifier)
                repaired = True
                continue
            accepted.append({"clause_id": clause_id, "kind": kind, "contract_id": identifier,
                             "text": _limitation_text(relations[identifier]),
                             "numeric_slot_ids": []})
            represented_relations.add(identifier)
        else:
            raise ValueError("candidate clause kind is not registered")

    missing_claims = required - represented_claims
    missing_relations = required_relations - represented_relations
    for identifier in sorted(missing_claims):
        values = [value for key, value in approved_values.items() if key[0] == identifier]
        accepted.append({"clause_id": f"repair-claim-{identifier}", "kind": "CLAIM",
                         "contract_id": identifier, "text": _claim_text(claims[identifier], values),
                         "numeric_slot_ids": sorted(item["slot_id"] for item in values)})
        represented_claims.add(identifier)
        repaired = True
    for identifier in sorted(missing_relations):
        accepted.append({"clause_id": f"repair-limit-{identifier}", "kind": "NON_ENTAILMENT",
                         "contract_id": identifier, "text": _limitation_text(relations[identifier]),
                         "numeric_slot_ids": []})
        represented_relations.add(identifier)
        repaired = True

    final_text = " ".join(item["text"] for item in accepted)
    if not final_text:
        raise ValueError("a claim-aware response cannot be empty")
    false_premise_required = result["state"] == DiagnosticState.FALSE_PREMISE.value
    false_premise_preserved = None if not false_premise_required else \
        "claim-false-premise-success" in represented_claims
    status = AuditStatus.REPAIRED if repaired else AuditStatus.ACCEPTED
    clause_audits = tuple(ClauseAudit(
        clause_id=item["clause_id"], response_span=item["text"],
        approved_claim_ids=(item["contract_id"],) if item["kind"] == "CLAIM" else (),
        support_references=tuple(
            next(row for row in result["claim_evaluations"]
                 if row["claim_id"] == item["contract_id"])["support_references"]
        ) if item["kind"] == "CLAIM" else (),
        numeric_slots=tuple(item["numeric_slot_ids"]),
    ) for item in accepted)
    nodes = {item.node_id: item for item in ontology.diagnostic_nodes}
    asserted_nodes = {claims[item].diagnostic_node_id for item in represented_claims}
    highest = tuple(sorted(node for node in asserted_nodes if not any(
        node != other and node in _ancestors(other, nodes) for other in asserted_nodes
    )))
    ranks = tuple(Parameter(family, max(nodes[node].rank_within_family for node in asserted_nodes
                                        if nodes[node].mechanism_family == family))
                  for family in sorted({nodes[node].mechanism_family for node in asserted_nodes}))
    audit = ExplanationAudit(
        schema=AUDIT_SCHEMA, response_id=candidate["response_id"], episode_id=result["episode_id"],
        condition_id=result["condition_id"], diagnostic_result_sha256=canonical_sha256(result),
        status=status, clause_audits=clause_audits,
        represented_required_claim_ids=tuple(sorted(required & represented_claims)),
        missing_required_claim_ids=(), unapproved_claim_ids=tuple(sorted(unapproved)),
        numeric_mismatches=tuple(sorted(mismatches)), missing_limitation_ids=(),
        highest_asserted_node_ids=highest, highest_asserted_rank_by_family=ranks,
        false_premise_preserved=false_premise_preserved,
        final_response_sha256=canonical_sha256(final_text),
    )
    return {"schema": OUTPUT_SCHEMA, "realizer_id": REALIZER_ID,
            "realizer_version": REALIZER_VERSION, "plan_sha256": canonical_sha256(plan),
            "candidate_sha256": canonical_sha256(candidate), "final_response": final_text,
            "final_clauses": accepted, "audit": asdict(audit)}


def _ancestors(node_id: str, nodes: dict[str, Any]) -> set[str]:
    result, pending = set(), list(nodes[node_id].parent_node_ids)
    while pending:
        current = pending.pop()
        if current not in result:
            result.add(current)
            pending.extend(nodes[current].parent_node_ids)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    for name in ("ontology", "result", "plan", "candidate", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    output = realize(*(json.loads(getattr(args, name).read_text(encoding="utf-8"))
                       for name in ("ontology", "result", "plan", "candidate")))
    args.output.write_bytes(canonical_json_bytes(output) + b"\n")


if __name__ == "__main__":
    main()
