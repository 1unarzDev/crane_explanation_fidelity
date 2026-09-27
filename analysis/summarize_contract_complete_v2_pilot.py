#!/usr/bin/env python3
"""Summarize the frozen contract-complete v2 development pilot.

This is descriptive development analysis (alpha=0).  It preserves both Luna passes and
maps pass disagreement adversely/favourably to P for bounded sensitivity analysis.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _condition_bounds(values: list[bool | None], *, favourable: bool) -> tuple[int, int]:
    numeric = [int(value) for value in values if value is not None]
    if len(numeric) == 2 and numeric[0] == numeric[1]:
        return numeric[0], numeric[0]
    # Missing or discordant repeated measurements span both possible assignments.
    return (0, 1) if favourable else (0, 1)


def _claim_assignments(report: dict[str, Any], claim: str) -> dict[str, int]:
    passes = [report["passes"][pass_id] for pass_id in ("pass-1", "pass-2")]
    if claim == "A":
        field = "claim_a_complete_supported_communication"
        p_values = [item["P"].get(field) for item in passes]
        r_values = [item["R"].get(field) for item in passes]
        p_low, p_high = _condition_bounds(p_values, favourable=True)
        r_low, r_high = _condition_bounds(r_values, favourable=False)
        return {"least_p": p_low, "least_r": r_high, "most_p": p_high, "most_r": r_low}
    if claim == "B":
        field = "claim_b_substantive_assertion_error"
        p_values = [item["P"].get(field) for item in passes]
        r_values = [item["R"].get(field) for item in passes]
        p_low, p_high = _condition_bounds(p_values, favourable=False)
        r_low, r_high = _condition_bounds(r_values, favourable=True)
        # Express the risk-reduction claim as reliability (= 1 - error), allowing the
        # shared P-minus-R effect calculation to equal R-error minus P-error.
        return {
            "least_p": 1 - p_high, "least_r": 1 - r_low,
            "most_p": 1 - p_low, "most_r": 1 - r_high,
        }
    raise ValueError(f"unknown claim: {claim}")


def _effect(rows: list[dict[str, int]], mode: str) -> dict[str, Any]:
    differences = [row[f"{mode}_p"] - row[f"{mode}_r"] for row in rows]
    p_only = sum(value == 1 for value in differences)
    r_only = sum(value == -1 for value in differences)
    return {
        "n": len(rows),
        "effect_p_minus_r": sum(differences) / len(rows) if rows else None,
        "p_only_favourable": p_only,
        "r_only_favourable": r_only,
        "net_p_favourable_discordances": p_only - r_only,
        "ties": sum(value == 0 for value in differences),
    }


def summarize(schedule: dict[str, Any], result_root: Path, failure_root: Path) -> dict[str, Any]:
    primary: dict[str, list[dict[str, int]]] = {"A": [], "B": []}
    rows: list[dict[str, Any]] = []
    unresolved_fields: Counter[str] = Counter()
    for config in schedule["configurations"]:
        run_id = config["run_id"]
        result_path = result_root / run_id / "development-summary.json"
        failure_path = failure_root / f"{run_id}-attempt-001-technical-failure.manifest.json"
        row: dict[str, Any] = {
            "order": config["order"], "run_id": run_id, "family": config["family"],
            "primary_endpoint_eligible": config["primary_eligible_family"],
        }
        if failure_path.is_file():
            row["status"] = "TECHNICAL_FAILURE"
        elif not result_path.is_file():
            row["status"] = "PENDING"
        else:
            report = json.loads(result_path.read_text(encoding="utf-8"))
            if report.get("status") != "DEVELOPMENT_ONLY_COMPLETE":
                row["status"] = report.get("status", "INVALID_RESULT")
            else:
                row["status"] = "RECONCILED_TWO_PASS"
                row["claims"] = {
                    claim: _claim_assignments(report, claim) for claim in ("A", "B")
                }
                for pass_id in ("pass-1", "pass-2"):
                    for condition in ("P", "R"):
                        endpoint = report["passes"][pass_id][condition]
                        for field in endpoint.get("unresolved_fields", []):
                            unresolved_fields[f"{condition}:{field}"] += 1
                if config["primary_eligible_family"]:
                    for claim in ("A", "B"):
                        primary[claim].append(row["claims"][claim])
        rows.append(row)

    claims = {}
    for claim, claim_rows in primary.items():
        claims[claim] = {
            "least_favourable": _effect(claim_rows, "least"),
            "most_favourable": _effect(claim_rows, "most"),
        }
    minimum_signal = any(
        claims[claim]["least_favourable"]["net_p_favourable_discordances"] >= 2
        for claim in ("A", "B")
    )
    statuses = Counter(row["status"] for row in rows)
    return {
        "schema": "crane-contract-complete-v2-pilot-summary/v1",
        "status": "COMPLETE" if statuses["PENDING"] == 0 else "IN_PROGRESS",
        "analysis_scope": "development_only_alpha_zero",
        "scheduled_configurations": len(rows),
        "status_counts": dict(sorted(statuses.items())),
        "primary_reconciled_n": sum(
            row["status"] == "RECONCILED_TWO_PASS" and row["primary_endpoint_eligible"]
            for row in rows
        ),
        "control_reconciled_n": sum(
            row["status"] == "RECONCILED_TWO_PASS" and not row["primary_endpoint_eligible"]
            for row in rows
        ),
        "claims": claims,
        "unresolved_field_counts": dict(sorted(unresolved_fields.items())),
        "minimum_signal_gate": {
            "rule": "at least two net P-favourable discordances for either claim under least-favourable two-pass mapping",
            "passed": minimum_signal,
            "sufficient_for_confirmation_activation": False,
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--result-root", required=True, type=Path)
    parser.add_argument("--failure-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = summarize(
        json.loads(args.schedule.read_text(encoding="utf-8")),
        args.result_root, args.failure_root,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("status", "primary_reconciled_n", "control_reconciled_n")}))


if __name__ == "__main__":
    main()
