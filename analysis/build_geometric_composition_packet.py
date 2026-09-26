#!/usr/bin/env python3
"""Compile one validated land-geometric diagnostic into a composition packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PACKET_SCHEMA = "crane-diagnostic-predicate-packet/v1"
ADAPTER_VERSION = "land-geometric-composition-adapter-v1"
VERSIONS = {"geometric-route-restriction-v1", "geometric-route-restriction-v2"}


def _measurement_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = result.get("measurements")
    if not isinstance(items, list):
        raise ValueError("geometric result has no measurement list")
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in indexed:
            raise ValueError("geometric measurement IDs are invalid or repeated")
        indexed[identifier] = item
    return indexed


def _evidence_ids(*items: dict[str, Any]) -> list[str]:
    result: set[str] = set()
    for item in items:
        values = item.get("evidence_ids", [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError(f"measurement {item.get('id')} has invalid evidence IDs")
        result.update(values)
    return sorted(result)


def _observation(predicate: str, value: bool, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {"predicate": predicate, "value": value, "evidence_ids": _evidence_ids(*items)}


def _unit(unit_id: str, role: str, text: str, evidence_ids: list[str], *, always=False) -> dict[str, Any]:
    value: dict[str, Any] = {
        "unit_id": unit_id,
        "role": role,
        "text": text,
        "evidence_ids": evidence_ids,
    }
    if always:
        value["always_include"] = True
    return value


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    if document.get("visibility") != "robot_visible":
        raise ValueError("adapter requires a robot-visible diagnostic export")
    result = document.get("diagnostic_result")
    if not isinstance(result, dict) or result.get("computation_version") not in VERSIONS:
        raise ValueError("unsupported geometric diagnostic result")
    episode_id = result.get("episode_id")
    if not isinstance(episode_id, str) or episode_id != document.get("episode_id"):
        raise ValueError("diagnostic/export episode IDs do not match")
    disposition = result.get("disposition")
    mechanism = result.get("mechanism")
    if disposition not in {"supported", "not_triggered", "insufficient"}:
        raise ValueError(f"unsupported geometric disposition: {disposition}")
    fields = [result.get(name) for name in ("diagnosis", "failure_chain", "limits", "next_check")]
    if any(not isinstance(value, str) or not value.strip() for value in fields):
        raise ValueError("geometric answer fields are incomplete")
    diagnosis, failure_chain, limits, next_check = fields
    measurements = _measurement_map(result)
    action = measurements.get("action_status")
    if action is None:
        # Some v1 partial exports retain the action only in checked prose. Refuse to infer it.
        raise ValueError("geometric result lacks an action-status measurement")
    if action.get("value") not in {"succeeded", "aborted", "remained active at the observation cutoff"}:
        raise ValueError("geometric result has an unsupported action status")
    action_value = action["value"]
    observations = []
    if action_value in {"succeeded", "aborted"}:
        observations.extend(
            [
                _observation("action_succeeded", action_value == "succeeded", [action]),
                _observation("action_aborted", action_value == "aborted", [action]),
            ]
        )
    units: list[dict[str, Any]] = []

    decisive_ids = result.get("decisive_measurement_ids")
    if not isinstance(decisive_ids, list) or any(not isinstance(value, str) for value in decisive_ids):
        raise ValueError("geometric result has invalid decisive-measurement IDs")
    missing_decisive = [value for value in decisive_ids if value not in measurements]
    if disposition != "insufficient" and missing_decisive:
        raise ValueError("geometric result lacks declared decisive measurements")
    decisive = [measurements[value] for value in decisive_ids if value in measurements]
    if not decisive:
        raise ValueError("geometric result retains no decisive measurements")

    applicable = [
        "geometric_route_restriction",
        "deadline_aligned_abort",
        "nominal_route_geometry",
        "geometry_evidence_insufficient",
        "recorded_route_change",
    ]
    if disposition == "supported" and mechanism == "geometric_route_restriction":
        observations.extend(
            [
                _observation("geometry_sufficient", True, decisive),
                _observation("geometry_supported", True, decisive),
                _observation("geometry_not_restricted", False, decisive),
                _observation("geometry_evidence_insufficient", False, decisive),
            ]
        )
        units.extend(
            [
                _unit("geometry-comparison", "diagnosis", diagnosis, _evidence_ids(*decisive)),
                _unit("model-scope-limit", "limit", limits, _evidence_ids(*decisive)),
            ]
        )
    elif disposition == "supported" and mechanism == "recorded_plan_change_with_unresolved_physical_trigger":
        observations.extend(
            [
                _observation("route_change_observed", True, decisive),
                _observation("geometry_sufficient", False, decisive),
            ]
        )
        units.extend(
            [
                _unit("path-comparison", "diagnosis", diagnosis, _evidence_ids(*decisive)),
                _unit("trigger-limit", "limit", limits, _evidence_ids(*decisive)),
            ]
        )
    elif disposition == "not_triggered":
        observations.extend(
            [
                _observation("geometry_sufficient", True, decisive),
                _observation("geometry_supported", False, decisive),
                _observation("geometry_not_restricted", True, decisive),
                _observation("geometry_evidence_insufficient", False, decisive),
            ]
        )
        units.extend(
            [
                _unit("nominal-geometry-comparison", "diagnosis", diagnosis, _evidence_ids(*decisive)),
                _unit(
                    "false-premise-rejection",
                    "limit",
                    "The retained bounded route evidence and successful action reject the question's failure premise.",
                    _evidence_ids(*decisive),
                ),
            ]
        )
    elif disposition == "insufficient":
        observations.extend(
            [
                _observation("geometry_evidence_insufficient", True, decisive),
                _observation("geometry_sufficient", False, decisive),
            ]
        )
        units.append(_unit("insufficiency-diagnosis", "diagnosis", diagnosis, _evidence_ids(*decisive)))
    else:
        raise ValueError(f"unsupported mechanism/disposition pair: {mechanism}/{disposition}")

    deadline = measurements.get("configured_deadline")
    timing = measurements.get("absolute_deadline_timing_difference")
    if action_value == "aborted" and deadline is not None and timing is not None:
        observations.extend(
            [
                _observation("deadline_source_qualified", True, [deadline]),
                _observation("deadline_timing_aligned", True, [timing]),
            ]
        )
        units.append(
            _unit("deadline-comparison", "evidence", diagnosis, _evidence_ids(deadline, timing), always=True)
        )

    units.extend(
        [
            _unit("retained-execution", "execution", failure_chain, _evidence_ids(action), always=True),
            _unit("geometry-limit", "limit", limits, _evidence_ids(*decisive), always=True),
            _unit("next-check", "limit", f"Next check: {next_check}", [], always=True),
        ]
    )
    return {
        "schema": PACKET_SCHEMA,
        "packet_id": f"{episode_id}:geometric-composition-v1",
        "adapter_version": ADAPTER_VERSION,
        "applicable_mechanism_ids": applicable,
        "source": {
            "episode_id": episode_id,
            "diagnostic_id": result.get("diagnostic_id"),
            "computation_version": result.get("computation_version"),
            "sha256": source_sha256,
        },
        "observations": observations,
        "answer_units": units,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.diagnostic.read_bytes()
    packet = build(json.loads(raw), source_sha256=hashlib.sha256(raw).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
