#!/usr/bin/env python3
"""Build the post-hoc transport-corrected N=24 focused-look sensitivity analysis."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

from focused_sequential_monitor import (
    DEFAULT_LEDGER,
    DEFAULT_PROTOCOL,
    DEFAULT_RESOURCE_FREEZE,
    analyze,
    sha256_path,
)
from repair_luna_opaque_ids import atomic_write, load_json, sha256_path as digest


def load_reconciliations(original_root: Path, repair_root: Path) -> list[dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for path in sorted(original_root.glob("*.json")):
        value = load_json(path)
        if value.get("schema") != "crane-focused-cluster-reconciliation/v1":
            continue
        values[value["cluster_id"]] = value
    repaired = 0
    for path in sorted(repair_root.glob("*/reconciliation.json")):
        value = load_json(path)
        if value.get("schema") != "crane-focused-cluster-reconciliation-transport-correction/v1":
            raise ValueError("unexpected corrected reconciliation schema")
        if value.get("status") != "POST_HOC_TRANSPORT_CORRECTED_NOT_ORIGINAL_REGISTERED_RELEASE":
            raise ValueError("corrected reconciliation has an unsafe status")
        values[value["cluster_id"]] = value
        repaired += 1
    if repaired != 2:
        raise ValueError("the N=24 correction requires exactly the two primary failed clusters")
    return list(values.values())


def payload_for_mode(
    reconciliations: list[dict[str, Any]], mode: str, eligible_n: int
) -> dict[str, Any]:
    ordered = sorted(
        (value["rows"][mode] for value in reconciliations),
        key=lambda row: (row["sequence_index"], row["configuration_id"]),
    )
    selected = [row for row in ordered if row.get("primary_endpoint_eligible") is True][:eligible_n]
    if len(selected) != eligible_n:
        raise ValueError("corrected reconciliation inventory does not reach the requested look")
    rows: list[dict[str, Any]] = []
    for analysis_index, row in enumerate(selected, start=1):
        item = copy.deepcopy(row)
        item["source_sequence_index"] = item["sequence_index"]
        item["sequence_index"] = analysis_index
        rows.append(item)
    if rows[-1]["configuration_id"] != "cm-land-conf-068":
        raise ValueError("corrected first look does not end at the frozen ordered-prefix boundary")
    required_repairs = {"cm-land-conf-062", "cm-land-conf-067"}
    if not required_repairs <= {row["configuration_id"] for row in rows}:
        raise ValueError("corrected first look omitted a frozen-prefix transport failure")
    return {
        "schema": "crane-focused-supported-diagnostic-results/v1",
        "campaign_id": "focused-supported-diagnostic-communication-v1-confirmation",
        "protocol_id": "focused-supported-diagnostic-communication-v1",
        "protocol_sha256": sha256_path(DEFAULT_PROTOCOL),
        "resource_freeze_sha256": sha256_path(DEFAULT_RESOURCE_FREEZE),
        "development_or_legacy_data_included": False,
        "sampling_rule_changed_after_outcomes": False,
        "judge": {
            "qualification_id": "luna-model-judge-v12-complete-endpoint-extension-v1",
            "two_isolated_passes": True,
        },
        "analysis_scope": "post_hoc_opaque_id_transport_correction_sensitivity",
        "original_registered_release_claimed": False,
        "sensitivity_mode": mode,
        "clusters": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original-reconciliations", required=True, type=Path)
    parser.add_argument("--repair-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--eligible-n", type=int, default=24)
    args = parser.parse_args()
    reconciliations = load_reconciliations(
        args.original_reconciliations.resolve(strict=True),
        args.repair_root.resolve(strict=True),
    )
    protocol = load_json(DEFAULT_PROTOCOL)
    ledger = load_json(DEFAULT_LEDGER)
    freeze = load_json(DEFAULT_RESOURCE_FREEZE)
    summary: dict[str, Any] = {
        "schema": "crane-focused-transport-corrected-look-summary/v1",
        "status": "POST_HOC_SENSITIVITY_NOT_ORIGINAL_REGISTERED_RELEASE",
        "registered_claim_allowed": False,
        "reason": (
            "Five complete judgments were corrected only at the opaque transport ID after the "
            "frozen no-retry calls; the original call records remain invalid and immutable."
        ),
        "eligible_n": args.eligible_n,
        "modes": {},
    }
    for mode in ("least_favourable", "most_favourable"):
        payload = payload_for_mode(reconciliations, mode, args.eligible_n)
        input_path = args.output_root / f"input-{mode}.json"
        atomic_write(input_path, payload)
        result = analyze(payload, protocol, ledger, freeze)
        result.update({
            "analysis_scope": payload["analysis_scope"],
            "original_registered_release_claimed": False,
            "input_sha256": digest(input_path),
        })
        result_path = args.output_root / f"monitor-{mode}.json"
        atomic_write(result_path, result)
        summary["modes"][mode] = {
            "input_path": str(input_path),
            "input_sha256": digest(input_path),
            "result_path": str(result_path),
            "result_sha256": digest(result_path),
            "monitor_status": result["status"],
            "allowed_conclusion_under_math_only": result["allowed_conclusion"],
        }
    atomic_write(args.output_root / "summary.json", summary)
    print(json.dumps({"status": summary["status"], "eligible_n": args.eligible_n}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
