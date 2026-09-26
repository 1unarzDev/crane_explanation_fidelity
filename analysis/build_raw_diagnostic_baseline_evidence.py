#!/usr/bin/env python3
"""Build raw robot-visible evidence for R without exposing P's checked diagnostic output."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from recompute_command_motion_diagnostic import method_input_from_export


GEOMETRY_FIELDS = (
    "actionResultPose",
    "behaviorTreeCapture",
    "behaviorTreeTransitionCounts",
    "finalPose",
    "goal",
    "initialPose",
    "latestCostmapSnapshot",
    "planHistory",
    "planHistoryProvenance",
    "status",
    "trajectory",
    "trajectoryProvenance",
    "wallSeconds",
)
GEOMETRY_CONFIGURATION_FIELDS = (
    "bt_xml_sha256",
    "computation_version",
    "costmap_frame",
    "deadline_seconds",
    "inflation_radius_m",
    "nav2_config_sha256",
    "robot_radius_m",
)
FORBIDDEN_KEYS = {
    "diagnostic_result",
    "reference_computation",
    "answer_plan",
    "final_answer",
    "final_text_verification",
    "land-evaluator-truth",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_no_forbidden_keys(value: Any, location: str = "root") -> None:
    if isinstance(value, dict):
        leaked = FORBIDDEN_KEYS.intersection(value)
        if leaked:
            raise ValueError(f"forbidden checked/evaluator fields at {location}: {sorted(leaked)}")
        for key, item in value.items():
            _assert_no_forbidden_keys(item, f"{location}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_keys(item, f"{location}[{index}]")


def build_command(export: dict[str, Any], *, source_sha256: str) -> dict[str, Any]:
    payload = method_input_from_export(export)
    payload["transport_schema"] = "crane-raw-command-motion-baseline-evidence/v1"
    payload["source_export_sha256"] = source_sha256
    payload["treatment_boundary"] = (
        "Raw robot-visible command, odometry, execution, and provenance inputs. P's diagnostic "
        "result, reference computation, answer plan, verifier, and answer are absent."
    )
    if "evidence_mask" in export:
        payload["evidence_mask"] = export["evidence_mask"]
    _assert_no_forbidden_keys(payload)
    return payload


def build_geometry(
    fixture: dict[str, Any],
    *,
    episode_id: str,
    source_sha256: str,
    configuration_export: dict[str, Any],
    configuration_source_sha256: str,
) -> dict[str, Any]:
    missing = [field for field in GEOMETRY_FIELDS if field not in fixture]
    if missing:
        raise ValueError("geometry fixture lacks required robot-visible fields: " + ", ".join(missing))
    method_input = configuration_export.get("method_input")
    if not isinstance(method_input, dict):
        raise ValueError("geometry configuration export lacks method_input")
    missing_configuration = [
        field for field in GEOMETRY_CONFIGURATION_FIELDS if field not in method_input
    ]
    if missing_configuration:
        raise ValueError(
            "geometry configuration lacks required fields: "
            + ", ".join(missing_configuration)
        )
    configuration = {
        field: method_input[field] for field in GEOMETRY_CONFIGURATION_FIELDS
    }
    payload = {field: fixture[field] for field in GEOMETRY_FIELDS}
    payload.update(
        {
            "schema": "crane-raw-geometric-baseline-evidence/v1",
            "visibility": "robot_visible",
            "episode_id": episode_id,
            "source_fixture_sha256": source_sha256,
            "declared_diagnostic_configuration": configuration,
            "configuration_source_sha256": configuration_source_sha256,
            "treatment_boundary": (
                "Sanitized robot-visible costmap, delivered plans, odometry trajectory, action "
                "boundary, and BT transition counts. Evaluator layout/intervention truth and P's "
                "diagnostic/reference/answer artifacts are absent."
            ),
        }
    )
    snapshot = payload["latestCostmapSnapshot"]
    if not isinstance(snapshot, dict) or not snapshot.get("dataSha256"):
        raise ValueError("geometry evidence lacks costmap metadata")
    _assert_no_forbidden_keys(payload)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=("command", "geometry"), required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--episode-id")
    parser.add_argument("--configuration-from", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit(f"refusing existing output: {args.output}")
    document = json.loads(args.input.read_text(encoding="utf-8"))
    if args.family == "command":
        payload = build_command(document, source_sha256=digest(args.input))
    else:
        if not args.episode_id:
            parser.error("--episode-id is required for geometry")
        if not args.configuration_from:
            parser.error("--configuration-from is required for geometry")
        configuration_export = json.loads(
            args.configuration_from.read_text(encoding="utf-8")
        )
        payload = build_geometry(
            document,
            episode_id=args.episode_id,
            source_sha256=digest(args.input),
            configuration_export=configuration_export,
            configuration_source_sha256=digest(args.configuration_from),
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
