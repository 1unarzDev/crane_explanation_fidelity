#!/usr/bin/env python3
"""Bind the existing terminal-margin export to one frozen prospective RoboBoat row.

The diagnostic computation remains in ``export_terminal_margin_diagnostic``.  This narrow adapter
only verifies the prospective registry identity and replaces the development disposition; it does
not expose the independent docking evaluator or hidden simulator state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from export_terminal_margin_diagnostic import build_export


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / (
    "research/explanation_fidelity/experiment_configs/prospective/"
    "roboboat-diagnostic-external-validity-v1-narrow-freeze.json"
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(payload: dict, configuration_id: str, summary_path: Path) -> dict:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = {
        item["configuration_id"]: item for item in registry["ordered_configurations"]
    }
    if registry.get("status") != "NARROW_ARM_FROZEN" or configuration_id not in rows:
        raise ValueError("configuration is not in the frozen narrow arm")
    row = rows[configuration_id]
    if payload["source"]["fixture_summary_sha256"] != digest(summary_path):
        raise ValueError("prospective fixture hash differs after export")
    result = dict(payload)
    result.update(
        {
            "schema": "crane-roboboat-prospective-robot-visible-evidence/v1",
            "study_status": "PROSPECTIVE_EXTERNAL_VALIDITY_ARM",
            "arm_id": registry["arm_id"],
            "configuration_id": configuration_id,
            "cluster_id": row["cluster_id"],
            "question_id": row["question_id"],
            "registry_sha256": digest(REGISTRY),
            "independent_physical_configuration": True,
            "land_n_added": 0,
            "land_alpha_consumed": 0.0,
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration-id", required=True)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--config-repository", required=True, type=Path)
    parser.add_argument("--config-commit", required=True)
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--task-tolerance-m", required=True, type=float)
    parser.add_argument("--source-reference", required=True)
    parser.add_argument("--mask", action="append", default=[])
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    payload = build_export(
        args.summary,
        args.config_repository,
        args.config_commit,
        args.config_path,
        args.task_tolerance_m,
        args.source_reference,
        frozenset(args.mask),
    )
    result = bind(payload, args.configuration_id, args.summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
