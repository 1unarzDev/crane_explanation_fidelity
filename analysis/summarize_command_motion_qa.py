#!/usr/bin/env python3
"""Build an evaluator-only QA summary for a command-motion development export."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(export_path: Path, reference_path: Path) -> dict[str, Any]:
    export = json.loads(export_path.read_text(encoding="utf-8"))
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    if export.get("schema") != "crane-command-motion-diagnostic-export-v1":
        raise ValueError("unsupported method export schema")
    if reference.get("schema") != "crane-command-motion-independent-reference/v1":
        raise ValueError("unsupported independent reference schema")
    measurements = {
        item["id"]: item["value"] for item in export["diagnostic_result"]["measurements"]
    }
    ref = reference["result"]
    parity = {
        "disposition": export["diagnostic_result"]["disposition"] == ref["disposition"],
        "healthy_measured_planar_speed_mps": abs(
            float(measurements["calibrated_healthy_planar_speed"])
            - float(ref["healthy_measured_planar_speed_mps"])
        )
        < 1e-12,
        "follow_path_failure_count": int(measurements["follow_path_failures"])
        == int(ref["follow_path_failure_count"])
        if "follow_path_failures" in measurements
        else int(ref["follow_path_failure_count"]) == 0,
        "source_qualified_wait_recovery_count": int(
            measurements["source_qualified_wait_recoveries"]
        )
        == int(ref["source_qualified_wait_recovery_count"])
        if "source_qualified_wait_recoveries" in measurements
        else int(ref["source_qualified_wait_recovery_count"]) == 0,
    }
    if ref["disposition"] == "supported":
        parity.update(
            {
                "discrepancy_commanded_planar_speed_mps": abs(
                    float(measurements["discrepancy_commanded_planar_speed"])
                    - float(ref["discrepancy_commanded_planar_speed_mps"])
                )
                < 1e-12,
                "discrepancy_measured_planar_speed_mps": abs(
                    float(measurements["discrepancy_measured_planar_speed"])
                    - float(ref["discrepancy_measured_planar_speed_mps"])
                )
                < 1e-12,
            }
        )
    else:
        parity["discrepancy_commanded_planar_speed_mps"] = (
            ref["discrepancy_commanded_planar_speed_mps"] is None
            and "discrepancy_commanded_planar_speed" not in measurements
        )
        parity["discrepancy_measured_planar_speed_mps"] = (
            ref["discrepancy_measured_planar_speed_mps"] is None
            and "discrepancy_measured_planar_speed" not in measurements
        )
    serialized = json.dumps(export, sort_keys=True).lower()
    leakage_tokens = {
        token: token in serialized
        for token in (
            "instrumentation-held",
            "mobility hold",
            "persistent hold",
            "mobilityhold",
            "evaluator_only",
        )
    }
    checks = {
        "method_export_is_robot_visible": export.get("visibility") == "robot_visible",
        "final_text_verification_accepted": export.get("final_text_verification", {}).get(
            "accepted"
        )
        is True,
        "independent_reference_does_not_import_proposed_core": reference.get(
            "implementation_independence", {}
        ).get("imports_proposed_diagnostic_core")
        is False,
        "all_reference_values_match": all(parity.values()),
        "no_evaluator_intervention_token_in_method_export": not any(leakage_tokens.values()),
        "source_hashes_present": all(
            len(str(export["source"].get(key, ""))) == 64
            for key in (
                "events_sha256",
                "runtime_manifest_sha256",
                "bt_policy_sha256",
                "nav2_config_sha256",
            )
        ),
    }
    return {
        "schema": "crane-command-motion-development-qa/v1",
        "status": (
            "VALID_DEVELOPMENT_INSTRUMENTATION_QUALIFICATION_NOT_INDEPENDENT_SCENARIO"
            if all(checks.values())
            else "FAILED_QA"
        ),
        "episode_id": export["episode_id"],
        "method_export_sha256": sha256(export_path),
        "independent_reference_sha256": sha256(reference_path),
        "checks": checks,
        "reference_parity": parity,
        "leakage_token_audit": leakage_tokens,
        "sample_counts": reference["sample_counts"],
        "supported_interval_s": ref["interval_s"],
        "limitations": [
            "This rerun qualifies instrumentation and is not an independent scenario cluster.",
            "The independent computation is a separate implementation, not a human label.",
            (
                "The supported discrepancy does not identify its unique physical cause."
                if ref["disposition"] == "supported"
                else "The negative result applies only to the retained interval and declared development thresholds."
            ),
            "Only the blind robot-visible export may be supplied to explanation methods; acquisition metadata and evaluator truth remain outside the method input.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    payload = summarize(args.export, args.reference)
    if payload["status"] == "FAILED_QA":
        raise RuntimeError("command-motion development artifact failed QA")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
