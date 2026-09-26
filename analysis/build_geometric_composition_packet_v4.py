#!/usr/bin/env python3
"""Preserve all supported geometry details after the v2 coverage-gate failure."""

from __future__ import annotations

from typing import Any

from build_geometric_composition_packet_v3 import (
    _append,
    _evidence_ids,
    _measurement_map,
    _unit,
    build as build_v3,
)


ADAPTER_VERSION = "land-geometric-composition-adapter-v4"


def _measurement_unit(
    unit_id: str,
    text: str,
    *measurements: dict[str, Any],
    role: str = "evidence",
) -> dict[str, Any]:
    return _unit(unit_id, role, text, _evidence_ids(*measurements))


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    packet = build_v3(document, source_sha256=source_sha256)
    packet["adapter_version"] = ADAPTER_VERSION
    packet["packet_id"] = packet["packet_id"].replace("composition-v3", "composition-v4")
    diagnostic = document["diagnostic_result"]
    measurements = _measurement_map(diagnostic)
    disposition = diagnostic["disposition"]
    mechanism = diagnostic.get("mechanism")
    reference = document.get("reference_computation")
    route = reference.get("direct_route") if isinstance(reference, dict) else None

    deviation = measurements.get("maximum_lateral_deviation")
    if deviation is not None and disposition in {"supported", "insufficient"}:
        unit_id = "trajectory-geometry" if disposition == "insufficient" else "trajectory-comparison"
        _append(
            packet,
            _measurement_unit(
                unit_id,
                f"Delivered odometry reached {float(deviation['value']):.3f} {deviation.get('unit')} maximum lateral deviation.",
                deviation,
            ),
        )

    if (
        disposition == "supported"
        and mechanism == "recorded_plan_change_with_unresolved_physical_trigger"
    ):
        # The exporter uses True for any observed lethal sample, False only for a fully
        # covered clear route, and None for an incomplete route with no observed lethal
        # sample.  Both non-True completed cases support only the bounded negative wording.
        if (
            isinstance(reference, dict)
            and reference.get("status") == "completed"
            and isinstance(route, dict)
            and route.get("has_lethal_cell") is not True
        ):
            snapshot = measurements["costmap_snapshot_sha256"]
            _append(
                packet,
                _measurement_unit(
                    "negative-route-cell",
                    "The incomplete retained grid contained no observed blocked direct-route cell.",
                    snapshot,
                    role="limit",
                ),
            )
        elif isinstance(reference, dict) and reference.get("status") in {
            "insufficient",
            "not_run_missing_costmap_cell_payload",
        }:
            missing = reference.get("missing")
            if missing not in (["costmap_cells"], ["latestCostmapSnapshot.data"]):
                raise ValueError("masked geometry has an unexpected missing-evidence declaration")
            snapshot = measurements["costmap_snapshot_sha256"]
            _append(
                packet,
                _measurement_unit(
                    "missing-discriminator",
                    "The costmap cell payload is unavailable, so direct-route restriction and retained-grid connectivity cannot be classified.",
                    snapshot,
                    role="limit",
                ),
            )

    if disposition == "insufficient":
        if (
            isinstance(reference, dict)
            and reference.get("status") == "completed"
            and isinstance(route, dict)
            and route.get("has_lethal_cell") is not True
        ):
            snapshot = measurements["costmap_snapshot_sha256"]
            _append(
                packet,
                _measurement_unit(
                    "negative-route-cell",
                    "The incomplete retained grid contained no observed blocked direct-route cell.",
                    snapshot,
                    role="limit",
                ),
            )
        plan_count = measurements.get("delivered_plan_count")
        minimum = measurements.get("all_plans_minimum_signed_lateral_deviation")
        maximum = measurements.get("all_plans_maximum_signed_lateral_deviation")
        if plan_count is not None and minimum is not None and maximum is not None:
            _append(
                packet,
                _measurement_unit(
                    "plan-geometry",
                    (
                        f"All {int(plan_count['value'])} delivered plans spanned "
                        f"{float(minimum['value']):.3f} to {float(maximum['value']):.3f} m signed "
                        "lateral deviation from the requested line."
                    ),
                    plan_count,
                    minimum,
                    maximum,
                ),
            )
        action = measurements["action_status"]
        _append(
            packet,
            _measurement_unit(
                "cause-limit",
                "The retained evidence does not establish obstacle identity, global no-path, exact Nav2 consumption, or geometry-to-outcome causation.",
                action,
                role="limit",
            ),
        )
    return packet
