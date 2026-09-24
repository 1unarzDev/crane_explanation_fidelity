#!/usr/bin/env python3
"""Build a complete, independently checked command-motion annotation reference.

The output deliberately excludes the proposed method's answer plan and evaluator intervention.
It exposes the independent computation plus the bounded robot-visible provenance needed to judge
the final answer without converting packet omissions into method errors.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _same(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    if isinstance(left, (int, float)) and not isinstance(left, bool):
        return math.isclose(float(left), float(right), rel_tol=1e-9, abs_tol=1e-9)
    return left == right


def _measurement_map(export: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values = export["diagnostic_result"]["measurements"]
    result = {item["id"]: item for item in values}
    if len(result) != len(values):
        raise ValueError("candidate diagnostic contains duplicate measurement IDs")
    return result


def build_reference(
    export: dict[str, Any], independent: dict[str, Any], *, question_id: str
) -> dict[str, Any]:
    diagnostic = export.get("diagnostic_result", {})
    method = export.get("method_input", {})
    if export.get("visibility") != "robot_visible":
        raise ValueError("candidate evidence is not robot-visible")
    if diagnostic.get("computation_version") != "command-motion-discrepancy-v3":
        raise ValueError("candidate reference requires command-motion-discrepancy-v3")
    if independent.get("episode_id") != export.get("episode_id"):
        raise ValueError("independent reference episode mismatch")
    independence = independent.get("implementation_independence", {})
    if independence.get("imports_proposed_diagnostic_core") is not False or independence.get(
        "imports_proposed_exporter"
    ) is not False:
        raise ValueError("reference implementation is not independent")

    checks: dict[str, bool] = {
        "disposition": independent["result"]["disposition"] == diagnostic["disposition"],
        "command_sample_count": independent["sample_counts"]["command"]
        == len(method.get("command_samples") or []),
        "odometry_sample_count": independent["sample_counts"]["odometry"]
        == len(method.get("odometry_samples") or []),
        "action_status": independent["execution_basis"]["action_status"]
        == method["action_status"],
        "command_provenance": independent["robot_visible_provenance"]["command"]
        == method["command_provenance"],
        "odometry_provenance": independent["robot_visible_provenance"]["odometry"]
        == method["odometry_provenance"],
        "windowing": independent["windowing"] == method["windowing"],
        "recovery_classifier": independent["execution_basis"]["recovery_node_classifier"]
        == method["execution_sequence"]["recovery_node_classifier"],
    }
    measurements = _measurement_map(export)
    mappings = {
        "healthy_commanded_planar_speed_mps": "calibrated_healthy_commanded_planar_speed",
        "healthy_measured_planar_speed_mps": "calibrated_healthy_planar_speed",
        "discrepancy_commanded_planar_speed_mps": "discrepancy_commanded_planar_speed",
        "discrepancy_measured_planar_speed_mps": "discrepancy_measured_planar_speed",
        "response_ratio": "measured_response_ratio",
        "recovered_measured_planar_speed_mps": "recovered_measured_planar_speed",
        "recovered_response_ratio": "recovered_response_ratio",
        "follow_path_failure_count": "follow_path_failures",
        "source_qualified_wait_recovery_count": "source_qualified_wait_recoveries",
    }
    for reference_name, measurement_id in mappings.items():
        reference_value = independent["result"].get(reference_name)
        measurement = measurements.get(measurement_id)
        checks[f"measurement:{measurement_id}"] = (
            measurement is None if reference_value is None else measurement is not None
            and _same(reference_value, measurement["value"])
        )
    checks["action_status_measurement"] = _same(
        method["action_status"], measurements.get("action_status", {}).get("value")
    )
    interval = independent["result"].get("interval_s")
    discrepancy_measurement = measurements.get("discrepancy_measured_planar_speed")
    checks["discrepancy_interval"] = (
        discrepancy_measurement is None if interval is None else discrepancy_measurement is not None
        and discrepancy_measurement.get("interval_s") == interval
    )
    recovery_interval = independent["result"].get("response_recovery_interval_s")
    recovery_measurement = measurements.get("recovered_measured_planar_speed")
    checks["recovery_interval"] = (
        recovery_measurement is None if recovery_interval is None else recovery_measurement is not None
        and recovery_measurement.get("interval_s") == recovery_interval
    )

    source = export["source"]
    expected_ids = {
        f"events-sha256:{source['events_sha256']}",
        f"runtime-manifest-sha256:{source['runtime_manifest_sha256']}",
        f"bt-policy-sha256:{source['bt_policy_sha256']}",
        f"nav2-config-sha256:{source['nav2_config_sha256']}",
    }
    diagnostic_config_sha256 = source.get("diagnostic_config_sha256")
    if diagnostic_config_sha256 is not None:
        if not isinstance(diagnostic_config_sha256, str) or len(diagnostic_config_sha256) != 64:
            raise ValueError("diagnostic configuration hash is malformed")
        expected_ids.add(f"diagnostic-config-sha256:{diagnostic_config_sha256}")
    checks["evidence_identifier_set"] = set(diagnostic["supporting_evidence"]) == expected_ids
    failed = sorted(name for name, accepted in checks.items() if not accepted)
    if failed:
        raise ValueError("reference completeness checks failed: " + ", ".join(failed))

    result = independent["result"]
    units = [
        {"unit_id": "mechanism", "text": independent["allowed_conclusion"]},
        {
            "unit_id": "healthy-comparator",
            "text": (
                f"The calibrated healthy response spans {result['healthy_interval_s'][0]:.1f} to "
                f"{result['healthy_interval_s'][1]:.1f} s and has median measured speed "
                f"{result['healthy_measured_planar_speed_mps']:.4f} m/s."
                if result["healthy_interval_s"] is not None
                and result["healthy_measured_planar_speed_mps"] is not None
                else "The retained evidence does not establish a healthy-response comparator."
            ),
        },
        {
            "unit_id": "execution-sequence",
            "text": (
                f"The action status is {method['action_status']}; the retained sequence contains "
                f"{result['follow_path_failure_count']} FollowPath failures, "
                f"{result['source_qualified_wait_recovery_count']} source-qualified Wait "
                f"invocations, and {result['follow_path_attempt_count']} FollowPath attempts."
            ),
        },
        {
            "unit_id": "provenance-limit",
            "text": "Delivered command does not prove actuator acceptance, and delivered odometry does not prove Nav2 consumption.",
        },
        {
            "unit_id": "cause-limit",
            "text": "The evidence does not uniquely identify actuator rejection, mobility constraint, collision or obstruction, slip, or another execution-layer cause.",
        },
        {
            "unit_id": "next-check",
            "text": "The next discriminating check is downstream accepted actuation or actuator feedback together with contact, clearance, and wheel-motion evidence.",
        },
    ]
    if result["interval_s"] is not None:
        units.insert(
            2,
            {
                "unit_id": "discrepancy-comparison",
                "text": (
                    f"The earliest qualifying interval is {result['interval_s'][0]:.1f} to "
                    f"{result['interval_s'][1]:.1f} s, with median command "
                    f"{result['discrepancy_commanded_planar_speed_mps']:.3f} m/s and measured "
                    f"response {result['discrepancy_measured_planar_speed_mps']:.3f} m/s."
                ),
            },
        )
    if result["response_recovery_interval_s"] is not None:
        units.insert(
            3,
            {
                "unit_id": "measured-response-recovery",
                "text": (
                    f"Measured response recovered during {result['response_recovery_interval_s'][0]:.1f} "
                    f"to {result['response_recovery_interval_s'][1]:.1f} s to "
                    f"{result['recovered_measured_planar_speed_mps']:.4f} m/s."
                ),
            },
        )

    visible_independent = copy.deepcopy(independent)
    visible_independent["prohibited_conclusions"] = [
        "an unobserved intervention identity"
        if item == "the evaluator intervention identity"
        else item
        for item in visible_independent["prohibited_conclusions"]
    ]
    return {
        "schema": "crane-command-motion-annotation-reference/v2",
        "visibility": "robot_visible_reference",
        "reference_status": "DEVELOPMENT_PRE_MODEL_INDEPENDENT_REFERENCE_NOT_HUMAN_GOLD",
        "episode_id": export["episode_id"],
        "question_id": question_id,
        "diagnosable": result["disposition"] != "insufficient",
        "evidence_completeness": "The packet includes the complete independent computation, measurement intervals, stream provenance, thresholds, execution counts/status, classifier derivation, source identities, and declared limits needed for this command-motion question.",
        "required_units": units,
        "prohibited_claims": [
            (
                "an unobserved intervention identity"
                if item == "the evaluator intervention identity"
                else item
            )
            for item in independent["prohibited_conclusions"]
        ]
        + [
            "A Wait invocation or retry caused measured response recovery.",
            "The healthy comparator is an event-specific observation outside its retained interval.",
            "The command and odometry streams have an independence relationship not declared by the evidence.",
        ],
        "allowed_evidence_identifiers": sorted(expected_ids),
        "allowed_evidence": {
            "independent_computation": visible_independent,
            "robot_visible_source": source,
        },
        "completeness_audit": {"accepted": True, "checks": checks, "failed_checks": []},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--independent-reference", required=True, type=Path)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("refusing to overwrite existing reference")
    export = json.loads(args.export.read_text(encoding="utf-8"))
    independent = json.loads(args.independent_reference.read_text(encoding="utf-8"))
    result = build_reference(export, independent, question_id=args.question_id)
    result["inputs"] = {
        "robot_visible_export_sha256": digest(args.export),
        "independent_reference_sha256": digest(args.independent_reference),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
