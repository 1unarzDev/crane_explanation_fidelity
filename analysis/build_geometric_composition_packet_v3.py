#!/usr/bin/env python3
"""Build measurement-complete geometry packets without altering the frozen v2 adapter."""

from __future__ import annotations

from typing import Any

from build_geometric_composition_packet_v2 import (
    _append,
    _evidence_ids,
    _measurement_map,
    _unit,
    build as build_v2,
)


ADAPTER_VERSION = "land-geometric-composition-adapter-v3"


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    packet = build_v2(document, source_sha256=source_sha256)
    packet["adapter_version"] = ADAPTER_VERSION
    packet["packet_id"] = packet["packet_id"].replace("composition-v2", "composition-v3")
    result = document["diagnostic_result"]
    measurements = _measurement_map(result)
    disposition = result["disposition"]
    reference = document.get("reference_computation")
    route = reference.get("direct_route") if isinstance(reference, dict) else None

    if disposition == "insufficient":
        action = measurements["action_status"]
        if action.get("value") == "aborted":
            packet["answer_units"] = [
                item for item in packet["answer_units"] if item["unit_id"] != "nonterminal-limit"
            ]

    # A configured deadline is not evidence that it triggered an abort. The frozen v2 adapter
    # marked every insufficient abort with timing fields as deadline-aligned; v3 requires the
    # primitive diagnostic itself to have established that relationship.
    if disposition == "insufficient" and result.get("mechanism") != "deadline_aligned_abort":
        for observation in packet["observations"]:
            if observation["predicate"] == "deadline_timing_aligned":
                observation["value"] = False
        packet["answer_units"] = [
            item for item in packet["answer_units"] if item["unit_id"] != "deadline-comparison"
        ]

    # A route-change export may also retain a bounded navigation-model restriction even when
    # snapshot-to-plan causation and obstacle identity remain unresolved. Promote that narrower
    # mechanism only when the robot-visible audit found both a blocked direct-route cell and a
    # remaining connection in the same retained grid.
    if (
        disposition == "supported"
        and result.get("mechanism") == "recorded_plan_change_with_unresolved_physical_trigger"
        and isinstance(route, dict)
        and route.get("has_lethal_cell") is True
        and reference.get("connected_below_cost_253") is True
    ):
        first = route.get("first_lethal_sample_from_start")
        if not isinstance(first, dict) or not isinstance(first.get("x"), (int, float)):
            raise ValueError("bounded geometric restriction lacks its first blocked-route location")
        decisive = [
            measurements[name]
            for name in (
                "first_lethal_route_x",
                "direct_route_minimum_clearance",
                "maximum_lateral_deviation",
                "action_status",
            )
            if name in measurements
        ]
        if len(decisive) != 4:
            raise ValueError("bounded geometric restriction lacks decisive measurements")
        for observation in packet["observations"]:
            if observation["predicate"] == "geometry_sufficient":
                observation["value"] = True
                observation["evidence_ids"] = _evidence_ids(*decisive)
                break
        else:
            raise ValueError("route-change packet lacks its geometry-sufficiency observation")
        packet["observations"].extend(
            [
                {
                    "predicate": "geometry_supported",
                    "value": True,
                    "evidence_ids": _evidence_ids(*decisive),
                },
                {
                    "predicate": "geometry_not_restricted",
                    "value": False,
                    "evidence_ids": _evidence_ids(*decisive),
                },
                {
                    "predicate": "geometry_evidence_insufficient",
                    "value": False,
                    "evidence_ids": _evidence_ids(*decisive),
                },
            ]
        )
        _append(
            packet,
            _unit(
                "geometry-comparison",
                "diagnosis",
                (
                    "The retained navigation-model snapshot marked the requested direct route "
                    f"non-traversable near x={float(first['x']):.3f} m while retaining a "
                    "below-threshold connection from the action-result pose to the goal."
                ),
                _evidence_ids(*decisive),
            ),
        )
        _append(
            packet,
            _unit(
                "model-scope-limit",
                "limit",
                (
                    "This is a bounded navigation-model restriction. The incomplete snapshot "
                    "does not prove global physical no-path, a unique obstacle identity, exact "
                    "Nav2 consumption, or that the snapshot caused the delivered plan change."
                ),
                _evidence_ids(*decisive),
            ),
        )

    if disposition == "insufficient":
        action = measurements["action_status"]
        if action.get("value") == "remained active at the observation cutoff":
            # The inherited v2 unit is correct for a nonterminal observation boundary.
            return packet
        if action.get("value") == "aborted":
            _append(
                packet,
                _unit(
                    "terminal-mechanism-limit",
                    "limit",
                    "The action aborted, but the retained geometry does not establish that a route restriction caused the abort.",
                    _evidence_ids(action),
                ),
            )
        else:
            raise ValueError("insufficient geometry has an unsupported action boundary")
    return packet
