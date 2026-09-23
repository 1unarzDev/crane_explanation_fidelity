#!/usr/bin/env python3
"""Validate and adjudicate blinded prospective-diagnostic annotations."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from adjudicate_annotations import agreement, read_jsonl


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = (
    "response_id",
    "annotator_id",
    "supported_diagnostic_success",
    "material_error",
    "error_categories",
    "required_units_total",
    "required_units_correct",
    "mechanism_correct",
    "failure_chain_correct",
    "qualification_correct",
    "causal_overclaim",
    "unnecessary_abstention",
    "evidence_citations_correct",
    "next_check_correct",
    "evidence_problem",
    "rationale",
)
BINARY_FIELDS = (
    "supported_diagnostic_success",
    "material_error",
    "mechanism_correct",
    "failure_chain_correct",
    "qualification_correct",
    "causal_overclaim",
    "unnecessary_abstention",
    "evidence_citations_correct",
    "next_check_correct",
    "evidence_problem",
)
ERROR_CATEGORIES = frozenset(
    {
        "unsupported_fact",
        "contradicted_fact",
        "incorrect_measurement",
        "incorrect_mechanism",
        "incorrect_failure_chain",
        "unsupported_causal_claim",
        "unsupported_identity",
        "incorrect_completeness",
        "incorrect_source_link",
        "false_premise_acceptance",
        "unsupported_counterfactual",
    }
)


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def packet_inventory(packet_rows: list[dict[str, Any]]) -> dict[str, int]:
    inventory: dict[str, int] = {}
    for row in packet_rows:
        identifier = row["response_id"]
        if identifier in inventory:
            raise ValueError(f"duplicate packet response_id: {identifier}")
        inventory[identifier] = len(row["required_units"])
    return inventory


def validate_rows(
    rows: list[dict[str, Any]],
    inventory: dict[str, int],
    label: str,
    *,
    expected_ids: set[str],
) -> str:
    problems: list[str] = []
    seen: set[str] = set()
    annotators = {row.get("annotator_id") for row in rows}
    if len(annotators) != 1 or None in annotators:
        problems.append(f"{label}: expected exactly one non-null annotator_id")
    for index, row in enumerate(rows):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            problems.append(f"{label} row {index}: missing fields {missing}")
            continue
        identifier = row["response_id"]
        if identifier in seen:
            problems.append(f"{label}: duplicate response_id {identifier}")
        seen.add(identifier)
        if identifier not in expected_ids:
            problems.append(f"{label}: unexpected response_id {identifier}")
            continue
        for field in BINARY_FIELDS:
            if not isinstance(row[field], bool):
                problems.append(f"{label} {identifier}: {field} must be boolean")
        categories = set(row["error_categories"])
        unknown = categories - ERROR_CATEGORIES
        if unknown:
            problems.append(f"{label} {identifier}: unknown categories {sorted(unknown)}")
        if row["material_error"] != bool(categories):
            problems.append(f"{label} {identifier}: material_error/category inconsistency")
        expected_total = inventory[identifier]
        if row["required_units_total"] != expected_total:
            problems.append(
                f"{label} {identifier}: required_units_total is {row['required_units_total']}, "
                f"packet has {expected_total}"
            )
        correct = row["required_units_correct"]
        if not isinstance(correct, int) or isinstance(correct, bool) or not 0 <= correct <= expected_total:
            problems.append(f"{label} {identifier}: invalid required_units_correct")
        if row["supported_diagnostic_success"] and (
            row["material_error"] or not row["mechanism_correct"]
        ):
            problems.append(
                f"{label} {identifier}: supported success requires a correct mechanism and no material error"
            )
        if not str(row["rationale"]).strip():
            problems.append(f"{label} {identifier}: empty rationale")
    absent = expected_ids - seen
    if absent:
        problems.append(f"{label}: incomplete; {len(absent)} expected responses are absent")
    if problems:
        raise ValueError("annotation pass rejected:\n  " + "\n  ".join(problems))
    return next(iter(annotators))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--annotator-a", required=True, type=Path)
    parser.add_argument("--annotator-b", required=True, type=Path)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    packet_path = (ROOT / args.packet).resolve(strict=True)
    inventory = packet_inventory(read_jsonl(packet_path))
    packet_ids = set(inventory)
    rows_a = read_jsonl((ROOT / args.annotator_a).resolve(strict=True))
    rows_b = read_jsonl((ROOT / args.annotator_b).resolve(strict=True))
    annotator_a = validate_rows(rows_a, inventory, "annotator-a", expected_ids=packet_ids)
    annotator_b = validate_rows(rows_b, inventory, "annotator-b", expected_ids=packet_ids)
    if annotator_a == annotator_b:
        raise SystemExit("both passes use the same annotator_id")

    first = {row["response_id"]: row for row in rows_a}
    second = {row["response_id"]: row for row in rows_b}
    report = {field: agreement(first, second, field) for field in BINARY_FIELDS}
    report["required_units_correct"] = agreement(first, second, "required_units_correct")
    compared_fields = (*BINARY_FIELDS, "required_units_correct")
    disagreements = sorted(
        identifier
        for identifier in packet_ids
        if any(first[identifier][field] != second[identifier][field] for field in compared_fields)
    )
    quarantined = sorted(
        identifier
        for identifier in packet_ids
        if first[identifier]["evidence_problem"] or second[identifier]["evidence_problem"]
    )

    final = (
        {identifier: first[identifier] for identifier in sorted(packet_ids)}
        if not disagreements
        else None
    )
    unresolved = list(disagreements)
    if args.adjudication is not None:
        if not disagreements:
            raise SystemExit("adjudication was supplied but the annotators had no disagreements")
        rows_c = read_jsonl((ROOT / args.adjudication).resolve(strict=True))
        adjudicator = validate_rows(
            rows_c,
            inventory,
            "adjudicator",
            expected_ids=set(disagreements),
        )
        if adjudicator in {annotator_a, annotator_b}:
            raise SystemExit("adjudicator must be a distinct third person")
        adjudicated = {row["response_id"]: row for row in rows_c}
        unresolved = sorted(set(disagreements) - set(adjudicated))
        if not unresolved:
            final = {
                identifier: adjudicated.get(identifier, first[identifier])
                for identifier in sorted(packet_ids)
            }

    payload = {
        "schema": "crane-diagnostic-annotation-adjudication/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETE" if final is not None else "AWAITING_ADJUDICATION",
        "packet": display_path(packet_path),
        "packet_responses": len(packet_ids),
        "annotators": sorted((annotator_a, annotator_b)),
        "agreement": report,
        "disagreements": disagreements,
        "unresolved_disagreements": unresolved,
        "evidence_problem_quarantined_responses": quarantined,
        "condition_key_joined": False,
        "labels": final,
    }
    output_path = (ROOT / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in payload.items() if key != "labels"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
