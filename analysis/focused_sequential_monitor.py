#!/usr/bin/env python3
"""Fail-closed monitor for focused supported diagnostic communication.

This campaign deliberately does not reuse the broader v2 decision rule.  It reuses the validated
bounded paired-difference confidence-sequence implementation, while making complete supported
diagnostic communication the sole confirmatory endpoint.  Secondary tradeoffs are reported and
never silently promoted to confirmatory gates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from sequential_diagnostic_monitor import lower_confidence_bound, upper_confidence_bound


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROTOCOL = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1.json"
)
DEFAULT_LEDGER = ROOT / "manifests/study/diagnostic-sequential-error-ledger-v2.json"
DEFAULT_RESOURCE_FREEZE = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "focused-supported-diagnostic-communication-v1-resource-freeze.json"
)
SCHEMA = "crane-focused-supported-diagnostic-results/v1"
BETTING_FRACTIONS = (
    0.005, 0.01, 0.02, 0.04, 0.08, 0.12, 0.18, 0.25, 0.33,
    0.42, 0.5, 0.6, 0.7, 0.8, 0.9, 0.97, 0.99,
)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _binary(row: dict[str, Any], field: str) -> int:
    value = row.get(field)
    if value not in {0, 1} or isinstance(value, bool):
        raise ValueError(f"{field} must be binary")
    return int(value)


def _allocation(ledger: dict[str, Any], allocation_id: str) -> dict[str, Any]:
    matches = [x for x in ledger.get("allocations", []) if x.get("allocation_id") == allocation_id]
    if len(matches) != 1:
        raise ValueError("focused alpha allocation is missing or duplicated")
    return matches[0]


def validate_inputs(
    payload: dict[str, Any], protocol: dict[str, Any], ledger: dict[str, Any], freeze: dict[str, Any]
) -> list[dict[str, Any]]:
    if payload.get("schema") != SCHEMA:
        raise ValueError("unsupported focused result schema")
    if payload.get("campaign_id") != "focused-supported-diagnostic-communication-v1-confirmation":
        raise ValueError("unexpected focused campaign ID")
    if payload.get("protocol_id") != protocol.get("protocol_id"):
        raise ValueError("focused protocol ID mismatch")
    if payload.get("protocol_sha256") != sha256_path(DEFAULT_PROTOCOL):
        raise ValueError("focused protocol hash mismatch")
    if payload.get("resource_freeze_sha256") != sha256_path(DEFAULT_RESOURCE_FREEZE):
        raise ValueError("focused resource-freeze hash mismatch")
    if freeze.get("status") != "FROZEN_BEFORE_CONFIRMATORY_RESPONSE":
        raise ValueError("focused resources are not frozen")
    if payload.get("development_or_legacy_data_included") is not False:
        raise ValueError("development or legacy data cannot enter focused confirmation")
    if payload.get("sampling_rule_changed_after_outcomes") is not False:
        raise ValueError("outcome-adaptive sampling is prohibited")
    if payload.get("judge", {}).get("qualification_id") != (
        "luna-model-judge-v12-complete-endpoint-extension-v1"
    ):
        raise ValueError("focused endpoint requires the qualified Luna v12 extension")
    if payload.get("judge", {}).get("two_isolated_passes") is not True:
        raise ValueError("two isolated Luna passes are required")

    allocation_id = protocol["inference"]["discovery_allocation"]
    allocation = _allocation(ledger, allocation_id)
    rows = payload.get("clusters")
    if not isinstance(rows, list):
        raise ValueError("clusters must be a chronological list")
    if rows and (
        allocation.get("status") != "CONSUMED"
        or allocation.get("campaign_id") != payload["campaign_id"]
    ):
        raise ValueError("focused alpha must be atomically bound before outcomes")
    if not rows and allocation.get("status") not in {"AVAILABLE", "CONSUMED"}:
        raise ValueError("unknown focused allocation status")

    ids: set[str] = set()
    configurations: set[str] = set()
    primary_families = set(protocol["families"]["primary"])
    control_families = set(protocol["families"]["controls"])
    for index, row in enumerate(rows, start=1):
        if row.get("sequence_index") != index:
            raise ValueError("focused rows must remain in fixed chronological order")
        if row.get("independent_scenario_configuration") is not True:
            raise ValueError("only independent scenario configurations increment N")
        cluster_id = row.get("cluster_id")
        configuration_id = row.get("configuration_id")
        if not isinstance(cluster_id, str) or not cluster_id or cluster_id in ids:
            raise ValueError("focused cluster IDs must be unique and nonempty")
        if not isinstance(configuration_id, str) or not configuration_id or configuration_id in configurations:
            raise ValueError("focused configuration IDs must be unique and nonempty")
        ids.add(cluster_id)
        configurations.add(configuration_id)
        family = row.get("family")
        if family not in primary_families | control_families:
            raise ValueError("unknown focused family")
        eligible = row.get("primary_endpoint_eligible")
        if eligible is not (family in primary_families):
            raise ValueError("primary eligibility disagrees with the frozen family")
        for condition in ("p", "r"):
            _binary(row, f"complete_supported_diagnostic_communication_{condition}")
            _binary(row, f"material_error_{condition}")
            _binary(row, f"mechanism_correct_{condition}")
            _binary(row, f"measurement_correct_{condition}")
            _binary(row, f"causal_limit_preserved_{condition}")
            total = row.get("essential_unit_total")
            covered = row.get(f"essential_units_covered_{condition}")
            if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
                raise ValueError("essential_unit_total must be a positive integer")
            if not isinstance(covered, int) or isinstance(covered, bool) or not 0 <= covered <= total:
                raise ValueError("essential-unit coverage count is invalid")
            expected = int(
                row[f"mechanism_correct_{condition}"] == 1
                and row[f"measurement_correct_{condition}"] == 1
                and row[f"causal_limit_preserved_{condition}"] == 1
                and covered == total
                and row[f"material_error_{condition}"] == 0
            )
            if eligible and row[f"complete_supported_diagnostic_communication_{condition}"] != expected:
                raise ValueError("reported complete endpoint disagrees with component fields")
    if len(rows) > sum(protocol["families"]["fixed_discovery_counts"].values()):
        raise ValueError("focused campaign exceeds its frozen schedule")
    return rows


def analyze(
    payload: dict[str, Any], protocol: dict[str, Any], ledger: dict[str, Any], freeze: dict[str, Any]
) -> dict[str, Any]:
    rows = validate_inputs(payload, protocol, ledger, freeze)
    primary_rows = [row for row in rows if row["primary_endpoint_eligible"]]
    differences = [
        _binary(row, "complete_supported_diagnostic_communication_p")
        - _binary(row, "complete_supported_diagnostic_communication_r")
        for row in primary_rows
    ]
    alpha = float(protocol["inference"]["discovery_alpha"])
    estimate = sum(differences) / len(differences) if differences else None
    lower = lower_confidence_bound(differences, alpha, BETTING_FRACTIONS) if differences else -1.0
    upper = upper_confidence_bound(differences, alpha, BETTING_FRACTIONS) if differences else 1.0
    looks = protocol["inference"]["planned_eligible_cluster_looks"]
    at_registered_look = len(primary_rows) in looks
    represented = sorted({row["family"] for row in primary_rows})
    all_primary_families = sorted(protocol["families"]["primary"])
    representation_ready = represented == all_primary_families
    level_a = at_registered_look and representation_ready and lower > 0.0
    level_b = (
        at_registered_look
        and representation_ready
        and lower > float(protocol["inference"]["level_B_minimum_worthwhile_improvement"])
    )
    final = len(primary_rows) == int(protocol["inference"]["maximum_eligible_clusters"])
    futility = at_registered_look and upper <= 0.0
    status = "LEVEL_B" if level_b else "LEVEL_A" if level_a else "FUTILITY" if futility else "INCONCLUSIVE_FINAL" if final else "CONTINUE"

    def rate(field: str, selected: list[dict[str, Any]] = rows) -> float | None:
        return sum(_binary(row, field) for row in selected) / len(selected) if selected else None

    return {
        "schema": "crane-focused-supported-diagnostic-monitor/v1",
        "campaign_id": payload["campaign_id"],
        "status": status,
        "independent_configuration_count": len(rows),
        "primary_eligible_count": len(primary_rows),
        "represented_primary_families": represented,
        "registered_look": at_registered_look,
        "primary": {
            "endpoint": "complete_supported_diagnostic_communication",
            "p_rate": rate("complete_supported_diagnostic_communication_p", primary_rows),
            "r_rate": rate("complete_supported_diagnostic_communication_r", primary_rows),
            "paired_difference_estimate": estimate,
            "anytime_valid_lower_bound": lower,
            "anytime_valid_upper_bound": upper,
            "alpha": alpha,
            "level_A_positive_benefit": level_a,
            "level_B_exceeds_0_10": level_b,
        },
        "secondary_tradeoffs_not_level_A_gates": {
            "material_error_rate_p": rate("material_error_p"),
            "material_error_rate_r": rate("material_error_r"),
            "mean_essential_coverage_p": (
                sum(row["essential_units_covered_p"] / row["essential_unit_total"] for row in rows) / len(rows)
                if rows else None
            ),
            "mean_essential_coverage_r": (
                sum(row["essential_units_covered_r"] / row["essential_unit_total"] for row in rows) / len(rows)
                if rows else None
            ),
            "control_configuration_count": len(rows) - len(primary_rows),
        },
        "allowed_conclusion": (
            "focused_positive_benefit_and_practical_magnitude_established" if level_b
            else "focused_positive_benefit_established" if level_a
            else "focused_benefit_not_established"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--resource-freeze", type=Path, default=DEFAULT_RESOURCE_FREEZE)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    values = [json.loads(path.read_text(encoding="utf-8")) for path in (args.input, args.protocol, args.ledger, args.resource_freeze)]
    result = analyze(*values)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
