#!/usr/bin/env python3
"""Run two isolated Luna passes for the boat readiness canary and reconcile conservatively."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from luna_model_judge import atomic_write_json  # noqa: E402
from run_luna_single_diagnostic_packet import run as run_two_passes  # noqa: E402


BOAT_MANIFEST = ROOT / "manifests/annotation/luna-boat-diagnostic-heldout-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def qualified_boat_release() -> dict[str, str]:
    manifest = json.loads(BOAT_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "HELDOUT_QUALIFIED" or manifest.get(
        "boat_study_scoring_allowed"
    ) is not True:
        raise ValueError("boat-specific Luna extension is not qualified")
    freeze = ROOT / manifest["freeze"]["path"]
    result = ROOT / manifest["result"]["path"]
    if digest(freeze) != manifest["freeze"]["sha256"]:
        raise ValueError("boat judge freeze differs from qualified release")
    if digest(result) != manifest["result"]["sha256"]:
        raise ValueError("boat judge qualification result differs from manifest")
    retained = json.loads(result.read_text(encoding="utf-8"))
    if retained.get("boat_study_scoring_allowed") is not True:
        raise ValueError("retained boat qualification did not authorize scoring")
    return {
        "manifest_sha256": digest(BOAT_MANIFEST),
        "freeze_sha256": digest(freeze),
        "qualification_result_sha256": digest(result),
    }


def reconcile(report: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "supported_diagnostic_success",
        "material_error",
        "mechanism_identification",
    )
    resolved: dict[str, dict[str, Any]] = {}
    unresolved: dict[str, list[str]] = {}
    for condition in report["conditions"]:
        first = report["passes"]["pass-1"][condition]
        second = report["passes"]["pass-2"][condition]
        if first["judgment_status"] != "valid" or second["judgment_status"] != "valid":
            unresolved[condition] = ["technical_failure"]
            continue
        differences = [field for field in fields if first[field] != second[field]]
        if differences:
            unresolved[condition] = differences
        else:
            resolved[condition] = {field: first[field] for field in fields}
    return {
        "schema": "crane-boat-readiness-luna-reconciliation/v1",
        "status": "RECONCILED" if not unresolved else "RECONCILED_WITH_UNRESOLVED_FIELDS",
        "policy": (
            "Two isolated passes are retained. Exact agreement is carried forward; disagreement "
            "is unresolved unless an independently checkable fact or predeclared rule settles it. "
            "No third Luna vote and no quality-driven retry are permitted."
        ),
        "resolved": resolved,
        "unresolved": unresolved,
        "confirmatory_alpha_consumed": 0.0,
        "prospective_boat_n_added": 0,
        "land_n_added": 0,
    }


def run(packet: Path, key: Path, output_root: Path) -> dict[str, Any]:
    boat_release = qualified_boat_release()
    report = run_two_passes(packet, key, output_root)
    reconciliation = reconcile(report)
    summary = {
        "schema": "crane-boat-readiness-luna-summary/v1",
        "status": (
            "DEVELOPMENT_CANARY_COMPLETE"
            if not report["call_failures"]
            else "DEVELOPMENT_CANARY_TECHNICAL_FAILURE"
        ),
        "boat_qualified_judge_release": boat_release,
        "land_qualified_judge_release": report["qualified_judge_release"],
        "two_isolated_passes": True,
        "planned_judgments": report["planned_judgments"],
        "valid_judgments": report["valid_judgments"],
        "call_failures": report["call_failures"],
        "reconciliation": reconciliation,
        "development_summary_sha256": digest(output_root / "development-summary.json"),
    }
    atomic_write_json(output_root / "boat-readiness-summary.json", summary)
    atomic_write_json(output_root / "reconciliation.json", reconciliation)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if (output / "boat-readiness-summary.json").exists():
        raise SystemExit("refusing to overwrite completed boat canary result")
    summary = run(args.packet.resolve(strict=True), args.key.resolve(strict=True), output)
    print(json.dumps({"status": summary["status"], "valid_judgments": summary["valid_judgments"]}))
    return 0 if not summary["call_failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
