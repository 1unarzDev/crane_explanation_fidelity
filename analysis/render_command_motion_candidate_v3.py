#!/usr/bin/env python3
"""Render a complete, causally bounded command-motion explanation."""

from __future__ import annotations

from typing import Any


def _measurements(export: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = export["diagnostic_result"]["measurements"]
    result = {item["id"]: item for item in items}
    if len(result) != len(items):
        raise ValueError("duplicate diagnostic measurement ID")
    return result


def _interval(item: dict[str, Any]) -> str:
    start, end = item["interval_s"]
    return f"{start:.1f}--{end:.1f} s"


def render(export: dict[str, Any]) -> str:
    if export.get("visibility") != "robot_visible":
        raise ValueError("candidate v3 requires robot-visible evidence")
    diagnostic = export["diagnostic_result"]
    if diagnostic.get("computation_version") != "command-motion-discrepancy-v3":
        raise ValueError("candidate v3 requires command-motion-discrepancy-v3")
    measurements = _measurements(export)
    method = export["method_input"]
    sequence = method["execution_sequence"]
    status = method["action_status"].lower()
    attempts = int(sequence["follow_path_attempt_count"])
    failures = int(sequence["follow_path_failure_count"])
    recoveries = int(sequence["source_qualified_wait_recovery_count"])
    evidence_ids = ", ".join(sorted(diagnostic["supporting_evidence"]))
    disposition = diagnostic["disposition"]

    if disposition == "supported":
        healthy = measurements["calibrated_healthy_planar_speed"]
        command = measurements["discrepancy_commanded_planar_speed"]
        motion = measurements["discrepancy_measured_planar_speed"]
        diagnosis = (
            "The retained streams establish a sustained command-to-motion discrepancy: during "
            f"{_interval(motion)}, the median delivered command was {command['value']:.3f} m/s "
            f"while median delivered odometry was {motion['value']:.3f} m/s."
        )
        facts = [
            f"healthy comparator {_interval(healthy)} at {healthy['value']:.4f} m/s",
            f"discrepancy comparison {_interval(motion)} at {command['value']:.3f} versus {motion['value']:.3f} m/s",
        ]
        recovered = measurements.get("recovered_measured_planar_speed")
        if recovered is not None:
            facts.append(
                f"later measured-response window {_interval(recovered)} at {recovered['value']:.4f} m/s"
            )
        mechanism_limit = (
            "The evidence establishes the discrepancy, but not actuator acceptance, Nav2 "
            "consumption of the delivered odometry, or a unique cause such as actuator rejection, "
            "mobility constraint, collision or obstruction, or slip."
        )
        next_check = (
            "Record downstream accepted actuation or actuator feedback together with contact, "
            f"clearance, and wheel-motion evidence during {_interval(motion)}."
        )
    elif disposition == "not_triggered":
        healthy = measurements["calibrated_healthy_planar_speed"]
        diagnosis = (
            "The declared computation did not establish a sustained command-to-motion "
            "discrepancy. Because the navigation action succeeded, the retained evidence does not "
            "support the premise that such a discrepancy prevented eventual continuation."
        )
        facts = [f"healthy comparator {_interval(healthy)} at {healthy['value']:.4f} m/s"]
        mechanism_limit = (
            "This negative result is limited to the retained synchronized interval and declared "
            "thresholds; it does not prove every transient execution difficulty was absent. "
            "Delivered commands do not prove actuator acceptance, and delivered odometry does not "
            "prove Nav2 consumption."
        )
        next_check = "Retain the same synchronized streams if a later navigation action fails."
    elif disposition == "insufficient":
        command_count = measurements["delivered_command_sample_count"]["value"]
        odometry_count = measurements["independent_odometry_sample_count"]["value"]
        diagnosis = (
            "A command-to-motion discrepancy cannot be assessed because the retained evidence "
            "contains no delivered odometry samples for a time-aligned motion comparison."
        )
        facts = [f"{command_count} delivered command samples", f"{odometry_count} delivered odometry samples"]
        mechanism_limit = (
            "The execution sequence alone does not establish a command-to-motion discrepancy or "
            "a unique physical cause; delivered commands also do not prove actuator acceptance."
        )
        next_check = "Record synchronized delivered commands and measured planar odometry."
    else:
        raise ValueError(f"unsupported diagnostic disposition: {disposition}")

    facts.extend(
        [
            f"action status {status}",
            f"{attempts} FollowPath attempts",
            f"{failures} FollowPath failures",
            f"{recoveries} source-qualified Wait invocations",
        ]
    )
    failure_chain = (
        f"The same goal-scoped record contains {attempts} FollowPath attempts, {failures} failures, "
        f"{recoveries} source-qualified Wait invocations, and an action status of {status}. These "
        "counts do not by themselves establish that the discrepancy caused those execution events "
        "or establish their ordering relative to the diagnostic interval."
    )
    return "\n".join(
        (
            f"Diagnosis: {diagnosis}",
            f"Decisive evidence: {'; '.join(facts)}. Evidence IDs: {evidence_ids}.",
            f"Failure chain: {failure_chain}",
            f"Limits and next check: {mechanism_limit} Next check: {next_check}",
        )
    )
