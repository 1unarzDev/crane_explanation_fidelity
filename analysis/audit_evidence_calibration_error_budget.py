#!/usr/bin/env python3
"""Validate the evidence-calibration redirect against the cumulative alpha ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(root: Path, item: dict[str, Any]) -> dict[str, Any]:
    path = root / item["path"]
    if sha256(path) != item["sha256"]:
        raise ValueError(f"source hash mismatch: {item['path']}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"source must be an object: {item['path']}")
    return value


def audit(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    if declaration.get("schema") != "crane-evidence-calibration-error-budget-audit/v1":
        raise ValueError("unsupported error-budget audit schema")
    ledger = _load(root, declaration["source_ledger"])
    redirect = _load(root, declaration["redirect_audit"])
    if ledger.get("schema") != "crane-diagnostic-error-ledger/v1":
        raise ValueError("unsupported cumulative ledger schema")
    allocations = {item["allocation_id"]: item for item in ledger["allocations"]}
    if len(allocations) != len(ledger["allocations"]):
        raise ValueError("duplicate cumulative allocation ID")
    declared = {item["allocation_id"]: item for item in declaration["immutable_disposition"]}
    if set(declared) != set(allocations):
        raise ValueError("audit does not cover every cumulative allocation")
    for allocation_id, actual in allocations.items():
        expected = declared[allocation_id]
        for field in ("role", "alpha", "status"):
            if expected[field] != actual[field]:
                raise ValueError(f"allocation mismatch: {allocation_id}.{field}")
    program_alpha = float(ledger["program_alpha"])
    total = sum(float(item["alpha"]) for item in allocations.values())
    consumed = sum(
        float(item["alpha"]) for item in allocations.values() if item["status"] == "CONSUMED"
    )
    available = sum(
        float(item["alpha"]) for item in allocations.values() if item["status"] == "AVAILABLE"
    )
    if abs(total - program_alpha) > 1e-12:
        raise ValueError("allocation total differs from program alpha")
    source = declaration["source_ledger"]
    for field, actual in (
        ("program_alpha", program_alpha),
        ("consumed_alpha", consumed),
        ("available_alpha", available),
    ):
        if abs(float(source[field]) - actual) > 1e-12:
            raise ValueError(f"declared ledger summary mismatch: {field}")
    boundary = declaration["prospective_boundary"]
    discovery = allocations[boundary["discovery_allocation_id"]]
    replication = allocations[boundary["replication_allocation_id"]]
    if discovery["role"] != "candidate" or discovery["status"] != "AVAILABLE":
        raise ValueError("discovery reserve is not available candidate alpha")
    if replication["role"] != "replication" or replication["status"] != "AVAILABLE":
        raise ValueError("replication reserve is not available replication alpha")
    if float(boundary["maximum_discovery_alpha"]) != float(discovery["alpha"]):
        raise ValueError("redirect discovery alpha exceeds or understates the available reserve")
    if float(boundary["reserved_replication_alpha"]) != float(replication["alpha"]):
        raise ValueError("redirect replication alpha differs from the protected reserve")
    if boundary["primary_confirmatory_endpoint_count"] != 1:
        raise ValueError("redirect must freeze exactly one primary confirmatory endpoint")
    redirect_budget = redirect.get("error_budget", {})
    if redirect_budget.get("source_sha256") != declaration["source_ledger"]["sha256"]:
        raise ValueError("redirect audit points to another cumulative ledger")
    if declaration.get("bound_by_this_audit") != 0.0:
        raise ValueError("pre-freeze audit must not bind alpha")
    if declaration.get("consumed_by_this_audit") != 0.0:
        raise ValueError("pre-freeze audit must not consume alpha")
    if declaration.get("confirmation_authorized") is not False:
        raise ValueError("pre-freeze audit must not authorize confirmation")
    return {
        "schema": "crane-evidence-calibration-error-budget-audit-result/v1",
        "audit_id": declaration["audit_id"],
        "status": "PASS_PROVISIONAL_UNBOUND",
        "program_alpha": program_alpha,
        "consumed_alpha": consumed,
        "maximum_discovery_alpha": float(discovery["alpha"]),
        "reserved_replication_alpha": float(replication["alpha"]),
        "confirmation_authorized": False,
        "confirmation_independent_n": declaration["confirmation_independent_n"],
        "replication_independent_n": declaration["replication_independent_n"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--declaration",
        type=Path,
        default=ROOT / "manifests/study/evidence-calibration-error-budget-audit-v1.json",
    )
    args = parser.parse_args()
    path = args.declaration if args.declaration.is_absolute() else ROOT / args.declaration
    try:
        result = audit(ROOT, json.loads(path.read_text(encoding="utf-8")))
    except (KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
