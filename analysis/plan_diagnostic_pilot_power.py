#!/usr/bin/env python3
"""Build a predeclared, pilot-informed paired-power feasibility report.

The tool consumes only fully adjudicated/key-joined development rows. It uses one endpoint selected
before human labels per eligible statistical cluster, never counts masks or controls as independent,
and cannot lower the fixed smallest-practical-effect target from the small pilot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from plan_diagnostic_power import minimum_clusters


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def resolve_declared(path_value: str) -> Path:
    path = Path(path_value)
    return path.resolve(strict=True) if path.is_absolute() else (ROOT / path).resolve(strict=True)


def validate_selection(selection: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if selection.get("schema") != "crane-diagnostic-pilot-primary-endpoints/v1":
        raise ValueError("unsupported primary-endpoint selection schema")
    if selection.get("labels_inspected_when_declared") is not False:
        raise ValueError("selection does not attest pre-label declaration")
    inventory_path = resolve_declared(selection["annotation_inventory"])
    if digest(inventory_path) != selection["annotation_inventory_sha256"]:
        raise ValueError("annotation inventory hash differs from selection")
    design_path = resolve_declared(selection["design_sensitivity"])
    if digest(design_path) != selection["design_sensitivity_sha256"]:
        raise ValueError("design-sensitivity hash differs from selection")

    inventory = load_json(inventory_path)
    specifications = inventory.get("packets")
    if not isinstance(specifications, list):
        raise ValueError("annotation inventory has no packet list")
    by_name = {item["name"]: item for item in specifications}
    if len(by_name) != len(specifications):
        raise ValueError("annotation inventory repeats a packet name")
    selected = selection.get("selected")
    excluded = selection.get("excluded")
    if not isinstance(selected, list) or not selected:
        raise ValueError("selection has no primary endpoints")
    if not isinstance(excluded, list):
        raise ValueError("selection has no exclusion inventory")
    selected_names = [item.get("packet_name") for item in selected]
    excluded_names = [item.get("packet_name") for item in excluded]
    if len(selected_names) != len(set(selected_names)):
        raise ValueError("selection repeats a primary packet")
    if set(selected_names) & set(excluded_names):
        raise ValueError("a packet is both selected and excluded")
    if set(selected_names) | set(excluded_names) != set(by_name):
        raise ValueError("selected and excluded packets do not partition the inventory")

    clusters: set[str] = set()
    for item in selected:
        specification = by_name[item["packet_name"]]
        if item.get("statistical_cluster_id") != specification["statistical_cluster_id"]:
            raise ValueError(f"{item['packet_name']}: cluster differs from inventory")
        if item.get("evidence_variant") != specification["evidence_variant"]:
            raise ValueError(f"{item['packet_name']}: evidence variant differs from inventory")
        cluster = item["statistical_cluster_id"]
        if cluster in clusters:
            raise ValueError("selection contains more than one primary endpoint in a cluster")
        clusters.add(cluster)
    return selected, selection["planning_rule"]


def bounded_minimum(p_only: float, r_only: float, target: float) -> int | None:
    if p_only <= r_only:
        return None
    try:
        return minimum_clusters(p_only, r_only, target, maximum=5000)
    except ValueError:
        return None


def plan(rows: list[dict[str, Any]], selection: dict[str, Any]) -> dict[str, Any]:
    selected, rule = validate_selection(selection)
    endpoints: list[dict[str, Any]] = []
    missing: list[str] = []
    counts = {"both_success": 0, "p_only_success": 0, "r_only_success": 0, "neither_success": 0}

    for item in selected:
        subset = [
            row
            for row in rows
            if row.get("statistical_cluster_id") == item["statistical_cluster_id"]
            and row.get("evidence_variant") == item["evidence_variant"]
        ]
        if not subset:
            missing.append(item["packet_name"])
            continue
        by_condition = {row.get("condition"): row for row in subset}
        if len(by_condition) != len(subset) or set(by_condition) != {"R", "P", "T", "N"}:
            raise ValueError(f"{item['packet_name']}: endpoint is not exactly paired R/P/T/N")
        if not all(row.get("diagnosable") is True for row in subset):
            raise ValueError(f"{item['packet_name']}: primary endpoint is not diagnosable")
        r_success = by_condition["R"].get("supported_diagnostic_success")
        p_success = by_condition["P"].get("supported_diagnostic_success")
        if not isinstance(r_success, bool) or not isinstance(p_success, bool):
            raise ValueError(f"{item['packet_name']}: primary outcome is not boolean")
        if p_success and r_success:
            cell = "both_success"
        elif p_success:
            cell = "p_only_success"
        elif r_success:
            cell = "r_only_success"
        else:
            cell = "neither_success"
        counts[cell] += 1
        endpoints.append(
            {
                **item,
                "r_supported_diagnostic_success": r_success,
                "p_supported_diagnostic_success": p_success,
                "paired_cell": cell,
            }
        )

    total = len(endpoints)
    if total == 0:
        raise ValueError("no selected primary endpoint remains after quarantine")
    raw_p_only = counts["p_only_success"] / total
    raw_r_only = counts["r_only_success"] / total
    # Jeffreys prior over the four paired outcome cells contributes 0.5 to each cell.
    denominator = total + 2.0
    smooth_p_only = (counts["p_only_success"] + 0.5) / denominator
    smooth_r_only = (counts["r_only_success"] + 0.5) / denominator
    pilot_80 = bounded_minimum(smooth_p_only, smooth_r_only, 0.80)
    pilot_90 = bounded_minimum(smooth_p_only, smooth_r_only, 0.90)
    fixed_minimum = rule["fixed_design_minimum_clusters_for_80_percent_power"]
    recommended = max(fixed_minimum, pilot_80) if pilot_80 is not None else None
    direction = (
        "FAVORS_P" if counts["p_only_success"] > counts["r_only_success"]
        else "FAVORS_R" if counts["r_only_success"] > counts["p_only_success"]
        else "TIED"
    )
    return {
        "schema": "crane-diagnostic-pilot-power-feasibility/v1",
        "status": "DEVELOPMENT_ONLY_PILOT_INFORMED_NOT_CONFIRMATORY",
        "selected_endpoints_declared": len(selected),
        "selected_endpoints_analyzed": total,
        "selected_endpoints_missing_after_quarantine": missing,
        "paired_counts": counts,
        "raw_discordance": {
            "p_only_probability": raw_p_only,
            "r_only_probability": raw_r_only,
            "net_difference": raw_p_only - raw_r_only,
            "direction": direction,
        },
        "jeffreys_smoothed_four_cell_sensitivity": {
            "p_only_probability": smooth_p_only,
            "r_only_probability": smooth_r_only,
            "minimum_clusters_for_80_percent_power": pilot_80,
            "minimum_clusters_for_90_percent_power": pilot_90,
        },
        "fixed_smallest_practical_effect_design_minimum": fixed_minimum,
        "pilot_informed_minimum_not_below_fixed_design": recommended,
        "observed_direction_favors_p": direction == "FAVORS_P",
        "superiority_freeze_authorized": False,
        "endpoints": endpoints,
        "interpretation": (
            "Six or fewer adjudicated development clusters are unstable planning evidence. "
            "The pilot may increase the fixed target or show that a superiority freeze is not "
            "credible; it cannot lower the predeclared 92-cluster target. Missing endpoints are "
            "reported, never replaced after labels."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotations", required=True, type=Path)
    parser.add_argument("--selection", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    annotations = args.annotations.resolve(strict=True)
    selection_path = args.selection.resolve(strict=True)
    output = args.output.resolve()
    if output.exists():
        raise SystemExit("refusing to overwrite an existing power-feasibility report")
    try:
        result = plan(read_jsonl(annotations), load_json(selection_path))
    except ValueError as error:
        parser.error(str(error))
    result.update(
        {
            "annotations": str(annotations),
            "annotations_sha256": digest(annotations),
            "selection": str(selection_path),
            "selection_sha256": digest(selection_path),
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
