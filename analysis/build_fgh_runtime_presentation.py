#!/usr/bin/env python3
"""Build the shared runtime presentation and pre-call F/G/H parity audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from crane_explain.io import load_episode
from crane_explain.runtime_presentation import (
    audit_fgh_information_parity,
    build_nav2_runtime_presentation,
    load_jsonl_records,
    validate_episode_projection,
)


def write_new(path: Path, payload: dict) -> None:
    if path.exists():
        raise SystemExit(f"refusing existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture-dir", required=True, type=Path)
    parser.add_argument("--structured-episode", required=True, type=Path)
    parser.add_argument(
        "--question-kind", choices=("recovery-mechanism", "failure-cause"), required=True
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    capture = args.capture_dir
    records = load_jsonl_records(
        (capture / "events.jsonl").read_text(encoding="utf-8").splitlines()
    )
    manifest = json.loads((capture / "manifest.json").read_text(encoding="utf-8"))
    episode = load_episode(args.structured_episode)
    presentation = build_nav2_runtime_presentation(
        records,
        manifest,
        (capture / "behavior_tree.xml").read_bytes(),
        episode,
    )
    validate_episode_projection(presentation, episode)
    audit = audit_fgh_information_parity(presentation, args.question_kind)
    write_new(args.output_dir / "runtime-presentation.json", presentation)
    write_new(args.output_dir / "information-parity-audit.json", audit)
    print(
        json.dumps(
            {
                "status": "accepted" if audit["accepted"] else "rejected",
                "episode_id": presentation["episode_id"],
                "question_kind": args.question_kind,
                "unit_count": len(audit["units"]),
                "output_dir": str(args.output_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
