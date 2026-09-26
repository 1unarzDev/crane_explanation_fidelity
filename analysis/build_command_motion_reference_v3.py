#!/usr/bin/env python3
"""Build command-motion references with grammar fixes without altering frozen v2 bytes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_command_motion_reference_v2 import build_reference as build_v2, digest


def build_reference(
    export: dict[str, Any], independent: dict[str, Any], *, question_id: str
) -> dict[str, Any]:
    result = build_v2(export, independent, question_id=question_id)
    measurements = independent["result"]
    failure_count = measurements["follow_path_failure_count"]
    recovery_count = measurements["source_qualified_wait_recovery_count"]
    attempt_count = measurements["follow_path_attempt_count"]
    unit = next(
        item for item in result["required_units"] if item["unit_id"] == "execution-sequence"
    )
    action_status = export["method_input"]["action_status"]
    unit["text"] = (
        f"The action status is {action_status}; the retained sequence contains "
        f"{failure_count} FollowPath {'failure' if failure_count == 1 else 'failures'}, "
        f"{recovery_count} source-qualified Wait "
        f"{'invocation' if recovery_count == 1 else 'invocations'}, and {attempt_count} "
        f"FollowPath {'attempt' if attempt_count == 1 else 'attempts'}."
    )
    return result


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
