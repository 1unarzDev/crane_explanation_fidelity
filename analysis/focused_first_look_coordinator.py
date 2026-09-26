#!/usr/bin/env python3
"""Deterministic transport and two-pass sensitivity adapter for the focused campaign.

This module does not call a model and does not alter either response.  It closes the interface
between the frozen response-pair runner, annotation packet builder, Luna packet runner, and focused
monitor.  Disagreements are retained and mapped to least-/most-favourable endpoint assignments;
the least-favourable payload is the only one permitted to establish the focused claim.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from run_luna_single_diagnostic_packet import success


def decorate_pair(pair: dict[str, Any], reference: dict[str, Any], question_id: str) -> dict[str, Any]:
    if pair.get("schema") != "crane-focused-supported-diagnostic-response-pair/v1":
        raise ValueError("unexpected response-pair schema")
    if pair.get("episode_id") != reference.get("episode_id"):
        raise ValueError("pair/reference episode mismatch")
    if [item.get("condition") for item in pair.get("outputs", [])] != ["P", "R"]:
        raise ValueError("focused pair must preserve exact P/R inventory")
    result = copy.deepcopy(pair)
    result.update({
        "question_id": question_id,
        "question_kind": pair["family"],
        "provider": "mixed-deterministic-and-frozen-baseline",
        "model": "condition-specific",
        "permitted_evidence_identifiers": reference["allowed_evidence_identifiers"],
    })
    return result


def _judgment(
    report: dict[str, Any], pass_id: str, response_id: str, cache_root: Path
) -> dict[str, Any]:
    key = report["cache_keys"][pass_id].get(response_id)
    if not key:
        raise ValueError("missing Luna judgment is unresolved and cannot enter the monitor")
    record = json.loads((cache_root / pass_id / f"{key}.json").read_text(encoding="utf-8"))
    if record.get("status") != "VALID":
        raise ValueError("invalid Luna judgment cannot enter the monitor")
    return record["judgment"]


def _binary_pair(values: list[int], *, condition: str, mode: str, error: bool = False) -> tuple[int, bool]:
    if values[0] == values[1]:
        return values[0], False
    if mode not in {"least_favourable", "most_favourable"}:
        raise ValueError("unknown sensitivity mode")
    favourable = (condition == "P") != error
    value = int(favourable if mode == "most_favourable" else not favourable)
    return value, True


def cluster_rows(
    *, packet_rows: list[dict[str, Any]], key: dict[str, Any], report: dict[str, Any],
    cache_root: Path, cluster_id: str, configuration_id: str, family: str, sequence_index: int,
) -> dict[str, Any]:
    by_id = {row["response_id"]: row for row in packet_rows}
    ids = {item["condition"]: item["response_id"] for item in key["entries"]}
    if set(ids) != {"P", "R"} or set(ids.values()) != set(by_id):
        raise ValueError("packet/key condition inventory mismatch")
    rows: dict[str, dict[str, Any]] = {}
    unresolved: list[dict[str, str]] = []
    for mode in ("least_favourable", "most_favourable"):
        row: dict[str, Any] = {
            "cluster_id": cluster_id, "configuration_id": configuration_id,
            "sequence_index": sequence_index, "independent_scenario_configuration": True,
            "family": family, "primary_endpoint_eligible": True,
        }
        total = None
        for condition in ("P", "R"):
            packet_row = by_id[ids[condition]]
            judgments = [
                _judgment(report, pass_id, ids[condition], cache_root)
                for pass_id in ("pass-1", "pass-2")
            ]
            required_ids = packet_row["complete_endpoint_unit_ids"]
            total = len(required_ids)
            unit_maps = [{u["unit_id"]: u["status"] for u in j["required_units"]} for j in judgments]
            covered = [sum(m.get(uid) == "covered" for uid in required_ids) for m in unit_maps]
            endpoint = [int(bool(success(j, packet_row))) for j in judgments]
            material = [int(bool(j["material_error"])) for j in judgments]
            values: dict[str, tuple[list[int], bool]] = {
                "complete_supported_diagnostic_communication": (endpoint, False),
                "material_error": (material, True),
                "mechanism_correct": ([int(m.get(required_ids[0]) == "covered") for m in unit_maps], False),
                "measurement_correct": ([int(m.get(required_ids[1]) == "covered") for m in unit_maps], False),
                "causal_limit_preserved": ([int(m.get(required_ids[-1]) == "covered") for m in unit_maps], False),
            }
            chosen: dict[str, int] = {}
            for field, (pair_values, is_error) in values.items():
                value, disagreed = _binary_pair(pair_values, condition=condition, mode=mode, error=is_error)
                chosen[field] = value
                if disagreed and mode == "least_favourable":
                    unresolved.append({"condition": condition, "field": field})
            if covered[0] == covered[1]:
                coverage = covered[0]
            elif mode == "least_favourable":
                coverage = min(covered) if condition == "P" else max(covered)
            else:
                coverage = max(covered) if condition == "P" else min(covered)
            expected = int(
                chosen["mechanism_correct"] == 1 and chosen["measurement_correct"] == 1
                and chosen["causal_limit_preserved"] == 1 and coverage == total
                and chosen["material_error"] == 0
            )
            chosen["complete_supported_diagnostic_communication"] = expected
            suffix = condition.lower()
            for field, value in chosen.items():
                row[f"{field}_{suffix}"] = value
            row[f"essential_units_covered_{suffix}"] = coverage
        row["essential_unit_total"] = total
        rows[mode] = row
    return {"rows": rows, "unresolved": unresolved}
