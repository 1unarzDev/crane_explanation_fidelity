#!/usr/bin/env python3
"""Structural gate for method-blind, assertion-aware claim-role judgments.

This gate does not qualify a classifier or decide whether its semantic roles are right.
It prevents limitation/source/hypothetical claims from mechanically becoming asserted
diagnostic ranks when a future, separately qualified role return is joined to scoring.
"""

from __future__ import annotations

from typing import Any


INPUT_SCHEMA = "crane-evidence-calibration-claim-role-input/v1-development"
RETURN_SCHEMA = "crane-evidence-calibration-claim-role-return/v1-development"
LEVELS = (
    "task_outcome", "software_action_failure", "recovery_mechanism",
    "command_motion_discrepancy", "physical_execution_mechanism",
    "specific_physical_cause",
)
ROLES = {
    "AFFIRMATIVE_EPISODE_ASSERTION",
    "HEDGED_DIAGNOSTIC_CANDIDATE",
    "NON_DIAGNOSTIC_OBSERVATION_OR_SOURCE",
    "LIMITATION_OR_NON_ENTAILMENT",
    "HYPOTHETICAL_OR_ATTRIBUTED",
    "UNRESOLVED_ROLE",
}


def validate_claim_roles(payload: dict[str, Any], returned: dict[str, Any]) -> dict[str, Any]:
    """Validate exact identity/coverage and retain asserted and hedged levels separately."""
    if not isinstance(payload, dict) or set(payload) != {"schema", "opaque_response_id", "response_text", "claims"}:
        raise ValueError("claim-role input has missing or unknown fields")
    if payload["schema"] != INPUT_SCHEMA or not isinstance(payload["opaque_response_id"], str) or not payload["opaque_response_id"]:
        raise ValueError("unsupported claim-role input or identity")
    response = payload["response_text"]
    claims = payload["claims"]
    if not isinstance(response, str) or not response or not isinstance(claims, list) or not claims:
        raise ValueError("claim-role input needs response text and atomic claims")
    ids = []
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {"item_id", "response_span", "claim_text"}:
            raise ValueError("atomic claim input has missing or unknown fields")
        item_id, span, statement = claim["item_id"], claim["response_span"], claim["claim_text"]
        if not all(isinstance(value, str) and value for value in (item_id, span, statement)) or span not in response:
            raise ValueError("atomic claim identity, text, or exact response span is invalid")
        ids.append(item_id)
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate atomic claim ID")

    if not isinstance(returned, dict) or set(returned) != {"schema", "opaque_response_id", "claim_roles", "attestation"}:
        raise ValueError("claim-role return has missing or unknown fields")
    if returned["schema"] != RETURN_SCHEMA or returned["opaque_response_id"] != payload["opaque_response_id"]:
        raise ValueError("claim-role return schema or identity mismatch")
    if returned["attestation"] != "METHOD_BLIND_ASSERTION_ROLE_ATTEMPT":
        raise ValueError("claim-role attestation mismatch")
    judgments = returned["claim_roles"]
    if not isinstance(judgments, list) or len(judgments) != len(claims):
        raise ValueError("every atomic claim needs exactly one role")
    if [item.get("item_id") if isinstance(item, dict) else None for item in judgments] != ids:
        raise ValueError("claim-role IDs must match the input exactly and in order")
    affirmative_levels = []
    hedged_candidate_levels = []
    unresolved = []
    for claim, judgment in zip(claims, judgments, strict=True):
        if not isinstance(judgment, dict):
            raise ValueError("claim-role judgment must be an object")
        if set(judgment) != {"item_id", "role", "asserted_diagnostic_level", "rationale_span"}:
            raise ValueError("claim-role judgment has missing or unknown fields")
        role, level, span = judgment["role"], judgment["asserted_diagnostic_level"], judgment["rationale_span"]
        if not isinstance(role, str) or role not in ROLES:
            raise ValueError("unknown assertion role")
        if not isinstance(span, str) or not span or span not in claim["response_span"]:
            raise ValueError("role rationale must quote an exact substring of its atomic claim span")
        if role in {"AFFIRMATIVE_EPISODE_ASSERTION", "HEDGED_DIAGNOSTIC_CANDIDATE"}:
            if not isinstance(level, str) or level not in LEVELS:
                raise ValueError("episode assertion or hedged diagnosis needs a declared abstraction level")
            (affirmative_levels if role == "AFFIRMATIVE_EPISODE_ASSERTION" else hedged_candidate_levels).append(level)
        elif level is not None:
            raise ValueError("non-affirmative role cannot carry an asserted diagnostic level")
        if role == "UNRESOLVED_ROLE":
            unresolved.append(judgment["item_id"])
    return {
        "schema": "crane-evidence-calibration-claim-role-structural-validation/v1-development",
        "status": "STRUCTURALLY_VALID_SEMANTIC_QUALIFICATION_REQUIRED",
        "claim_count": len(ids),
        "affirmative_asserted_levels": affirmative_levels,
        "hedged_diagnostic_candidate_levels": hedged_candidate_levels,
        "unresolved_role_item_ids": unresolved,
        "mechanistic_flag_authorized": False,
        "response_rank_authorized": False,
        "endpoint_scoring_authorized": False,
    }
