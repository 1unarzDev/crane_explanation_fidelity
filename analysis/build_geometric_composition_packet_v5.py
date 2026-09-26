#!/usr/bin/env python3
"""Correct masked-cell wording while preserving the coverage-complete v4 packet."""

from __future__ import annotations

from typing import Any

from build_geometric_composition_packet_v4 import (
    _evidence_ids,
    _measurement_map,
    build as build_v4,
)


ADAPTER_VERSION = "land-geometric-composition-adapter-v5"


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    packet = build_v4(document, source_sha256=source_sha256)
    packet["adapter_version"] = ADAPTER_VERSION
    packet["packet_id"] = packet["packet_id"].replace("composition-v4", "composition-v5")
    result = document["diagnostic_result"]
    reference = document.get("reference_computation")
    if not (
        result.get("disposition") == "supported"
        and result.get("mechanism") == "recorded_plan_change_with_unresolved_physical_trigger"
        and isinstance(reference, dict)
        and reference.get("status") in {
            "insufficient",
            "not_run_missing_costmap_cell_payload",
        }
    ):
        return packet
    missing = reference.get("missing")
    if missing not in (["costmap_cells"], ["latestCostmapSnapshot.data"]):
        raise ValueError("masked geometry has an unexpected missing-evidence declaration")

    measurements = _measurement_map(result)
    required = (
        "delivered_plan_count",
        "first_plan_maximum_lateral_deviation",
        "all_plans_minimum_signed_lateral_deviation",
        "all_plans_maximum_signed_lateral_deviation",
        "action_status",
        "costmap_snapshot_sha256",
    )
    if any(name not in measurements for name in required):
        raise ValueError("masked route-change packet lacks decisive path or outcome measurements")
    values = [measurements[name] for name in required]
    count, first, minimum, maximum, action, _snapshot = values
    if action.get("value") != "succeeded":
        raise ValueError("masked route-change correction only supports the retained success case")
    unit = next(
        (item for item in packet["answer_units"] if item["unit_id"] == "path-comparison"),
        None,
    )
    if unit is None:
        raise ValueError("masked route-change packet has no path-comparison unit")
    unit["text"] = (
        "The retained navigation record shows a successful route change: the first delivered "
        f"plan was direct ({float(first['value']):.3f} m maximum lateral deviation), while all "
        f"{int(count['value'])} delivered plans spanned {float(minimum['value']):.3f} to "
        f"{float(maximum['value']):.3f} m signed lateral deviation. The costmap cell payload is "
        "unavailable, so the physical trigger cannot be classified. The action succeeded."
    )
    unit["evidence_ids"] = _evidence_ids(*values)
    return packet
