#!/usr/bin/env python3
"""Join evaluator-only legacy condition metadata after complete adjudication.

This is the first workflow stage allowed to read the sealed key. It verifies the
packet hash and complete ID inventory, replaces blinded metadata sentinels from
the human form, applies the frozen whole-episode evidence-problem quarantine,
and emits analysis-ready JSONL plus an auditable report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BLINDED_METADATA_SENTINEL = "BLINDED_PENDING_KEY_JOIN"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def join(
    adjudication: dict[str, Any],
    key: dict[str, Any],
    split: dict[str, Any],
    packet_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if adjudication.get("schema") != "crane-explain-annotation-adjudication/v1":
        raise ValueError("unsupported adjudication schema")
    if adjudication.get("status") != "COMPLETE" or not isinstance(
        adjudication.get("labels"), dict
    ):
        raise ValueError("adjudication is not complete")
    if adjudication.get("condition_key_joined") is not False:
        raise ValueError("adjudication already claims a condition-key join")
    if key.get("schema") != "crane-explain-blinded-annotation-key/v1":
        raise ValueError("unsupported annotation-key schema")
    if split.get("schema") != "crane-provenance-final-split/v1":
        raise ValueError("unsupported frozen-split schema")
    if sha256(packet_path) != key.get("packet_sha256"):
        raise ValueError("sealed packet hash does not match the evaluator-only key")

    packet_ids = {
        json.loads(line)["response_id"]
        for line in packet_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    entries = key.get("entries")
    if not isinstance(entries, list):
        raise ValueError("annotation key has no entry inventory")
    by_response = {entry["response_id"]: entry for entry in entries}
    labels = adjudication["labels"]
    if len(by_response) != len(entries):
        raise ValueError("annotation key has duplicate response IDs")
    if packet_ids != set(by_response) or packet_ids != set(labels):
        raise ValueError("packet, key, and adjudicated response inventories differ")
    quarantined_response_ids = set(
        adjudication.get("evidence_problem_quarantined_responses", [])
    )
    if not quarantined_response_ids.issubset(packet_ids):
        raise ValueError("adjudication quarantines a response outside the packet")

    instances = split.get("instances")
    if not isinstance(instances, list):
        raise ValueError("frozen split has no instance inventory")
    family_by_episode = {
        instance["opaque_episode_id"]: instance["scenario_family"]
        for instance in instances
    }
    if len(family_by_episode) != len(instances):
        raise ValueError("frozen split has duplicate episode IDs")

    quarantine_episodes: set[str] = set()
    joined_all: list[dict[str, Any]] = []
    for response_id in sorted(packet_ids):
        label = labels[response_id]
        entry = by_response[response_id]
        if label.get("response_id") != response_id:
            raise ValueError(f"label mapping disagrees with response_id {response_id}")
        if label.get("episode_id") != BLINDED_METADATA_SENTINEL:
            raise ValueError(f"{response_id}: unexpected pre-join episode metadata")
        if label.get("scenario_family") != BLINDED_METADATA_SENTINEL:
            raise ValueError(f"{response_id}: unexpected pre-join scenario metadata")
        if label.get("condition_blinded_id") != response_id:
            raise ValueError(f"{response_id}: invalid condition-blinded identifier")
        if label.get("question_kind") != entry.get("question_kind"):
            raise ValueError(f"{response_id}: question kind differs from sealed key")
        episode_id = entry["episode_id"]
        split_id = episode_id.split("-worker-", 1)[0]
        if split_id not in family_by_episode:
            raise ValueError(f"{response_id}: episode is absent from frozen split")
        row = dict(label)
        row.update(
            {
                "episode_id": episode_id,
                "scenario_family": family_by_episode[split_id],
                "condition": entry["condition"],
                "arm": entry["arm"],
                "model": entry["model"],
                "result_path": entry["result_path"],
            }
        )
        joined_all.append(row)
        if response_id in quarantined_response_ids or bool(label.get("evidence_problem")):
            quarantine_episodes.add(episode_id)

    analysis_rows = [
        row for row in joined_all if row["episode_id"] not in quarantine_episodes
    ]
    report = {
        "schema": "crane-explain-annotation-key-join/v1",
        "status": "COMPLETE",
        "condition_key_joined": True,
        "packet_responses": len(packet_ids),
        "analysis_responses": len(analysis_rows),
        "analysis_episodes": len({row["episode_id"] for row in analysis_rows}),
        "quarantine_rule": "evidence_problem quarantines the whole episode, never one condition",
        "quarantined_episodes": sorted(quarantine_episodes),
        "quarantined_responses": len(joined_all) - len(analysis_rows),
    }
    return analysis_rows, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--adjudication", required=True, type=Path)
    parser.add_argument("--key", required=True, type=Path)
    parser.add_argument("--split", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()

    paths = {name: (ROOT / value).resolve() for name, value in vars(args).items()}
    for name in ("adjudication", "key", "split"):
        if not paths[name].is_file():
            parser.error(f"--{name} does not exist")
    for name in ("output", "report"):
        if paths[name].exists():
            raise SystemExit(f"refusing to overwrite existing {name}")
    evaluator_root = (ROOT / "data" / "evaluator_only").resolve()
    if evaluator_root not in paths["key"].parents:
        parser.error("--key must be under data/evaluator_only/")

    key = load(paths["key"])
    packet_path = (ROOT / key["packet"]).resolve(strict=True)
    rows, report = join(
        load(paths["adjudication"]), key, load(paths["split"]), packet_path
    )
    paths["output"].parent.mkdir(parents=True, exist_ok=True)
    paths["output"].write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report.update(
        {
            "adjudication": paths["adjudication"].relative_to(ROOT).as_posix(),
            "adjudication_sha256": sha256(paths["adjudication"]),
            "key": paths["key"].relative_to(ROOT).as_posix(),
            "key_sha256": sha256(paths["key"]),
            "packet": packet_path.relative_to(ROOT).as_posix(),
            "packet_sha256": sha256(packet_path),
            "split": paths["split"].relative_to(ROOT).as_posix(),
            "split_sha256": sha256(paths["split"]),
            "output": paths["output"].relative_to(ROOT).as_posix(),
            "output_sha256": sha256(paths["output"]),
        }
    )
    paths["report"].parent.mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
