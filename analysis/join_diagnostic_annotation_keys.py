#!/usr/bin/env python3
"""Join diagnostic development condition keys after complete human adjudication."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_named(values: list[str]) -> dict[str, Path]:
    parsed: dict[str, Path] = {}
    for value in values:
        name, separator, path = value.partition("=")
        if not separator or not name or not path:
            raise ValueError(f"expected NAME=PATH, got {value!r}")
        if name in parsed:
            raise ValueError(f"duplicate adjudication name: {name}")
        parsed[name] = (ROOT / path).resolve(strict=True)
    return parsed


def join(
    inventory: dict[str, Any], adjudications: dict[str, dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if inventory.get("schema") != "crane-diagnostic-development-annotation-inventory/v1":
        raise ValueError("unsupported diagnostic annotation inventory")
    specifications = inventory.get("packets")
    if not isinstance(specifications, list):
        raise ValueError("inventory has no packet specifications")
    names = {specification["name"] for specification in specifications}
    if len(names) != len(specifications) or names != set(adjudications):
        raise ValueError("inventory and adjudication names differ")

    joined: list[dict[str, Any]] = []
    quarantine_clusters: set[str] = set()
    input_report: list[dict[str, Any]] = []
    seen_response_ids: set[str] = set()
    for specification in specifications:
        name = specification["name"]
        packet_path = (ROOT / specification["packet"]).resolve(strict=True)
        key_path = (ROOT / specification["key"]).resolve(strict=True)
        if digest(packet_path) != specification["packet_sha256"]:
            raise ValueError(f"{name}: packet hash differs from inventory")
        if digest(key_path) != specification["key_sha256"]:
            raise ValueError(f"{name}: key hash differs from inventory")
        key = load(key_path)
        if key.get("packet_sha256") != specification["packet_sha256"]:
            raise ValueError(f"{name}: evaluator key names a different packet hash")
        adjudication = adjudications[name]
        if adjudication.get("schema") != "crane-diagnostic-annotation-adjudication/v1":
            raise ValueError(f"{name}: unsupported adjudication schema")
        if adjudication.get("status") != "COMPLETE" or not isinstance(
            adjudication.get("labels"), dict
        ):
            raise ValueError(f"{name}: adjudication is not complete")
        if adjudication.get("condition_key_joined") is not False:
            raise ValueError(f"{name}: adjudication already claims a key join")

        packet_rows = [
            json.loads(line)
            for line in packet_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        packet_by_response = {row["response_id"]: row for row in packet_rows}
        packet_ids = set(packet_by_response)
        if len(packet_by_response) != len(packet_rows):
            raise ValueError(f"{name}: duplicate response IDs in packet")
        key_entries = key.get("entries")
        if not isinstance(key_entries, list):
            raise ValueError(f"{name}: key has no entry inventory")
        by_response = {entry["response_id"]: entry for entry in key_entries}
        if len(by_response) != len(key_entries):
            raise ValueError(f"{name}: duplicate response IDs in key")
        labels = adjudication["labels"]
        if packet_ids != set(by_response) or packet_ids != set(labels):
            raise ValueError(f"{name}: packet, key, and label inventories differ")
        if seen_response_ids.intersection(packet_ids):
            raise ValueError(f"{name}: response ID appears in multiple packets")
        seen_response_ids.update(packet_ids)

        quarantined_ids = set(
            adjudication.get("evidence_problem_quarantined_responses", [])
        )
        if not quarantined_ids.issubset(packet_ids):
            raise ValueError(f"{name}: quarantine contains an unknown response")
        cluster = specification["statistical_cluster_id"]
        for response_id in sorted(packet_ids):
            label = labels[response_id]
            entry = by_response[response_id]
            if label.get("response_id") != response_id:
                raise ValueError(f"{name}: label/response mapping differs")
            row = dict(label)
            packet_row = packet_by_response[response_id]
            row.update(
                {
                    "condition": entry["condition"],
                    "source_episode_id": entry["episode_id"],
                    "question_id": entry["question_id"],
                    "statistical_cluster_id": cluster,
                    "evidence_variant": specification["evidence_variant"],
                    "question_kind": packet_row["question_kind"],
                    "diagnosable": packet_row["diagnosable"],
                    "reference_status": packet_row["reference_status"],
                    "provider": entry["provider"],
                    "model": entry["model"],
                    "used_template_fallback": entry["used_template_fallback"],
                    "verification_accepted": entry["verification_accepted"],
                }
            )
            joined.append(row)
            if response_id in quarantined_ids or bool(label.get("evidence_problem")):
                quarantine_clusters.add(cluster)
        input_report.append(
            {
                "name": name,
                "packet": specification["packet"],
                "packet_sha256": specification["packet_sha256"],
                "key": specification["key"],
                "key_sha256": specification["key_sha256"],
                "responses": len(packet_ids),
            }
        )

    analysis_rows = [
        row
        for row in joined
        if row["statistical_cluster_id"] not in quarantine_clusters
    ]
    report = {
        "schema": "crane-diagnostic-annotation-key-join/v1",
        "status": "COMPLETE_DEVELOPMENT_ONLY",
        "condition_key_joined": True,
        "input_responses": len(joined),
        "analysis_responses": len(analysis_rows),
        "input_statistical_clusters": len(
            {row["statistical_cluster_id"] for row in joined}
        ),
        "analysis_statistical_clusters": len(
            {row["statistical_cluster_id"] for row in analysis_rows}
        ),
        "quarantined_statistical_clusters": sorted(quarantine_clusters),
        "quarantined_responses": len(joined) - len(analysis_rows),
        "inputs": input_report,
    }
    return analysis_rows, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--adjudication", action="append", required=True, metavar="NAME=PATH")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    inventory_path = (ROOT / args.inventory).resolve(strict=True)
    adjudication_paths = parse_named(args.adjudication)
    output_path = (ROOT / args.output).resolve()
    report_path = (ROOT / args.report).resolve()
    if output_path.exists() or report_path.exists():
        raise SystemExit("refusing to overwrite existing output or report")

    adjudications = {name: load(path) for name, path in adjudication_paths.items()}
    rows, report = join(load(inventory_path), adjudications)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    report.update(
        {
            "inventory": inventory_path.relative_to(ROOT).as_posix(),
            "inventory_sha256": digest(inventory_path),
            "adjudications": {
                name: {"path": str(path), "sha256": digest(path)}
                for name, path in sorted(adjudication_paths.items())
            },
            "output": str(output_path),
            "output_sha256": digest(output_path),
        }
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
