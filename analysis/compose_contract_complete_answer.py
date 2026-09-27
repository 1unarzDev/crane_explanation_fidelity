#!/usr/bin/env python3
"""Compile one public M/Q/O/L question contract from robot-visible diagnostics.

This development candidate wraps the existing validated diagnostic adapters and finite composer.
It does not read evaluator references, filled gold units, hidden interventions, or method labels.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics
from typing import Any

from build_command_motion_composition_packet import _evidence_ids, _format_number, _interval, _measurement_map
from build_command_motion_composition_packet_v2 import build as build_command
from build_geometric_composition_packet_v5 import build as build_geometry
from compose_diagnostic_hypotheses_v2 import compose as compose_checked


SCHEMA = "crane-contract-complete-answer/v1"
VERSION = "p-contract-v2-development"
REGISTRY_SCHEMA = "crane-contract-complete-question-registry/v1"
REQUIRED_COMPONENTS = ["M", "Q", "O", "L"]
BLOCKED_COST_THRESHOLD = 253
EVIDENCE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*-sha256:[0-9a-f]{64}$")


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _question(registry: dict[str, Any], family: str) -> dict[str, Any]:
    if registry.get("schema") != REGISTRY_SCHEMA:
        raise ValueError("unsupported public question-contract registry")
    if registry.get("episode_specific_answers_present") is not False:
        raise ValueError("public question contract may not contain episode-specific answers")
    matches = [item for item in registry.get("questions", []) if item.get("family") == family]
    if len(matches) != 1:
        raise ValueError("question family is absent or duplicated")
    if matches[0].get("required_components") != REQUIRED_COMPONENTS:
        raise ValueError("question contract must require M/Q/O/L exactly once")
    return matches[0]


def _component(code: str, text: str, *measurements: dict[str, Any]) -> dict[str, Any]:
    evidence = _evidence_ids(*measurements)
    if not evidence:
        raise ValueError(f"contract component {code} has no governed evidence reference")
    return {"component": code, "text": text, "evidence_ids": evidence}


def _action(measurements: dict[str, dict[str, Any]]) -> tuple[dict[str, Any], str]:
    action = measurements.get("action_status")
    if action is None or action.get("value") not in {
        "succeeded", "aborted", "remained active at the observation cutoff"
    }:
        raise ValueError("contract answer lacks a bounded recorded action outcome")
    return action, str(action["value"])


def _recovered_command_measurement(
    document: dict[str, Any], recovered: dict[str, Any]
) -> dict[str, Any]:
    interval = recovered.get("interval_s")
    samples = document.get("method_input", {}).get("command_samples")
    if (
        not isinstance(interval, list)
        or len(interval) != 2
        or not isinstance(samples, list)
    ):
        raise ValueError("recovery contract lacks its command-comparison inputs")
    start, end = map(float, interval)
    values = [
        float(item["planar_speed_mps"])
        for item in samples
        if isinstance(item, dict)
        and isinstance(item.get("offset_s"), (int, float))
        and start <= float(item["offset_s"]) < end
        and isinstance(item.get("planar_speed_mps"), (int, float))
    ]
    if not values:
        raise ValueError("recovery interval has no delivered-command samples")
    return {
        "id": "recovered_commanded_planar_speed",
        "value": float(statistics.median(values)),
        "unit": "m/s",
        "interval_s": [start, end],
        "evidence_ids": list(recovered.get("evidence_ids", [])),
    }


def _command_components(
    document: dict[str, Any], family: str
) -> list[dict[str, Any]]:
    result = document["diagnostic_result"]
    measurements = _measurement_map(result)
    action, action_value = _action(measurements)
    disposition = result.get("disposition")

    if family in {"persistent_command_motion_discrepancy", "measured_response_recovery"}:
        if disposition != "supported":
            raise ValueError("diagnosable command contract requires a supported diagnostic result")
        names = (
            "calibrated_healthy_commanded_planar_speed",
            "calibrated_healthy_planar_speed",
            "discrepancy_commanded_planar_speed",
            "discrepancy_measured_planar_speed",
        )
        if any(name not in measurements for name in names):
            raise ValueError("supported command contract lacks its healthy/event comparison")
        healthy_command, healthy_measured, event_command, event_measured = (
            measurements[name] for name in names
        )
        if _interval(healthy_command) != _interval(healthy_measured):
            raise ValueError("healthy commanded/measured intervals disagree")
        if _interval(event_command) != _interval(event_measured):
            raise ValueError("event commanded/measured intervals disagree")
        comparison = (
            f"In the healthy {_interval(healthy_measured)} interval, the commanded median was "
            f"{_format_number(healthy_command['value'])} {healthy_command.get('unit')} and the "
            f"measured median was {_format_number(healthy_measured['value'])} "
            f"{healthy_measured.get('unit')}; in the event {_interval(event_measured)} interval, "
            f"the commanded median was {_format_number(event_command['value'])} "
            f"{event_command.get('unit')} and the measured median was "
            f"{_format_number(event_measured['value'])} {event_measured.get('unit')}."
        )
        if family == "persistent_command_motion_discrepancy":
            if "recovered_measured_planar_speed" in measurements:
                raise ValueError("persistent contract received a measured-recovery episode")
            return [
                _component(
                    "M",
                    "The retained streams support a persistent command-to-measured-motion discrepancy.",
                    event_command,
                    event_measured,
                ),
                _component(
                    "Q", comparison, healthy_command, healthy_measured, event_command, event_measured
                ),
                _component("O", f"The recorded navigation action {action_value}.", action),
                _component(
                    "L",
                    "The evidence does not uniquely identify actuator rejection, mobility constraint, collision, obstruction, slip, or another physical cause; delivered commands do not prove actuator acceptance, and delivered odometry does not prove Nav2 consumption.",
                    event_command,
                    event_measured,
                ),
            ]

        recovered = measurements.get("recovered_measured_planar_speed")
        ratio = measurements.get("recovered_response_ratio")
        waits = measurements.get("source_qualified_wait_recoveries")
        if recovered is None or ratio is None or waits is None:
            raise ValueError("recovery contract lacks measured recovery or Wait-order evidence")
        recovered_command = _recovered_command_measurement(document, recovered)
        comparison += (
            f" Measured response recovered in the recovery interval {_interval(recovered)}: "
            f"the commanded median was "
            f"{_format_number(recovered_command['value'])} {recovered_command.get('unit')} and "
            f"the measured median was {_format_number(recovered['value'])} "
            f"{recovered.get('unit')} "
            f"({_format_number(ratio['value'])} of the calibrated healthy response)."
        )
        return [
            _component(
                "M",
                "The initial command-to-measured-motion discrepancy was followed by measured response recovery.",
                event_command,
                event_measured,
                recovered,
            ),
            _component(
                "Q", comparison, healthy_command, healthy_measured, event_command, event_measured,
                recovered_command, recovered, ratio
            ),
            _component(
                "O",
                f"After that measured response recovery, the recorded navigation action {action_value}.",
                recovered,
                action,
            ),
            _component(
                "L",
                "The retained ordering does not establish that a Wait invocation caused the measured response recovery, and it does not establish that the measured response recovery caused the eventual action outcome; the original physical or actuator cause remains unresolved.",
                waits,
                recovered,
                action,
            ),
        ]

    if family == "nominal_false_premise_or_irrelevant_obstacle":
        if disposition != "not_triggered":
            raise ValueError("nominal contract requires a not-triggered diagnostic result")
        commanded = measurements["calibrated_healthy_commanded_planar_speed"]
        measured = measurements["calibrated_healthy_planar_speed"]
        return [
            _component("M", "The retained evidence does not support the alleged command-to-motion failure premise.", commanded, measured),
            _component("Q", f"During {_interval(measured)}, the commanded median was {_format_number(commanded['value'])} {commanded.get('unit')} and the measured median was {_format_number(measured['value'])} {measured.get('unit')}.", commanded, measured),
            _component("O", f"The recorded navigation action {action_value}.", action),
            _component("L", "This bounded negative result does not prove every transient difficulty absent, and obstacle visibility alone would not establish Nav2 consumption or obstacle causation.", commanded, measured),
        ]

    if family == "missing_decisive_or_ambiguous_evidence":
        if disposition != "insufficient":
            raise ValueError("missing-evidence contract requires an insufficient diagnostic result")
        commands = measurements["delivered_command_sample_count"]
        odometry = measurements["independent_odometry_sample_count"]
        return [
            _component("M", "A command-to-measured-motion mechanism cannot be established from the retained evidence.", commands, odometry),
            _component("Q", f"The record contains {int(commands['value'])} delivered command samples and {int(odometry['value'])} independent odometry samples; measured motion is the decisive missing discriminator.", commands, odometry),
            _component("O", f"The recorded navigation action {action_value}.", action),
            _component("L", "Without the missing measured-motion stream, command delivery cannot establish discrepancy, actuator acceptance, or a unique physical cause.", commands, odometry),
        ]
    raise ValueError("unsupported command question family")


def _geometry_components(document: dict[str, Any]) -> list[dict[str, Any]]:
    result = document["diagnostic_result"]
    measurements = _measurement_map(result)
    action, action_value = _action(measurements)
    reference = document.get("reference_computation")
    route = reference.get("direct_route") if isinstance(reference, dict) else None
    blocked = route.get("first_lethal_sample_from_start") if isinstance(route, dict) else None
    if not (
        result.get("disposition") == "supported"
        and isinstance(blocked, dict)
        and route.get("has_lethal_cell") is True
        and reference.get("connected_below_cost_253") is True
    ):
        raise ValueError("bounded geometry contract requires a supported restricted route and retained connection")
    cost = blocked.get("cost")
    if not isinstance(cost, int) or isinstance(cost, bool):
        raise ValueError("bounded geometry contract lacks an observed integer cell cost")
    if cost < BLOCKED_COST_THRESHOLD:
        raise ValueError("observed route-cell cost is below the non-traversable threshold")
    assumptions = result.get("assumptions", [])
    if not any("at or above 253" in str(value) for value in assumptions):
        raise ValueError("geometry result does not declare the applicable cost threshold")
    first_x = measurements["first_lethal_route_x"]
    snapshot = measurements["costmap_snapshot_sha256"]
    return [
        _component("M", "The retained navigation-model snapshot supports a bounded direct-route restriction while retaining a below-threshold connection to the goal.", first_x, snapshot),
        _component("Q", f"Near x={float(blocked['x']):.3f} m, the observed cell cost was {cost}, meeting the non-traversable threshold of {BLOCKED_COST_THRESHOLD}.", first_x, snapshot),
        _component("O", f"The recorded navigation action {action_value}.", action),
        _component("L", "The local snapshot does not establish global physical no-path, unique obstacle identity, exact Nav2 consumption, or that the retained geometry caused the outcome.", first_x, action),
    ]


def _render(components: list[dict[str, Any]]) -> str:
    titles = {"M": "Supported mechanism", "Q": "Decisive comparison", "O": "Recorded outcome", "L": "Necessary limitation"}
    return "\n\n".join(
        f"{titles[item['component']]} ({item['component']}):\n{item['text']}"
        for item in components
    )


def compile_answer(
    document: dict[str, Any], *, family: str, source_sha256: str,
    question_registry: dict[str, Any],
) -> dict[str, Any]:
    """Return a deterministic supported-and-complete answer for one public contract."""
    question = _question(question_registry, family)
    builder = build_geometry if family == "bounded_geometric_restriction" else build_command
    packet = builder(document, source_sha256=source_sha256)
    registry = json.loads(
        (Path(__file__).resolve().parents[1] / "configs/diagnostic_composition_registry_v1.json").read_text()
    )
    certificate = compose_checked(packet, registry)
    if certificate.get("status") != "composed" or certificate.get("answer_plan", {}).get("language_ready") is not True:
        raise ValueError("validated diagnostic composition is not language-ready")
    components = (
        _geometry_components(document)
        if family == "bounded_geometric_restriction"
        else _command_components(document, family)
    )
    present = [item["component"] for item in components]
    support_issues = [
        item["component"]
        for item in components
        if not item["text"].strip()
        or not item["evidence_ids"]
        or any(EVIDENCE_ID.fullmatch(value) is None for value in item["evidence_ids"])
    ]
    if support_issues:
        raise ValueError(f"contract answer has unsupported component bindings: {support_issues}")
    completeness = present == question["required_components"] == REQUIRED_COMPONENTS
    if not completeness:
        raise ValueError("contract answer is missing or reordering M/Q/O/L")
    answer = _render(components)
    if answer != _render(components):
        raise AssertionError("contract rendering is nondeterministic")
    return {
        "schema": SCHEMA,
        "candidate_version": VERSION,
        "family": family,
        "question_registry_id": question_registry["registry_id"],
        "question_registry_sha256": _canonical_digest(question_registry),
        "source_sha256": source_sha256,
        "production_packet_sha256": _canonical_digest(packet),
        "production_certificate_sha256": _canonical_digest(certificate),
        "evaluator_only_inputs_read": False,
        "components": components,
        "support_check": {"checked_components": REQUIRED_COMPONENTS, "issues": [], "passed": True},
        "completeness_check": {
            "required_components": REQUIRED_COMPONENTS,
            "present_components": present,
            "passed": True,
        },
        "final_answer": answer,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--family", required=True)
    parser.add_argument("--question-registry", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    raw = args.evidence.resolve(strict=True).read_bytes()
    result = compile_answer(
        json.loads(raw),
        family=args.family,
        source_sha256=hashlib.sha256(raw).hexdigest(),
        question_registry=json.loads(args.question_registry.resolve(strict=True).read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
