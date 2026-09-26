#!/usr/bin/env python3
"""Compile one validated command--motion export into a finite-composition packet."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


PACKET_SCHEMA = "crane-diagnostic-predicate-packet/v1"
ADAPTER_VERSION = "command-motion-composition-adapter-v1"
ALLOWED_DISPOSITIONS = {"supported", "not_triggered", "insufficient"}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _measurement_map(result: dict[str, Any]) -> dict[str, dict[str, Any]]:
    measurements = result.get("measurements")
    if not isinstance(measurements, list):
        raise ValueError("diagnostic result has no measurement list")
    indexed: dict[str, dict[str, Any]] = {}
    for item in measurements:
        identifier = item.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in indexed:
            raise ValueError("diagnostic measurement IDs are invalid or repeated")
        indexed[identifier] = item
    return indexed


def _evidence_ids(*measurements: dict[str, Any]) -> list[str]:
    identifiers: set[str] = set()
    for item in measurements:
        values = item.get("evidence_ids", [])
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError(f"measurement {item.get('id')} has invalid evidence IDs")
        identifiers.update(values)
    return sorted(identifiers)


def _format_number(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"expected numeric measurement, got {value!r}")
    return f"{value:.6g}"


def _interval(item: dict[str, Any]) -> str:
    value = item.get("interval_s")
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"measurement {item.get('id')} has no bounded interval")
    return f"{_format_number(value[0])}--{_format_number(value[1])} s"


def _unit(
    unit_id: str,
    role: str,
    text: str,
    evidence_ids: list[str],
    *,
    always_include: bool = False,
) -> dict[str, Any]:
    value: dict[str, Any] = {
        "unit_id": unit_id,
        "role": role,
        "text": text,
        "evidence_ids": evidence_ids,
    }
    if always_include:
        value["always_include"] = True
    return value


def _observation(predicate: str, value: bool, measurements: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "predicate": predicate,
        "value": value,
        "evidence_ids": _evidence_ids(*measurements),
    }


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    """Return a fail-closed packet without inventing unavailable measurements."""
    if document.get("visibility") != "robot_visible":
        raise ValueError("adapter requires a robot-visible diagnostic export")
    result = document.get("diagnostic_result")
    if not isinstance(result, dict):
        raise ValueError("export has no diagnostic result")
    if result.get("computation_version") != "command-motion-discrepancy-v3":
        raise ValueError("unsupported command--motion computation version")
    disposition = result.get("disposition")
    if disposition not in ALLOWED_DISPOSITIONS:
        raise ValueError(f"unsupported command--motion disposition: {disposition}")
    episode_id = result.get("episode_id")
    if not isinstance(episode_id, str) or episode_id != document.get("episode_id"):
        raise ValueError("diagnostic/export episode IDs do not match")

    measurements = _measurement_map(result)
    action = measurements.get("action_status")
    if action is None or action.get("value") not in {"succeeded", "aborted"}:
        raise ValueError("command--motion export lacks a supported action status")
    action_value = action["value"]
    observations = [
        _observation("action_succeeded", action_value == "succeeded", [action]),
        _observation("action_aborted", action_value == "aborted", [action]),
    ]
    answer_units: list[dict[str, Any]] = []

    diagnosis = result.get("diagnosis")
    failure_chain = result.get("failure_chain")
    limits = result.get("limits")
    next_check = result.get("next_check")
    if any(not isinstance(value, str) or not value.strip() for value in (diagnosis, failure_chain, limits, next_check)):
        raise ValueError("diagnostic answer fields are incomplete")

    execution = document.get("method_input", {}).get("execution_sequence")
    failures = measurements.get("follow_path_failures")
    recoveries = measurements.get("source_qualified_wait_recoveries")
    if not isinstance(execution, dict) or failures is None or recoveries is None:
        raise ValueError("command--motion export lacks a structured execution sequence")
    attempt_count = execution.get("follow_path_attempt_count")
    if (
        not isinstance(attempt_count, int)
        or isinstance(attempt_count, bool)
        or failures.get("value") != execution.get("follow_path_failure_count")
        or recoveries.get("value") != execution.get("source_qualified_wait_recovery_count")
    ):
        raise ValueError("structured execution sequence and measurements disagree")
    execution_evidence = _evidence_ids(action, failures, recoveries)
    execution_text = (
        f"The recorded action {action_value} after {attempt_count} FollowPath attempts, "
        f"{failures['value']} FollowPath failures, and {recoveries['value']} "
        "source-qualified Wait invocations."
    )

    if disposition == "supported":
        healthy = measurements.get("calibrated_healthy_planar_speed")
        commanded = measurements.get("discrepancy_commanded_planar_speed")
        measured = measurements.get("discrepancy_measured_planar_speed")
        duration = measurements.get("sustained_discrepancy_duration")
        if any(item is None for item in (healthy, commanded, measured, duration)):
            raise ValueError("supported command--motion result lacks decisive measurements")
        decisive = [healthy, commanded, measured, duration]
        observations.extend(
            [
                _observation("command_motion_supported", True, decisive),
                _observation("command_motion_not_triggered", False, decisive),
                _observation("command_motion_evidence_insufficient", False, decisive),
            ]
        )
        diagnosis = (
            "The retained delivered-command and measured-motion streams establish a sustained "
            f"command-to-motion discrepancy: median command {_format_number(commanded['value'])} "
            f"{commanded.get('unit')} and median measured speed {_format_number(measured['value'])} "
            f"{measured.get('unit')} during {_interval(measured)}."
        )
        limits = (
            "The discrepancy is supported, but the evidence does not uniquely identify actuator "
            "rejection, mobility constraint, collision, obstruction, slip, or another physical cause. "
            "Delivered commands do not prove actuator acceptance, and delivered odometry does not "
            "prove Nav2 consumption."
        )
        answer_units.extend(
            [
                _unit(
                    "healthy-comparator",
                    "evidence",
                    (
                        "The calibrated healthy measured planar-speed median was "
                        f"{_format_number(healthy['value'])} {healthy.get('unit')} during {_interval(healthy)}."
                    ),
                    _evidence_ids(healthy),
                    always_include=True,
                ),
                _unit(
                    "discrepancy-comparison",
                    "diagnosis",
                    diagnosis,
                    _evidence_ids(*decisive),
                ),
                _unit(
                    "cause-limit",
                    "limit",
                    limits,
                    _evidence_ids(*decisive),
                    always_include=True,
                ),
            ]
        )
        recovered = measurements.get("recovered_measured_planar_speed")
        recovered_ratio = measurements.get("recovered_response_ratio")
        if (recovered is None) != (recovered_ratio is None):
            raise ValueError("recovered response measurements are incomplete")
        if recovered is not None and recovered_ratio is not None:
            recovery_evidence = [recovered, recovered_ratio]
            observations.append(_observation("response_recovered", True, recovery_evidence))
            answer_units.extend(
                [
                    _unit(
                        "response-recovery",
                        "evidence",
                        (
                            "Measured response later recovered to "
                            f"{_format_number(recovered['value'])} {recovered.get('unit')} during "
                            f"{_interval(recovered)} ({_format_number(recovered_ratio['value'])} of the "
                            "calibrated healthy response)."
                        ),
                        _evidence_ids(*recovery_evidence),
                    ),
                    _unit(
                        "task-outcome",
                        "outcome",
                        f"The recorded navigation action {action_value}.",
                        _evidence_ids(action),
                    ),
                ]
            )
        else:
            observations.append(_observation("response_recovered", False, decisive))
    elif disposition == "not_triggered":
        healthy = measurements.get("calibrated_healthy_planar_speed")
        commanded = measurements.get("calibrated_healthy_commanded_planar_speed")
        if healthy is None or commanded is None:
            raise ValueError("not-triggered result lacks its healthy comparison")
        comparison = [healthy, commanded, action]
        observations.extend(
            [
                _observation("command_motion_supported", False, comparison),
                _observation("command_motion_not_triggered", True, comparison),
                _observation("command_motion_evidence_insufficient", False, comparison),
                _observation("response_recovered", False, comparison),
            ]
        )
        diagnosis = (
            "The declared command-to-motion diagnostic did not trigger: the retained streams did "
            "not contain the required consecutive low-response windows after healthy calibration."
        )
        limits = (
            "This bounded negative result does not prove that every transient control difficulty was "
            "absent."
        )
        answer_units.extend(
            [
                _unit("nominal-comparison", "diagnosis", diagnosis, _evidence_ids(*comparison)),
                _unit(
                    "false-premise-rejection",
                    "limit",
                    "The retained evidence does not support the question's command-to-motion-failure premise.",
                    _evidence_ids(*comparison),
                ),
                _unit("retained-execution", "execution", execution_text, execution_evidence, always_include=True),
                _unit("insufficiency-limit", "limit", limits, _evidence_ids(*comparison), always_include=True),
            ]
        )
    else:
        command_count = measurements.get("delivered_command_sample_count")
        odometry_count = measurements.get("independent_odometry_sample_count")
        if command_count is None or odometry_count is None:
            raise ValueError("insufficient result lacks evidence-completeness measurements")
        completeness = [command_count, odometry_count]
        observations.append(_observation("command_motion_evidence_insufficient", True, completeness))
        diagnosis = (
            "The command-to-motion discrepancy cannot be assessed because the missing delivered "
            "odometry stream prevents a time-aligned command-response chain."
        )
        limits = (
            "The missing measured-motion stream prevents a time-aligned comparison; the execution "
            "sequence alone does not establish a command-to-motion discrepancy or unique physical cause."
        )
        answer_units.extend(
            [
                _unit("insufficiency-diagnosis", "diagnosis", diagnosis, _evidence_ids(*completeness)),
                _unit("retained-execution", "execution", execution_text, execution_evidence),
                _unit("insufficiency-limit", "limit", limits, _evidence_ids(*completeness)),
            ]
        )

    # These units retain useful execution context and a discriminating next check without
    # changing which mechanism is selected.
    if not any(item["unit_id"] == "retained-execution" for item in answer_units):
        answer_units.append(
            _unit("retained-execution", "execution", execution_text, execution_evidence, always_include=True)
        )
    answer_units.append(
        _unit("next-check", "limit", f"Next check: {next_check}", [], always_include=True)
    )

    return {
        "schema": PACKET_SCHEMA,
        "packet_id": f"{episode_id}:command-motion-composition-v1",
        "adapter_version": ADAPTER_VERSION,
        "applicable_mechanism_ids": [
            "measured_response_recovery",
            "command_to_motion_discrepancy",
            "command_motion_evidence_insufficient",
            "nominal_command_motion",
        ],
        "source": {
            "episode_id": episode_id,
            "diagnostic_id": result.get("diagnostic_id"),
            "computation_version": result.get("computation_version"),
            "sha256": source_sha256,
        },
        "observations": observations,
        "answer_units": answer_units,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.diagnostic.read_bytes()
    document = json.loads(raw)
    packet = build(document, source_sha256=_sha256(raw))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
