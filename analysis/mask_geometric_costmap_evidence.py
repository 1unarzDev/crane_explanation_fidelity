#!/usr/bin/env python3
"""Create a deterministic robot-visible evidence mask for geometric diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mask_costmap_cells(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    masked = json.loads(json.dumps(payload))
    snapshot = masked.get("latestCostmapSnapshot")
    if not isinstance(snapshot, dict) or "data" not in snapshot:
        raise ValueError("latestCostmapSnapshot.data is absent")
    del snapshot["data"]
    return masked, ["/latestCostmapSnapshot/data"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--mask-id", default="withhold-costmap-cell-payload-v1")
    args = parser.parse_args()

    source = (ROOT / args.input).resolve(strict=True)
    output = (ROOT / args.output).resolve()
    manifest = (ROOT / args.manifest).resolve()
    robot_root = (ROOT / "data" / "robot_visible").resolve(strict=True)
    if robot_root not in source.parents or robot_root not in output.parents:
        parser.error("input and output must both be under data/robot_visible/")
    if output.exists() or manifest.exists():
        raise SystemExit("refusing to overwrite an existing masked fixture or manifest")

    payload = json.loads(source.read_text(encoding="utf-8"))
    masked, removed = mask_costmap_cells(payload)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(masked, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schema": "crane-robot-visible-evidence-mask/v1",
                "mask_id": args.mask_id,
                "visibility": "robot_visible",
                "source": source.relative_to(ROOT).as_posix(),
                "source_sha256": sha256(source),
                "output": output.relative_to(ROOT).as_posix(),
                "output_sha256": sha256(output),
                "removed_json_pointers": removed,
                "purpose": "Test qualification when decisive costmap cell values are unavailable.",
                "evaluator_truth_available_to_methods": False,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
