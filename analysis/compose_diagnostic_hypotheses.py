#!/usr/bin/env python3
"""Compose bounded diagnostic claims over a finite, versioned predicate registry.

The public interface is ``compose(packet, registry) -> certificate``.  Primitive
diagnostic tools remain responsible for producing predicates; this module only
checks their consistency and classifies registered mechanisms as entailed,
excluded, or unresolved across every admissible completion of missing evidence.
"""

from __future__ import annotations

import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
from typing import Any, Iterable


PACKET_SCHEMA = "crane-diagnostic-predicate-packet/v1"
REGISTRY_SCHEMA = "crane-diagnostic-composition-registry/v1"
CERTIFICATE_SCHEMA = "crane-diagnostic-composition-certificate/v1"
MAX_PREDICATES = 20


def _canonical_sha256(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _literal_value(world: dict[str, bool], literal: dict[str, Any]) -> bool:
    return world[literal["predicate"]] is literal["value"]


def _constraints_hold(world: dict[str, bool], registry: dict[str, Any]) -> bool:
    for rule in registry.get("implications", []):
        if _literal_value(world, rule["if"]) and not _literal_value(world, rule["then"]):
            return False
    for group in registry.get("mutually_exclusive", []):
        if sum(world[name] for name in group) > 1:
            return False
    return True


def _mechanism_holds(world: dict[str, bool], mechanism: dict[str, Any]) -> bool:
    return all(_literal_value(world, literal) for literal in mechanism["requires"])


def _observations(packet: dict[str, Any], predicates: set[str]) -> tuple[dict[str, bool], dict[str, list[str]]]:
    known: dict[str, bool] = {}
    evidence: dict[str, list[str]] = {}
    for item in packet.get("observations", []):
        predicate = item.get("predicate")
        value = item.get("value")
        if predicate not in predicates:
            raise ValueError(f"packet contains unregistered predicate: {predicate}")
        if not isinstance(value, bool):
            raise ValueError(f"predicate {predicate} does not have a boolean value")
        if predicate in known and known[predicate] is not value:
            raise ValueError(f"contradictory observations for predicate: {predicate}")
        known[predicate] = value
        identifiers = item.get("evidence_ids", [])
        if not isinstance(identifiers, list) or any(not isinstance(x, str) for x in identifiers):
            raise ValueError(f"predicate {predicate} has invalid evidence IDs")
        evidence.setdefault(predicate, []).extend(identifiers)
    return known, evidence


def _worlds(predicates: list[str], known: dict[str, bool], registry: dict[str, Any]) -> list[dict[str, bool]]:
    unknown = [name for name in predicates if name not in known]
    worlds = []
    for values in product((False, True), repeat=len(unknown)):
        world = {**known, **dict(zip(unknown, values, strict=True))}
        if _constraints_hold(world, registry):
            worlds.append(world)
    return worlds


def _minimal_direct_support(
    mechanism: dict[str, Any], known: dict[str, bool], evidence: dict[str, list[str]]
) -> list[dict[str, Any]]:
    support = []
    for literal in mechanism["requires"]:
        name = literal["predicate"]
        if known.get(name) is literal["value"]:
            support.append(
                {
                    "predicate": name,
                    "value": literal["value"],
                    "evidence_ids": sorted(set(evidence.get(name, []))),
                }
            )
    return support


def _project(world: dict[str, bool], names: Iterable[str]) -> dict[str, bool]:
    return {name: world[name] for name in sorted(set(names))}


def compose(packet: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    """Return one fail-closed composition certificate without side effects."""
    if packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("unsupported diagnostic predicate packet schema")
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("unsupported diagnostic composition registry schema")
    if registry.get("out_of_model_possible") is not True:
        raise ValueError("registry must explicitly preserve the out-of-model possibility")
    predicates = registry.get("predicates")
    mechanisms = registry.get("mechanisms")
    if not isinstance(predicates, list) or not predicates or len(predicates) > MAX_PREDICATES:
        raise ValueError("registry predicate inventory is empty or exceeds the finite bound")
    if len(set(predicates)) != len(predicates) or any(not isinstance(x, str) for x in predicates):
        raise ValueError("registry predicate inventory is invalid")
    if not isinstance(mechanisms, list) or not mechanisms:
        raise ValueError("registry has no mechanisms")
    predicate_set = set(predicates)
    mechanism_ids = [item.get("id") for item in mechanisms]
    if len(set(mechanism_ids)) != len(mechanism_ids) or any(not item for item in mechanism_ids):
        raise ValueError("registry mechanism IDs are invalid")
    for mechanism in mechanisms:
        required = mechanism.get("requires")
        if not isinstance(required, list) or not required:
            raise ValueError(f"mechanism {mechanism['id']} has no requirements")
        if any(item.get("predicate") not in predicate_set or not isinstance(item.get("value"), bool) for item in required):
            raise ValueError(f"mechanism {mechanism['id']} has invalid requirements")

    applicable_ids = packet.get("applicable_mechanism_ids", mechanism_ids)
    if (
        not isinstance(applicable_ids, list)
        or not applicable_ids
        or any(not isinstance(value, str) for value in applicable_ids)
        or len(set(applicable_ids)) != len(applicable_ids)
        or not set(applicable_ids).issubset(set(mechanism_ids))
    ):
        raise ValueError("packet applicable mechanism IDs are invalid")
    applicable = [item for item in mechanisms if item["id"] in set(applicable_ids)]

    answer_units = packet.get("answer_units", [])
    if not isinstance(answer_units, list):
        raise ValueError("packet answer_units must be a list")
    units_by_id: dict[str, dict[str, Any]] = {}
    for item in answer_units:
        identifier = item.get("unit_id")
        if not isinstance(identifier, str) or not identifier or identifier in units_by_id:
            raise ValueError("packet answer-unit IDs are invalid or repeated")
        if item.get("role") not in {"diagnosis", "evidence", "execution", "limit", "outcome"}:
            raise ValueError(f"answer unit {identifier} has an invalid role")
        if not isinstance(item.get("text"), str) or not item["text"].strip():
            raise ValueError(f"answer unit {identifier} has no text")
        evidence_ids = item.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or any(not isinstance(value, str) for value in evidence_ids):
            raise ValueError(f"answer unit {identifier} has invalid evidence IDs")
        units_by_id[identifier] = item
    declared_unit_ids = set(units_by_id)

    try:
        known, evidence = _observations(packet, predicate_set)
    except ValueError as error:
        return {
            "schema": CERTIFICATE_SCHEMA,
            "packet_id": packet.get("packet_id"),
            "registry_id": registry.get("registry_id"),
            "registry_sha256": _canonical_sha256(registry),
            "model_scope": registry.get("model_scope"),
            "out_of_model_possible": True,
            "status": "evidence_problem",
            "evidence_problem": str(error),
            "admissible_world_count": 0,
            "mechanisms": [],
            "answer_plan": None,
        }

    admissible = _worlds(predicates, known, registry)
    if not admissible:
        return {
            "schema": CERTIFICATE_SCHEMA,
            "packet_id": packet.get("packet_id"),
            "registry_id": registry.get("registry_id"),
            "registry_sha256": _canonical_sha256(registry),
            "model_scope": registry.get("model_scope"),
            "out_of_model_possible": True,
            "status": "evidence_problem",
            "evidence_problem": "retained observations violate the registered composition constraints",
            "admissible_world_count": 0,
            "mechanisms": [],
            "answer_plan": None,
        }

    results = []
    for mechanism in applicable:
        truth = [_mechanism_holds(world, mechanism) for world in admissible]
        relevant = [item["predicate"] for item in mechanism["requires"]]
        if all(truth):
            status = "entailed"
            witnesses: dict[str, Any] = {}
        elif not any(truth):
            status = "excluded"
            witnesses = {}
        else:
            status = "unresolved"
            positive = admissible[truth.index(True)]
            negative = admissible[truth.index(False)]
            witnesses = {
                "supporting_completion": _project(positive, relevant),
                "excluding_completion": _project(negative, relevant),
            }
        missing = sorted(name for name in relevant if name not in known)
        results.append(
            {
                "mechanism_id": mechanism["id"],
                "status": status,
                "causal_language_level": mechanism["causal_language_level"],
                "claim": mechanism["claim"],
                "required_unit_ids": mechanism["required_unit_ids"],
                "support": _minimal_direct_support(mechanism, known, evidence) if status == "entailed" else [],
                "missing_discriminators": missing if status == "unresolved" else [],
                "witnesses": witnesses,
            }
        )

    entailed = [item for item in results if item["status"] == "entailed"]
    entailed.sort(
        key=lambda item: next(
            mechanism.get("priority", 0)
            for mechanism in applicable
            if mechanism["id"] == item["mechanism_id"]
        ),
        reverse=True,
    )
    unresolved = [item for item in results if item["status"] == "unresolved"]
    primary = entailed[0] if entailed else None
    missing_units = (
        sorted(set(primary["required_unit_ids"]) - declared_unit_ids)
        if primary
        else []
    )
    # Mechanism classification is still useful before language compilation, but a
    # certificate must never look language-ready when its decisive checked units
    # are absent.  Keeping this state explicit lets conformance tests inspect the
    # lattice while forcing every user-facing renderer to fail closed.
    language_ready = bool(primary) and not missing_units
    answer_plan = {
        "primary_mechanism_id": primary["mechanism_id"] if primary else None,
        "primary_claim": primary["claim"] if primary else None,
        "required_unit_ids": primary["required_unit_ids"] if primary else [],
        "decisive_evidence_ids": sorted(
            {
                identifier
                for support in (primary["support"] if primary else [])
                for identifier in support["evidence_ids"]
            }
        ),
        "unresolved_alternatives": [item["mechanism_id"] for item in unresolved],
        "missing_discriminators": sorted(
            {name for item in unresolved for name in item["missing_discriminators"]}
        ),
        "units": ([] if not language_ready else (
            [
                units_by_id[identifier]
                for identifier in (primary["required_unit_ids"] if primary else [])
            ]
            + [
                item
                for item in answer_units
                if item.get("always_include") is True
                and item["unit_id"] not in set(primary["required_unit_ids"] if primary else [])
            ]
        )),
        "language_ready": language_ready,
        "missing_required_unit_ids": missing_units,
        "scope_limit": (
            "The certificate is relative to the declared registry and retained observations; "
            "unmodeled mechanisms remain possible."
        ),
    }
    return {
        "schema": CERTIFICATE_SCHEMA,
        "packet_id": packet.get("packet_id"),
        "registry_id": registry.get("registry_id"),
        "registry_sha256": _canonical_sha256(registry),
        "model_scope": registry.get("model_scope"),
        "applicable_mechanism_ids": applicable_ids,
        "out_of_model_possible": True,
        "status": "composed",
        "evidence_problem": None,
        "admissible_world_count": len(admissible),
        "mechanisms": results,
        "answer_plan": answer_plan,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compose(
        json.loads(args.packet.read_text(encoding="utf-8")),
        json.loads(args.registry.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if result["status"] == "evidence_problem":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
