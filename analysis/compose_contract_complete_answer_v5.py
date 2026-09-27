#!/usr/bin/env python3
"""Render the checked M/Q/O/L contract as a bounded 120-word diagnostic brief."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from build_command_motion_composition_packet import _format_number, _interval, _measurement_map
from compose_contract_complete_answer import _recovered_command_measurement
from compose_contract_complete_answer_v4 import compile_answer as compile_v4


VERSION = "p-contract-v5-concise-development"
WORD_BUDGET = 120


def _render(components: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"{item['component']} — {item['text']}" for item in components
    )


def _command_text(document: dict[str, Any], family: str) -> dict[str, str]:
    measurements = _measurement_map(document["diagnostic_result"])
    action = str(measurements["action_status"]["value"])
    if family in {"persistent_command_motion_discrepancy", "measured_response_recovery"}:
        healthy_command = measurements["calibrated_healthy_commanded_planar_speed"]
        healthy_motion = measurements["calibrated_healthy_planar_speed"]
        event_command = measurements["discrepancy_commanded_planar_speed"]
        event_motion = measurements["discrepancy_measured_planar_speed"]
        q = (
            f"Healthy {_interval(healthy_motion)}: command {_format_number(healthy_command['value'])} "
            f"{healthy_command['unit']}, motion {_format_number(healthy_motion['value'])} "
            f"{healthy_motion['unit']}. Event {_interval(event_motion)}: command "
            f"{_format_number(event_command['value'])} {event_command['unit']}, motion "
            f"{_format_number(event_motion['value'])} {event_motion['unit']}."
        )
        if family == "persistent_command_motion_discrepancy":
            return {
                "M": "The streams support a persistent command-to-measured-motion discrepancy.",
                "Q": q,
                "O": f"The recorded navigation action {action}.",
                "L": (
                    "The evidence does not identify a unique physical cause; commands do not prove "
                    "actuator acceptance, and odometry does not prove Nav2 consumption."
                ),
            }
        recovered = measurements["recovered_measured_planar_speed"]
        recovered_command = _recovered_command_measurement(document, recovered)
        ratio = measurements["recovered_response_ratio"]
        q += (
            f" Recovery {_interval(recovered)}: command "
            f"{_format_number(recovered_command['value'])} {recovered_command['unit']}, motion "
            f"{_format_number(recovered['value'])} {recovered['unit']} "
            f"({_format_number(ratio['value'])} of healthy response)."
        )
        return {
            "M": "The command–motion discrepancy was followed by measured response recovery.",
            "Q": q,
            "O": f"After recovery, the recorded navigation action {action}.",
            "L": (
                "Timing does not establish that Wait caused recovery or that recovery caused the "
                "eventual outcome; the original physical or actuator cause remains unresolved."
            ),
        }
    if family == "nominal_false_premise_or_irrelevant_obstacle":
        commanded = measurements["calibrated_healthy_commanded_planar_speed"]
        measured = measurements["calibrated_healthy_planar_speed"]
        return {
            "M": "The evidence does not support the alleged command-to-motion failure.",
            "Q": (
                f"Healthy {_interval(measured)}: command {_format_number(commanded['value'])} "
                f"{commanded['unit']}, motion {_format_number(measured['value'])} {measured['unit']}."
            ),
            "O": f"The recorded navigation action {action}.",
            "L": (
                "This bounded negative result does not exclude every transient difficulty; visible "
                "obstacles alone do not establish Nav2 consumption or causation."
            ),
        }
    if family == "missing_decisive_or_ambiguous_evidence":
        commands = int(measurements["delivered_command_sample_count"]["value"])
        odometry = int(measurements["independent_odometry_sample_count"]["value"])
        missing = "measured motion" if commands > 0 and odometry == 0 else "delivered command"
        chain = (
            "command-to-motion discrepancy"
            if missing == "measured motion"
            else "requested-to-delivered-to-measured response chain"
        )
        return {
            "M": "The command-to-measured-motion mechanism cannot be established.",
            "Q": (
                f"The record has {commands} delivered-command samples and {odometry} independent "
                f"odometry samples; {missing} is the decisive missing discriminator."
            ),
            "O": f"The recorded navigation action {action}.",
            "L": (
                f"Without {missing}, the execution sequence cannot establish a {chain}, actuator "
                "acceptance, or a unique physical cause."
            ),
        }
    raise ValueError(f"unsupported command family: {family}")


def _geometry_text(document: dict[str, Any]) -> dict[str, str]:
    measurements = _measurement_map(document["diagnostic_result"])
    action = str(measurements["action_status"]["value"])
    route = document["reference_computation"]["direct_route"]
    blocked = route["first_lethal_sample_from_start"]
    return {
        "M": "The retained navigation-model snapshot restricts the direct route but retains a below-threshold connection to the goal.",
        "Q": f"Near x={float(blocked['x']):.3f} m, cell cost {int(blocked['cost'])} meets the non-traversable threshold 253.",
        "O": f"The recorded navigation action {action}.",
        "L": "The snapshot does not establish global physical no-path, obstacle identity, exact Nav2 consumption, or outcome causation.",
    }


def compile_answer(
    document: dict[str, Any], *, family: str, source_sha256: str,
    question_registry: dict[str, Any],
) -> dict[str, Any]:
    result = compile_v4(
        document,
        family=family,
        source_sha256=source_sha256,
        question_registry=question_registry,
    )
    texts = _geometry_text(document) if family == "bounded_geometric_restriction" else _command_text(document, family)
    components = result["components"]
    if [item["component"] for item in components] != ["M", "Q", "O", "L"]:
        raise ValueError("parent answer is not exact M/Q/O/L")
    for item in components:
        item["text"] = texts[item["component"]]
    final = _render(components)
    words = len(final.split())
    if words > WORD_BUDGET:
        raise ValueError(f"concise contract exceeds {WORD_BUDGET}-word budget: {words}")
    result.update({
        "candidate_version": VERSION,
        "parent_candidate_version": result.get("candidate_version"),
        "bounded_repair": {
            "scope": "compact final rendering without dropping M/Q/O/L content",
            "word_budget": WORD_BUDGET,
            "word_count_rule": "Unicode whitespace-delimited tokens in final_answer",
        },
        "communication_budget": {"maximum_words": WORD_BUDGET, "actual_words": words, "passed": True},
        "final_answer": final,
    })
    return result


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
        json.loads(raw), family=args.family, source_sha256=hashlib.sha256(raw).hexdigest(),
        question_registry=json.loads(args.question_registry.resolve(strict=True).read_text()),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
