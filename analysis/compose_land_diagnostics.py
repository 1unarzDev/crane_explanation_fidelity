#!/usr/bin/env python3
"""Compose one bounded land execution diagnosis with explicit unresolved alternatives."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _measurement(result: dict[str, Any], measurement_id: str) -> dict[str, Any]:
    matches = [
        item
        for item in result.get("measurements", ())
        if item.get("id") == measurement_id
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one diagnostic measurement: {measurement_id}")
    return matches[0]


def _render(plan: dict[str, Any]) -> str:
    evidence = "; ".join(
        f"{item['label']}={item['display']}" for item in plan["decisive_evidence"]
    )
    return (
        f"Diagnosis: {plan['diagnosis']}\n"
        f"Decisive evidence: {evidence}.\n"
        f"Failure chain: {plan['failure_chain']}\n"
        f"Limits and next check: {plan['limits']} Next check: {plan['next_check']}"
    )


def _verify(plan: dict[str, Any], final_answer: str) -> dict[str, Any]:
    expected = _render(plan)
    forbidden = (
        "the action aborted",
        "the action failed",
        "recovery was exhausted",
        "geometry caused",
        "an obstacle caused",
        "motor failure caused",
        "mobility hold",
        "evaluator intervention",
    )
    lowered = final_answer.lower()
    findings = [text for text in forbidden if text in lowered]
    required = (
        "command-to-motion discrepancy",
        "0.260 m/s",
        "0.000 m/s",
        "10.0--51.0 s",
        "no terminal result was observed",
        "Geometric evidence is insufficient",
        "eventual action outcome is unresolved",
    )
    missing = [text for text in required if text not in final_answer]
    return {
        "accepted": final_answer == expected and not findings and not missing,
        "policy": "exact-bounded-land-composition-v1",
        "forbidden_findings": findings,
        "missing_required_spans": missing,
    }


def compose(
    command_path: Path,
    geometry_path: Path,
    contract_path: Path,
) -> dict[str, Any]:
    command = json.loads(command_path.read_text(encoding="utf-8"))
    geometry = json.loads(geometry_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("schema") != "crane-land-diagnostic-composition-plan-development/v1":
        raise ValueError("unsupported composition contract schema")
    for label, payload in (("command", command), ("geometry", geometry)):
        if payload.get("visibility") != "robot_visible":
            raise ValueError(f"{label} diagnostic is not robot-visible")
    episode_id = str(command.get("episode_id"))
    if not episode_id or geometry.get("episode_id") != episode_id:
        raise ValueError("diagnostic episode IDs do not match")
    source = contract["source"]
    if episode_id != source["episode_id"]:
        raise ValueError("episode ID does not match the composition contract")
    if sha256(command_path) != source["command_motion_export_sha256"]:
        raise ValueError("command diagnostic hash does not match the composition contract")
    if sha256(geometry_path) != source["geometric_export_sha256"]:
        raise ValueError("geometric diagnostic hash does not match the composition contract")

    command_result = command["diagnostic_result"]
    geometry_result = geometry["diagnostic_result"]
    if (
        command_result.get("mechanism") != "command_to_motion_discrepancy"
        or command_result.get("disposition") != "supported"
    ):
        raise ValueError("composition requires a supported command-motion discrepancy")
    if (
        geometry_result.get("mechanism") != "geometric_route_restriction"
        or geometry_result.get("disposition") != "insufficient"
    ):
        raise ValueError("composition requires insufficient geometric evidence")
    command_input = command["method_input"]
    geometry_input = geometry["method_input"]
    if command_input.get("terminal_result_observed") is not False:
        raise ValueError("command diagnostic lacks explicit nonterminal cutoff semantics")
    if geometry_input.get("observation_cutoff", {}).get("terminal_result_observed") is not False:
        raise ValueError("geometric diagnostic lacks explicit nonterminal cutoff semantics")
    if command_input.get("action_status") != "remained active at the observation cutoff":
        raise ValueError("unexpected command diagnostic action status")
    direct_route = geometry.get("reference_computation", {}).get("direct_route", {})
    if direct_route.get("fully_covered") is not False:
        raise ValueError("composition requires an incompletely covered requested route")

    healthy = _measurement(command_result, "calibrated_healthy_planar_speed")
    commanded = _measurement(command_result, "discrepancy_commanded_planar_speed")
    measured = _measurement(command_result, "discrepancy_measured_planar_speed")
    duration = _measurement(command_result, "sustained_discrepancy_duration")
    if commanded.get("interval_s") != measured.get("interval_s") or commanded.get(
        "interval_s"
    ) != duration.get("interval_s"):
        raise ValueError("discrepancy measurement intervals do not match")
    interval = [float(value) for value in commanded["interval_s"]]
    sequence = command_input["execution_sequence"]
    failures = int(sequence["follow_path_failure_count"])
    recoveries = int(sequence["source_qualified_wait_recovery_count"])
    attempts = int(sequence["follow_path_attempt_count"])

    plan = {
        "schema": "crane-bounded-diagnostic-answer-plan/v1",
        "episode_id": episode_id,
        "primary_mechanism": "command_to_motion_discrepancy",
        "diagnosis": (
            "During the retained observation window, the robot had a sustained command-to-motion "
            f"discrepancy from {interval[0]:.1f}--{interval[1]:.1f} s: Nav2 continued publishing "
            f"a median {float(commanded['value']):.3f} m/s planar command while delivered odometry "
            f"recorded a median {float(measured['value']):.3f} m/s planar response."
        ),
        "decisive_evidence": [
            {
                "id": "calibrated_healthy_planar_speed",
                "label": "healthy measured response",
                "value": float(healthy["value"]),
                "unit": "m/s",
                "display": f"{float(healthy['value']):.5f} m/s",
                "interval_s": healthy["interval_s"],
            },
            {
                "id": "discrepancy_commanded_planar_speed",
                "label": "discrepancy command",
                "value": float(commanded["value"]),
                "unit": "m/s",
                "display": f"{float(commanded['value']):.3f} m/s",
                "interval_s": interval,
            },
            {
                "id": "discrepancy_measured_planar_speed",
                "label": "measured response",
                "value": float(measured["value"]),
                "unit": "m/s",
                "display": f"{float(measured['value']):.3f} m/s",
                "interval_s": interval,
            },
            {
                "id": "sustained_discrepancy_duration",
                "label": "discrepancy interval",
                "value": float(duration["value"]),
                "unit": "s",
                "display": f"{interval[0]:.1f}--{interval[1]:.1f} s ({float(duration['value']):.1f} s)",
                "interval_s": interval,
            },
        ],
        "failure_chain": (
            f"After the response loss, the retained pre-cutoff sequence contains {failures} "
            f"FollowPath failures, {recoveries} source-qualified Wait invocation, and {attempts} "
            "FollowPath attempts. The action remained active at the observation cutoff; no "
            "terminal result was observed."
        ),
        "competing_mechanisms": [
            {
                "mechanism": "geometric_route_restriction",
                "disposition": "insufficient",
                "reason": (
                    "The retained rolling grid does not cover the complete requested route, so "
                    "geometry cannot classify that route or explain the discrepancy."
                ),
            }
        ],
        "limits": (
            "Geometric evidence is insufficient to classify the complete requested route or "
            "explain the discrepancy, and the eventual action outcome is unresolved. Delivered "
            "commands do not prove actuator acceptance, delivered odometry does not prove Nav2 "
            "consumption, and the evidence does not identify a unique actuator, collision, "
            "obstruction, or slip cause."
        ),
        "next_check": (
            "Record downstream accepted actuation or actuator feedback together with contact, "
            "clearance, and wheel-motion evidence over the discrepancy interval."
        ),
        "source_diagnostics": {
            "command_motion_sha256": sha256(command_path),
            "geometric_sha256": sha256(geometry_path),
            "composition_contract_sha256": sha256(contract_path),
        },
    }
    final_answer = _render(plan)
    verification = _verify(plan, final_answer)
    if not verification["accepted"]:
        raise RuntimeError(f"bounded composition verification failed: {verification}")
    return {
        "schema": "crane-land-diagnostic-composition-export/v1",
        "episode_id": episode_id,
        "visibility": "robot_visible",
        "development_only": True,
        "answer_plan": plan,
        "final_answer": final_answer,
        "final_text_verification": verification,
        "evidence_boundary": {
            "included": [
                "checked robot-visible command-motion diagnostic",
                "checked robot-visible geometric diagnostic",
                "declared nonterminal observation boundaries",
            ],
            "excluded": [
                "evaluator intervention identity and timing",
                "eventual action outcome after the cutoff",
                "unique physical cause",
            ],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--command-motion", type=Path, required=True)
    parser.add_argument("--geometry", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = compose(args.command_motion, args.geometry, args.contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
