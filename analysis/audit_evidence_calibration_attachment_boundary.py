#!/usr/bin/env python3
"""Inventory contract/ladder prerequisites without attaching or scoring pilot claims."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_ontology_v2_wording import audit as audit_wording
from evidence_calibration_io import ontology_from_dict
from validate_evidence_calibration_ladders import validate as validate_ladders

ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = "configs/evidence_calibration_claim_contracts_v2_development.json"
LADDERS = "configs/evidence_calibration_ladders_v1_development.json"
ROLES = "manifests/annotation/evidence-calibration-pilot-role-disposition-v1.json"
OUTPUT = "manifests/annotation/evidence-calibration-attachment-boundary-v1-development.json"


def inventory(ontology: dict, ladders: dict, disposition: dict) -> dict:
    """Public role availability is necessary only; predicate satisfaction is not inferred."""
    ontology_from_dict(ontology)
    if disposition.get("schema") != "crane-pilot-role-disposition/v1-development":
        raise ValueError("unsupported raw-role disposition")
    for key in ("claim_specific_endpoint_attachment_complete", "endpoint_scores_generated",
                "support_labels_generated", "method_key_opened", "pilot_annotation_authorized"):
        if disposition.get(key) is not False:
            raise ValueError("raw-role disposition must preserve the closed attachment boundary")
    rows = disposition["rows"]
    identifiers = [(row["case_id"], row["claim"]["item_id"]) for row in rows]
    if len(rows) != disposition["atom_count"] or len(set(identifiers)) != len(rows):
        raise ValueError("raw-role inventory count or atom identity mismatch")
    if len({row["case_id"] for row in rows}) != disposition["response_count"]:
        raise ValueError("raw-role response count mismatch")
    for row in rows:
        if any(key not in row or row[key] is not None for key in
               ("selected_role", "attached_contract", "asserted_rank", "mechanistic_flag")) \
                or row.get("endpoint_scoring_authorized") is not False:
            raise ValueError("raw roles cannot supply selected contracts, ranks or endpoint flags")

    requirements = {item["requirement_id"]: item for item in ontology["evidence_requirements"]}
    nodes = {item["node_id"]: item for item in ontology["diagnostic_nodes"]}
    claims = []
    for claim in sorted(ontology["claim_contracts"], key=lambda item: item["claim_id"]):
        required_roles = {role for identifier in claim["required_evidence_ids"]
                          for role in requirements[identifier]["evidence_roles"]}
        availability = []
        for ladder in ladders["ladders"]:
            eligible = [level["level_index"] for level in ladder["levels"]
                        if required_roles <= set(level["available_evidence_roles"])]
            availability.append({"ladder_id": ladder["ladder_id"],
                                 "first_role_complete_level": min(eligible) if eligible else None,
                                 "status": "ROLES_ONLY_PREDICATES_UNCHECKED" if eligible
                                           else "REQUIRED_ROLES_ABSENT_AT_ALL_REGISTERED_LEVELS"})
        node = nodes[claim["diagnostic_node_id"]]
        claims.append({"claim_id": claim["claim_id"], "proposition": claim["proposition"],
                       "claim_kind": claim["claim_kind"], "mechanism_family": claim["mechanism_family"],
                       "diagnostic_node_id": node["node_id"],
                       "rank_within_family": node["rank_within_family"],
                       "required_evidence_ids": claim["required_evidence_ids"],
                       "required_roles": sorted(required_roles), "role_availability": availability})
    concerns = Counter(concern for row in rows for concern in row["project_review_concerns"])
    return {"contract_count": len(claims), "contracts": claims,
            "catalog_claim_kind_counts": dict(sorted(Counter(
                item["claim_kind"] for item in claims).items())),
            "rank_scope": "WITHIN_MECHANISM_FAMILY_ONLY_NO_RESPONSE_RANK_MAPPING",
            "raw_role_atom_count": len(rows), "unattached_atom_count": len(rows),
            "carried_project_review_concern_counts": dict(sorted(concerns.items())),
            "required_roles_are_sufficient_for_support": False,
            "no_registered_role_complete_level_means":
                "No eligible level in this catalog; do not encode as zero, invent E4, or silently drop the claim.",
            "attachment_prerequisites": [
                "Resolve exact proposition, endorsement, modality, polarity and referent in full answer/question context.",
                "Keep explicit negative causal assertions distinct from non-establishment limitations.",
                "Keep source/configuration facts distinct from episode events and software recovery distinct from measured recovery.",
                "Bind requirements for unmatched propositions instead of borrowing a nearby positive contract.",
                "Validate family-to-response rank and mechanistic endpoint mappings; raw roles/highest levels are unqualified.",
                "Bind treatment of unresolved scope and UNINTERPRETABLE before episode inference.",
                "Complete authorized support measurement/adjudication before a method-key join or endpoint export."]}


def build() -> dict:
    audit_wording()  # v2 preserves v1 requirements/nodes used by the ladder catalog.
    ladders = json.loads((ROOT / LADDERS).read_text())
    validate_ladders(ROOT, ladders)
    ontology = json.loads((ROOT / ONTOLOGY).read_text())
    disposition = json.loads((ROOT / ROLES).read_text())
    result = inventory(ontology, ladders, disposition)
    sources = (ONTOLOGY, LADDERS, ROLES, "analysis/audit_evidence_calibration_attachment_boundary.py",
               "docs/CLAIM_ATTACHMENT_BOUNDARY_2026-09-30.md")
    return {"schema": "crane-evidence-calibration-attachment-boundary/v1-development",
            "recorded_date": "2026-09-30", "status": "INVENTORY_AUDITED_SEMANTIC_ATTACHMENT_OPEN",
            "bindings": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
                         for path in sources], **result,
            "model_call_attempted": False, "method_key_opened": False,
            "support_labels_generated": False, "endpoint_scores_generated": False,
            "pilot_annotation_authorized": False, "p11_authorized": False,
            "confirmation_independent_n": 0, "replication_independent_n": 0}


if __name__ == "__main__":
    # Read-only audit: a changed snapshot must be reviewed, never overwritten here.
    result = build()
    if json.loads((ROOT / OUTPUT).read_text()) != result:
        raise ValueError("attachment-boundary inventory differs from its retained snapshot")
    print(json.dumps({key: value for key, value in result.items() if key not in ("contracts", "bindings")},
                     indent=2, sort_keys=True))
