#!/usr/bin/env python3
"""Add explicit coverage and nonterminal units to the validated geometry adapter."""

from __future__ import annotations

from typing import Any

from build_geometric_composition_packet import (
    _evidence_ids,
    _measurement_map,
    _unit,
    build as build_v1,
)


ADAPTER_VERSION = "land-geometric-composition-adapter-v2"


def _append(packet: dict[str, Any], item: dict[str, Any]) -> None:
    if any(existing["unit_id"] == item["unit_id"] for existing in packet["answer_units"]):
        raise ValueError(f"duplicate v2 answer unit: {item['unit_id']}")
    packet["answer_units"].append(item)


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    packet = build_v1(document, source_sha256=source_sha256)
    packet["adapter_version"] = ADAPTER_VERSION
    packet["packet_id"] = packet["packet_id"].replace("composition-v1", "composition-v2")
    result = document["diagnostic_result"]
    measurements = _measurement_map(result)
    disposition = result["disposition"]
    reference = document.get("reference_computation")
    route = reference.get("direct_route") if isinstance(reference, dict) else None
    fully_covered = route.get("fully_covered") if isinstance(route, dict) else None

    if disposition == "not_triggered":
        if fully_covered is not True or route.get("has_lethal_cell") is not False:
            raise ValueError("nominal geometry requires a fully covered robot-visible clear-route audit")
        clearance = measurements.get("direct_route_minimum_clearance")
        deviation = measurements.get("maximum_lateral_deviation")
        if clearance is None or deviation is None:
            raise ValueError("nominal geometry lacks clearance or trajectory measurements")
        unit = next(
            item
            for item in packet["answer_units"]
            if item["unit_id"] == "nominal-geometry-comparison"
        )
        unit["text"] = (
            "The action succeeded. The fully covered direct-route audit found no "
            "non-traversable cell; minimum lethal-cell clearance was "
            f"{float(clearance['value']):.6g} {clearance.get('unit')}, and maximum recorded "
            f"lateral deviation was {float(deviation['value']):.6g} {deviation.get('unit')}."
        )
        unit["evidence_ids"] = _evidence_ids(clearance, deviation, measurements["action_status"])

    if disposition == "insufficient":
        if fully_covered is not False:
            raise ValueError(
                "insufficient geometry requires robot-visible proof that route coverage is incomplete"
            )
        evidence = [
            measurements[name]
            for name in ("costmap_snapshot_sha256", "action_status")
            if name in measurements
        ]
        _append(
            packet,
            _unit(
                "coverage-limit",
                "limit",
                "The retained grid does not cover the complete requested route.",
                _evidence_ids(*evidence),
            ),
        )
        progress = measurements.get("maximum_forward_progress")
        if progress is not None:
            _append(
                packet,
                _unit(
                    "progress",
                    "evidence",
                    f"Maximum recorded forward progress was {float(progress['value']):.3f} {progress.get('unit')}.",
                    _evidence_ids(progress),
                ),
            )
        action = measurements["action_status"]
        _append(
            packet,
            _unit(
                "nonterminal-limit",
                "limit",
                "The action remained active when the observation window ended; this does not establish a terminal navigation failure or a unique physical cause.",
                _evidence_ids(action),
            ),
        )
    return packet
