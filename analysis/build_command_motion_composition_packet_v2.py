#!/usr/bin/env python3
"""Add measurement-complete language units to the validated command-motion adapter."""

from __future__ import annotations

from typing import Any

from build_command_motion_composition_packet import (
    _evidence_ids,
    _format_number,
    _interval,
    _measurement_map,
    _unit,
    build as build_v1,
)


ADAPTER_VERSION = "command-motion-composition-adapter-v2"


def _append(packet: dict[str, Any], item: dict[str, Any]) -> None:
    if any(existing["unit_id"] == item["unit_id"] for existing in packet["answer_units"]):
        raise ValueError(f"duplicate v2 answer unit: {item['unit_id']}")
    packet["answer_units"].append(item)


def build(document: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    packet = build_v1(document, source_sha256=source_sha256)
    packet["adapter_version"] = ADAPTER_VERSION
    packet["packet_id"] = packet["packet_id"].replace("composition-v1", "composition-v2")
    result = document["diagnostic_result"]
    measurements = _measurement_map(result)
    disposition = result["disposition"]
    execution = document["method_input"]["execution_sequence"]
    attempts = execution["follow_path_attempt_count"]
    failures = execution["follow_path_failure_count"]
    recoveries = execution["source_qualified_wait_recovery_count"]
    execution_unit = next(
        item for item in packet["answer_units"] if item["unit_id"] == "retained-execution"
    )
    execution_unit["text"] = (
        f"The recorded action {measurements['action_status']['value']} after {attempts} FollowPath "
        f"{'attempt' if attempts == 1 else 'attempts'}, {failures} FollowPath "
        f"{'failure' if failures == 1 else 'failures'}, and {recoveries} source-qualified Wait "
        f"{'invocation' if recoveries == 1 else 'invocations'}."
    )

    if disposition == "supported" and "recovered_measured_planar_speed" in measurements:
        recovered = measurements["recovered_measured_planar_speed"]
        recoveries = measurements["source_qualified_wait_recoveries"]
        _append(
            packet,
            _unit(
                "recovery-causation-limit",
                "limit",
                "The recorded ordering does not establish that a Wait invocation caused the measured response to recover.",
                _evidence_ids(recovered, recoveries),
            ),
        )
    elif disposition == "not_triggered":
        commanded = measurements["calibrated_healthy_commanded_planar_speed"]
        measured = measurements["calibrated_healthy_planar_speed"]
        _append(
            packet,
            _unit(
                "healthy-comparator",
                "evidence",
                (
                    f"During {_interval(measured)}, the healthy comparator had median command "
                    f"{_format_number(commanded['value'])} {commanded.get('unit')} and median "
                    f"measured speed {_format_number(measured['value'])} {measured.get('unit')}."
                ),
                _evidence_ids(commanded, measured),
            ),
        )
    elif disposition == "insufficient":
        commands = measurements["delivered_command_sample_count"]
        odometry = measurements["independent_odometry_sample_count"]
        _append(
            packet,
            _unit(
                "evidence-completeness",
                "evidence",
                (
                    f"The retained record contains {commands['value']} delivered command samples "
                    f"and {odometry['value']} independent odometry samples."
                ),
                _evidence_ids(commands, odometry),
            ),
        )
    return packet
