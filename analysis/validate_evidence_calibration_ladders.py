#!/usr/bin/env python3
"""Validate mechanism-specific evidence ladders against the public claim ontology."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from evidence_calibration_io import ontology_from_dict


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "crane-evidence-calibration-ladder-catalog/v1-development"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path, catalog: dict[str, Any]) -> dict[str, Any]:
    if catalog.get("schema") != SCHEMA:
        raise ValueError("unsupported ladder catalog schema")
    ontology_ref = catalog["ontology"]
    ontology_path = root / ontology_ref["path"]
    if sha256(ontology_path) != ontology_ref["sha256"]:
        raise ValueError("ontology hash mismatch")
    ontology = ontology_from_dict(json.loads(ontology_path.read_text(encoding="utf-8")))
    requirements = {item.requirement_id: item for item in ontology.evidence_requirements}
    claims = {item.claim_id: item for item in ontology.claim_contracts}
    node_ids = {item.node_id for item in ontology.diagnostic_nodes}
    non_entailment_ids = {item.non_entailment_id for item in ontology.non_entailments}

    ladders = catalog.get("ladders")
    if not isinstance(ladders, list) or not ladders:
        raise ValueError("ladder catalog is empty")
    ladder_ids = [item.get("ladder_id") for item in ladders]
    if any(not isinstance(item, str) or not item for item in ladder_ids):
        raise ValueError("ladder ID is missing")
    if len(ladder_ids) != len(set(ladder_ids)):
        raise ValueError("duplicate ladder ID")

    public_roles = {role for requirement in requirements.values() for role in requirement.evidence_roles}
    summaries = []
    for ladder in ladders:
        levels = ladder.get("levels")
        if not isinstance(levels, list) or len(levels) < 2:
            raise ValueError(f"{ladder['ladder_id']} needs at least two levels")
        if [level.get("level_index") for level in levels] != list(range(len(levels))):
            raise ValueError(f"{ladder['ladder_id']} levels are not contiguous")
        previous_roles: set[str] = set()
        for level in levels:
            roles = level.get("available_evidence_roles")
            restored = level.get("newly_restored_roles")
            claim_ids = level.get("potentially_assessable_claim_ids")
            if not all(isinstance(value, list) for value in (roles, restored, claim_ids)):
                raise ValueError("ladder level lists are malformed")
            if len(roles) != len(set(roles)) or len(restored) != len(set(restored)):
                raise ValueError("ladder role lists contain duplicates")
            role_set = set(roles)
            restored_set = set(restored)
            if not previous_roles.issubset(role_set):
                raise ValueError(f"{ladder['ladder_id']} removes evidence in a stronger level")
            if restored_set != role_set - previous_roles:
                raise ValueError(f"{ladder['ladder_id']} restored-role delta is incorrect")
            if not role_set.issubset(public_roles):
                raise ValueError(f"{ladder['ladder_id']} uses an undeclared evidence role")
            if len(claim_ids) != len(set(claim_ids)) or not set(claim_ids).issubset(claims):
                raise ValueError(f"{ladder['ladder_id']} has invalid assessable claims")
            computed = {
                claim_id
                for claim_id, claim in claims.items()
                if all(
                    set(requirements[requirement_id].evidence_roles).issubset(role_set)
                    for requirement_id in claim.required_evidence_ids
                )
            }
            if set(claim_ids) != computed:
                raise ValueError(
                    f"{ladder['ladder_id']} E{level['level_index']} assessable claims differ "
                    "from ontology-required roles"
                )
            previous_roles = role_set
        expected_terminal = set(ladder["terminal_evidence_roles"])
        if previous_roles != expected_terminal:
            raise ValueError(f"{ladder['ladder_id']} terminal roles do not match final level")
        if not set(ladder["in_scope_node_ids"]).issubset(node_ids):
            raise ValueError(f"{ladder['ladder_id']} has an unknown in-scope node")
        if not set(ladder["required_non_entailment_ids"]).issubset(non_entailment_ids):
            raise ValueError(f"{ladder['ladder_id']} has an unknown non-entailment")
        if ladder["independent_unit_increment"] != 1:
            raise ValueError("one ladder must contribute exactly one episode unit")
        summaries.append(
            {
                "ladder_id": ladder["ladder_id"],
                "level_count": len(levels),
                "terminal_role_count": len(previous_roles),
                "terminal_assessable_claim_count": len(levels[-1]["potentially_assessable_claim_ids"]),
            }
        )

    return {
        "schema": "crane-evidence-calibration-ladder-validation/v1-development",
        "catalog_id": catalog["catalog_id"],
        "status": "PASS_DEVELOPMENT_NOT_FROZEN",
        "ladder_count": len(ladders),
        "independent_unit": "episode_configuration",
        "summaries": summaries,
        "confirmation_authorized": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--catalog",
        type=Path,
        default=ROOT / "configs/evidence_calibration_ladders_v1_development.json",
    )
    args = parser.parse_args()
    path = args.catalog if args.catalog.is_absolute() else ROOT / args.catalog
    try:
        result = validate(ROOT, json.loads(path.read_text(encoding="utf-8")))
    except (KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
