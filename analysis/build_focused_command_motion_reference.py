#!/usr/bin/env python3
"""Build the focused question-essential reference from independent command-motion evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_command_motion_reference_v2 import build_reference, digest


def unit(unit_id: str, text: str) -> dict[str, str]:
    return {"unit_id": unit_id, "text": text}


def build_focused_reference(
    export: dict[str, Any], independent: dict[str, Any], *, question_id: str
) -> dict[str, Any]:
    base = build_reference(export, independent, question_id=question_id)
    result = independent["result"]
    status = independent["execution_basis"]["action_status"]
    disposition = result["disposition"]
    required: list[dict[str, str]]
    mechanism_unit_id: str | None
    primary = disposition == "supported"
    if disposition == "supported":
        recovered = result.get("response_recovery_interval_s") is not None
        mechanism_unit_id = "mechanism-command-motion-response"
        required = [
            unit(
                mechanism_unit_id,
                (
                    "A delivered-command/measured-motion discrepancy followed by measured response recovery is supported."
                    if recovered
                    else "A persistent delivered-command/measured-motion discrepancy is supported."
                ),
            ),
            unit(
                "healthy-and-event-comparison",
                f"Healthy {result['healthy_interval_s'][0]:.1f}--{result['healthy_interval_s'][1]:.1f} s medians were "
                f"{result['healthy_commanded_planar_speed_mps']:.3f} m/s commanded and "
                f"{result['healthy_measured_planar_speed_mps']:.4f} m/s measured; event "
                f"{result['interval_s'][0]:.1f}--{result['interval_s'][1]:.1f} s medians were "
                f"{result['discrepancy_commanded_planar_speed_mps']:.3f} m/s commanded and "
                f"{result['discrepancy_measured_planar_speed_mps']:.3f} m/s measured.",
            ),
        ]
        if recovered:
            required.append(
                unit(
                    "measured-response-recovery",
                    f"Measured response recovered during {result['response_recovery_interval_s'][0]:.1f}--"
                    f"{result['response_recovery_interval_s'][1]:.1f} s to "
                    f"{result['recovered_measured_planar_speed_mps']:.4f} m/s "
                    f"(response ratio {result['recovered_response_ratio']:.4f}).",
                )
            )
        required.append(unit("action-outcome", f"The recorded action status is {status}."))
        required.append(
            unit(
                "causal-limit",
                (
                    "The ordering does not prove that response recovery caused the action outcome, and the unique physical cause of the earlier discrepancy remains unresolved."
                    if recovered
                    else "The evidence does not uniquely identify actuator rejection, obstruction, collision, slip, or another physical cause; delivered streams do not prove Nav2 consumption or actuator acceptance."
                ),
            )
        )
    elif disposition == "insufficient":
        mechanism_unit_id = None
        required = [
            unit("supported-outcome", f"The recorded action status is {status}."),
            unit(
                "missing-discriminator",
                f"The retained record has {independent['sample_counts']['command']} command samples and "
                f"{independent['sample_counts']['odometry']} odometry samples; the missing stream prevents the required comparison.",
            ),
            unit("mechanism-withheld", "No command-to-motion mechanism is established."),
            unit("causal-limit", "No unique physical cause is established."),
        ]
    else:
        mechanism_unit_id = None
        required = [
            unit("false-premise", "The command-to-motion diagnostic did not trigger."),
            unit(
                "healthy-motion-evidence",
                f"Healthy measured response was {result['healthy_measured_planar_speed_mps']:.4f} m/s during "
                f"{result['healthy_interval_s'][0]:.1f}--{result['healthy_interval_s'][1]:.1f} s.",
            ),
            unit("action-outcome", f"The recorded action status is {status}."),
            unit("causal-limit", "Visibility or temporal order alone does not prove obstacle causation or exact Nav2 consumption."),
        ]
    base.update(
        {
            "schema": "crane-focused-command-motion-annotation-reference/v1",
            "reference_status": "FOCUSED_INDEPENDENT_REFERENCE_NOT_HUMAN_GOLD",
            "primary_endpoint_eligible": primary,
            "mechanism_unit_id": mechanism_unit_id,
            "required_units": required,
            "complete_endpoint_unit_ids": (
                [item["unit_id"] for item in required] if primary else None
            ),
            "supplemental_evidence_policy": "Facts in allowed_evidence remain judge-visible and may support correct supplemental statements; omission of supplemental facts does not fail the focused endpoint.",
        }
    )
    return base


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--independent-reference", required=True, type=Path)
    parser.add_argument("--question-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing reference: {args.output}")
    export = json.loads(args.export.read_text(encoding="utf-8"))
    independent = json.loads(args.independent_reference.read_text(encoding="utf-8"))
    payload = build_focused_reference(export, independent, question_id=args.question_id)
    payload["inputs"] = {
        "robot_visible_export_sha256": digest(args.export),
        "independent_reference_sha256": digest(args.independent_reference),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
