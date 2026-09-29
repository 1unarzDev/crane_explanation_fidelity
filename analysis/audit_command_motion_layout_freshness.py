#!/usr/bin/env python3
"""Reconcile v6 command-motion layout allocation and materialization.

This audit deliberately distinguishes a layout named in a frozen schedule from a
layout for which robot-visible physical data actually exist.  Neither status is
called "untouched"; the latter is the contamination boundary for a future
physical cohort, while the former remains a governance constraint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
LAYOUT_PREFIX = "diagnostic-command-motion-"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_pinned(root: Path, item: dict[str, str]) -> dict[str, Any]:
    path = root / item["path"]
    if not path.is_file():
        raise ValueError(f"missing pinned source: {item['path']}")
    if sha256(path) != item["sha256"]:
        raise ValueError(f"source hash mismatch: {item['path']}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"source must be a JSON object: {item['path']}")
    return value


def _objects(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from _objects(child)


def _allocations(document: dict[str, Any], source_path: str) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in _objects(document):
        layout_id = item.get("layout_id", item.get("layout"))
        run_id = item.get("run_id")
        if (
            isinstance(layout_id, str)
            and layout_id.startswith(LAYOUT_PREFIX)
            and isinstance(run_id, str)
            and run_id
        ):
            result.append({"layout_id": layout_id, "run_id": run_id, "source": source_path})
    return result


def _run_has_physical_artifact(root: Path, run_id: str) -> bool:
    manifest = root / "manifests/data" / f"{run_id}.robot-visible.json"
    if manifest.is_file():
        return True
    visible = root / "data/robot_visible"
    return any(path.is_dir() for path in visible.glob(f"*/{run_id}"))


def _run_has_semantic_artifact(root: Path, run_id: str) -> bool:
    model_root = root / "model_outputs"
    if not model_root.is_dir():
        return False
    return any(path.is_file() for path in model_root.rglob(f"{run_id}.*"))


def audit(root: Path, declaration: dict[str, Any]) -> dict[str, Any]:
    if declaration.get("schema") != "crane-command-motion-layout-freshness-audit/v1":
        raise ValueError("unsupported freshness audit schema")

    catalog_item = declaration["catalog"]
    catalog = _load_pinned(root, catalog_item)
    layouts = catalog.get("layouts")
    if not isinstance(layouts, list):
        raise ValueError("catalog layouts are missing")
    catalog_by_id = {item["id"]: item for item in layouts}
    if len(catalog_by_id) != len(layouts):
        raise ValueError("duplicate catalog layout ID")

    allocations: list[dict[str, str]] = []
    for source in declaration["allocation_sources"]:
        document = _load_pinned(root, source)
        allocations.extend(_allocations(document, source["path"]))
    unknown = sorted({item["layout_id"] for item in allocations} - set(catalog_by_id))
    if unknown:
        raise ValueError(f"allocation references unknown catalog layouts: {unknown}")

    runs_by_layout: dict[str, set[str]] = {layout_id: set() for layout_id in catalog_by_id}
    sources_by_layout: dict[str, set[str]] = {layout_id: set() for layout_id in catalog_by_id}
    for item in allocations:
        runs_by_layout[item["layout_id"]].add(item["run_id"])
        sources_by_layout[item["layout_id"]].add(item["source"])

    records = []
    for layout_id, layout in sorted(catalog_by_id.items()):
        run_ids = sorted(runs_by_layout[layout_id])
        physical_runs = [run_id for run_id in run_ids if _run_has_physical_artifact(root, run_id)]
        semantic_runs = [run_id for run_id in run_ids if _run_has_semantic_artifact(root, run_id)]
        records.append(
            {
                "layout_id": layout_id,
                "split": layout["studySplit"],
                "scheduled_run_ids": run_ids,
                "allocation_sources": sorted(sources_by_layout[layout_id]),
                "physical_run_ids": physical_runs,
                "semantic_run_ids": semantic_runs,
                "physically_materialized": bool(physical_runs),
                "semantic_outputs_present": bool(semantic_runs),
            }
        )

    split_results: dict[str, Any] = {}
    for split in sorted({item["split"] for item in records}):
        members = [item for item in records if item["split"] == split]
        materialized = [item["layout_id"] for item in members if item["physically_materialized"]]
        semantic = [item["layout_id"] for item in members if item["semantic_outputs_present"]]
        scheduled = [item["layout_id"] for item in members if item["scheduled_run_ids"]]
        never_materialized = [
            item["layout_id"] for item in members if not item["physically_materialized"]
        ]
        split_results[split] = {
            "catalog_layouts": len(members),
            "scheduled_layouts": len(scheduled),
            "physically_materialized_layouts": len(materialized),
            "semantic_output_layouts": len(semantic),
            "never_physically_materialized_layouts": len(never_materialized),
            "physically_materialized_ids": materialized,
            "never_physically_materialized_ids": never_materialized,
        }

    expected = declaration["expected_counts"]
    for split, fields in expected.items():
        if split not in split_results:
            raise ValueError(f"expected split absent from catalog: {split}")
        for field, expected_value in fields.items():
            if split_results[split].get(field) != expected_value:
                raise ValueError(
                    f"freshness count mismatch: {split}.{field} "
                    f"expected {expected_value}, got {split_results[split].get(field)}"
                )

    confirmation = split_results["command-motion-confirmation-reserve"]
    replication = split_results["command-motion-replication-reserve"]
    return {
        "schema": "crane-command-motion-layout-freshness-audit-result/v1",
        "audit_id": declaration["audit_id"],
        "status": "PASS_RECONCILED",
        "splits": split_results,
        "governance_findings": {
            "confirmation_reserve": (
                "All catalog layouts have physical artifacts and are development-only for the "
                "evidence-calibration redirect."
            ),
            "replication_reserve": (
                f"{replication['physically_materialized_layouts']} layouts have physical "
                "development artifacts; the remaining "
                f"{replication['never_physically_materialized_layouts']} are physically unused "
                "but already allocated by the old frozen replication schedule."
            ),
            "freshness_boundary": (
                "Do not describe an allocated layout as untouched. Physical non-materialization "
                "is necessary but not sufficient for reassignment under a new protocol."
            ),
            "confirmation_materialized_count": confirmation["physically_materialized_layouts"],
        },
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--declaration",
        type=Path,
        default=ROOT / "manifests/study/command-motion-layout-freshness-audit-v1.json",
    )
    args = parser.parse_args()
    path = args.declaration if args.declaration.is_absolute() else ROOT / args.declaration
    try:
        result = audit(ROOT, json.loads(path.read_text(encoding="utf-8")))
    except (KeyError, TypeError, ValueError) as error:
        print(json.dumps({"status": "FAIL", "error": str(error)}, indent=2, sort_keys=True))
        sys.exit(1)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
