#!/usr/bin/env python3
"""Structural validation for an unqualified assertion-role successor candidate.

This module does not map roles or kinds to a primary endpoint. Qualification and a
prospectively bound endpoint map are separate gates.
"""

from __future__ import annotations

from typing import Any


INPUT_SCHEMA = "crane-evidence-calibration-claim-role-input/v2-development"
RETURN_SCHEMA = "crane-evidence-calibration-claim-role-return/v2-development"
STANCES = {
    "ASSERTED_FACT", "HEDGED_CURRENT_EPISODE",
    "INFERENCE_LIMITATION", "UNENDORSED_HYPOTHETICAL_OR_QUOTE", "UNRESOLVED",
}
KINDS = {
    "TASK_OUTCOME", "SOFTWARE_ACTION_EVENT", "RECOVERY_TRACE_EVENT",
    "MEASURED_RESPONSE_RECOVERY", "MOTION_OBSERVATION", "COMMAND_OBSERVATION",
    "COMMAND_MOTION_RELATION", "GEOMETRY_PLANNING_RELATION",
    "SPECIFIC_PHYSICAL_CAUSE", "RECOVERY_CAUSAL_RELATION",
    "SOURCE_OR_CONFIG_FACT", "EVIDENCE_AVAILABILITY", "OTHER",
}
POLARITIES = {"POSITIVE", "NEGATIVE", "NOT_APPLICABLE"}


def validate(payload: dict[str, Any], returned: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema", "opaque_response_id", "response_text", "claims"}:
        raise ValueError("v2 input has missing or unknown fields")
    if payload["schema"] != INPUT_SCHEMA or not isinstance(payload["opaque_response_id"], str) or not payload["opaque_response_id"]:
        raise ValueError("v2 input schema or identity mismatch")
    response, claims = payload["response_text"], payload["claims"]
    if not isinstance(response, str) or not response or not isinstance(claims, list) or not claims:
        raise ValueError("v2 input needs response text and claims")
    ids = []
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"item_id", "response_span", "claim_text"}:
            raise ValueError("v2 claim input has missing or unknown fields")
        if (not all(isinstance(claim[key], str) and claim[key]
                    for key in ("item_id", "response_span", "claim_text"))
                or claim["response_span"] not in response):
            raise ValueError("v2 claim identity or span is invalid")
        ids.append(claim["item_id"])
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate v2 claim ID")
    if not isinstance(returned, dict) or set(returned) != {"schema", "opaque_response_id", "claim_roles", "attestation"}:
        raise ValueError("v2 return has missing or unknown fields")
    if (returned["schema"] != RETURN_SCHEMA or returned["opaque_response_id"] != payload["opaque_response_id"]
            or returned["attestation"] != "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT"):
        raise ValueError("v2 return schema, identity, or attestation mismatch")
    judgments = returned["claim_roles"]
    if not isinstance(judgments, list) or len(judgments) != len(claims):
        raise ValueError("v2 return needs one judgment per claim")
    if [item.get("item_id") if isinstance(item, dict) else None for item in judgments] != ids:
        raise ValueError("v2 claim IDs must match exactly and in order")
    unresolved = []
    for claim, judgment in zip(claims, judgments, strict=True):
        if not isinstance(judgment, dict) or set(judgment) != {"item_id", "stance", "claim_kind", "polarity", "rationale_span"}:
            raise ValueError("v2 judgment has missing or unknown fields")
        stance, kind, polarity = judgment["stance"], judgment["claim_kind"], judgment["polarity"]
        span = judgment["rationale_span"]
        if (not isinstance(stance, str) or stance not in STANCES
                or not isinstance(kind, str) or kind not in KINDS
                or not isinstance(polarity, str) or polarity not in POLARITIES):
            raise ValueError("v2 judgment has an unknown category")
        if not isinstance(span, str) or not span or span not in claim["response_span"]:
            raise ValueError("v2 rationale must quote its own claim span")
        if stance in {"INFERENCE_LIMITATION", "UNENDORSED_HYPOTHETICAL_OR_QUOTE", "UNRESOLVED"} and polarity != "NOT_APPLICABLE":
            raise ValueError("nonasserted v2 claim cannot carry episode polarity")
        if stance == "UNRESOLVED":
            unresolved.append(judgment["item_id"])
    return {
        "schema": "crane-evidence-calibration-claim-role-v2-structural-validation/development",
        "status": "STRUCTURALLY_VALID_SEMANTIC_QUALIFICATION_REQUIRED",
        "claim_count": len(ids),
        "unresolved_item_ids": unresolved,
        "semantic_reference_review_complete": False,
        "role_kind_polarity_qualified": False,
        "mechanistic_flag_authorized": False,
        "response_rank_authorized": False,
        "endpoint_scoring_authorized": False,
    }
