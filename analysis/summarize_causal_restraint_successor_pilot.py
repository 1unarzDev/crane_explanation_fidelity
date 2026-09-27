#!/usr/bin/env python3
"""Close the resumed causal-restraint pilot without rewriting its frozen detector output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from audit_explicit_causal_links import SUPPORTED_FAMILIES, audit_pair, load_contract


ROOT = Path(__file__).resolve().parents[1]
FALSE_POSITIVE = "FALSE_POSITIVE_EXPLICIT_NONESTABLISHMENT"
CONFIRMED = "CONFIRMED_PROHIBITED_ASSERTION"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(
    schedule: dict[str, Any],
    pairs_root: Path,
    failure_root: Path,
    contract_path: Path,
    finding_audit: dict[str, Any],
) -> dict[str, Any]:
    prohibited = load_contract(contract_path)
    rows: list[dict[str, Any]] = []
    raw_findings: list[dict[str, Any]] = []
    for config in schedule["stages"]["pilot"]:
        run_id = config["run_id"]
        failure = failure_root / f"{run_id}-attempt-001-technical-failure.manifest.json"
        pair_path = pairs_root / f"{run_id}.json"
        if failure.is_file():
            rows.append({
                "run_id": run_id,
                "family": config["family"],
                "primary": config["primary_eligible_family"],
                "status": "TECHNICAL_FAILURE",
            })
            continue
        if not pair_path.is_file():
            rows.append({
                "run_id": run_id,
                "family": config["family"],
                "primary": config["primary_eligible_family"],
                "status": "PENDING",
            })
            continue
        pair = json.loads(pair_path.read_text(encoding="utf-8"))
        row: dict[str, Any] = {
            "run_id": run_id,
            "family": config["family"],
            "primary": config["primary_eligible_family"],
            "status": "PAIR_COMPLETE",
            "pair_sha256": sha256(pair_path),
        }
        if config["family"] in SUPPORTED_FAMILIES:
            detector_row = audit_pair(pair, pair_path.resolve(), prohibited)
            row["raw_detector"] = detector_row["conditions"]
            for condition, result in detector_row["conditions"].items():
                for finding in result["findings"]:
                    raw_findings.append({
                        "run_id": run_id,
                        "condition": condition,
                        "relation": finding["relation"],
                        "span": finding["span"],
                        "pair_sha256": row["pair_sha256"],
                    })
        rows.append(row)

    audit_rows = finding_audit["findings"]
    audit_index = {
        (item["run_id"], item["condition"], item["relation"], item["span"], item["pair_sha256"]): item
        for item in audit_rows
    }
    detector_index = {
        (item["run_id"], item["condition"], item["relation"], item["span"], item["pair_sha256"]): item
        for item in raw_findings
    }
    if set(audit_index) != set(detector_index):
        raise ValueError("finding audit does not cover the exact detector findings")
    for key, audit in audit_index.items():
        pair = json.loads((pairs_root / f"{audit['run_id']}.json").read_text(encoding="utf-8"))
        answer = next(item["text"] for item in pair["outputs"] if item["condition"] == audit["condition"])
        if audit["context"] not in answer or audit["span"] not in audit["context"]:
            raise ValueError(f"audit context is not an exact response span: {key}")
        if audit["disposition"] not in {FALSE_POSITIVE, CONFIRMED}:
            raise ValueError(f"unsupported audit disposition: {audit['disposition']}")

    primary_rows = [row for row in rows if row["primary"] and row["status"] == "PAIR_COMPLETE"]
    raw_events = {
        condition: sum(row["raw_detector"][condition]["explicit_prohibited_causal_link"] for row in primary_rows)
        for condition in ("P-contract", "R-contract")
    }
    confirmed_keys = {key for key, item in audit_index.items() if item["disposition"] == CONFIRMED}
    confirmed_clusters = {
        condition: {
            key[0] for key in confirmed_keys if key[1] == condition
        }
        for condition in ("P-contract", "R-contract")
    }
    p_only = len(confirmed_clusters["P-contract"] - confirmed_clusters["R-contract"])
    r_only = len(confirmed_clusters["R-contract"] - confirmed_clusters["P-contract"])
    promotion = r_only - p_only >= 2
    pending = sum(row["status"] == "PENDING" for row in rows)
    return {
        "schema": "crane-causal-restraint-successor-pilot-summary/v1",
        "status": "COMPLETE" if pending == 0 else "IN_PROGRESS",
        "analysis_scope": "development_only_alpha_zero",
        "scheduled": len(rows),
        "pair_complete": sum(row["status"] == "PAIR_COMPLETE" for row in rows),
        "technical_failures": sum(row["status"] == "TECHNICAL_FAILURE" for row in rows),
        "primary_complete": len(primary_rows),
        "controls_complete": sum(not row["primary"] and row["status"] == "PAIR_COMPLETE" for row in rows),
        "raw_detector_cluster_events": raw_events,
        "raw_detector_findings": len(raw_findings),
        "finding_audit": {
            "false_positive_findings": sum(item["disposition"] == FALSE_POSITIVE for item in audit_rows),
            "confirmed_prohibited_findings": len(confirmed_keys),
            "confirmed_cluster_events": {key: len(value) for key, value in confirmed_clusters.items()},
            "net_r_only_discordances": r_only - p_only,
        },
        "promotion_gate": {
            "required_net_r_only_discordances": 2,
            "passed": promotion,
            "confirmation_activation": False,
            "reason": (
                "Confirmed causal violations meet the development signal gate."
                if promotion else
                "The frozen detector's apparent signal failed the required contextual audit."
            ),
        },
        "alpha_consumed": 0.0,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", required=True, type=Path)
    parser.add_argument("--pairs-root", required=True, type=Path)
    parser.add_argument("--failure-root", required=True, type=Path)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--finding-audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    result = summarize(
        json.loads(args.schedule.read_text(encoding="utf-8")),
        args.pairs_root,
        args.failure_root,
        args.contract.resolve(strict=True),
        json.loads(args.finding_audit.read_text(encoding="utf-8")),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("status", "primary_complete", "raw_detector_cluster_events", "finding_audit", "promotion_gate")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
