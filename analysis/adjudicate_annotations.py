#!/usr/bin/env python3
"""Validate two independent annotation passes, report agreement, and adjudicate disagreements.

``docs/ANNOTATION_GUIDE.md`` requires two independent annotators on every sealed response, raw
agreement and Cohen's kappa for material error, substantive answer, and correct abstention, plus
agreement on unit-level coverage, and a third adjudicator who sees only the guide and the allowed
evidence. This enforces that procedure mechanically.

The tool refuses to compute agreement on a pass that is incomplete, that annotates a response the
packet does not contain, or that was produced by the same annotator twice. It never joins the
condition key: the join happens only in a separate, explicitly requested step after adjudication,
so a partially adjudicated dataset cannot be scored by condition.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent

REQUIRED_FIELDS = (
    "response_id",
    "episode_id",
    "scenario_family",
    "question_kind",
    "condition_blinded_id",
    "material_error",
    "error_categories",
    "disposition",
    "substantive_answer",
    "requested_conclusion_answerable",
    "correct_abstention",
    "answerable_units_total",
    "answerable_units_correct",
    "claim_count",
    "unsupported_claim_count",
    "source_reference_count",
    "correct_source_reference_count",
    "source_references_total_answerable",
    "physical_evidence_claim_count",
    "correct_physical_evidence_claim_count",
    "causal_overclaim",
    "qualification_correct",
    "evidence_problem",
    "annotator_id",
    "rationale",
)

BINARY_FIELDS = ("material_error", "substantive_answer", "correct_abstention")

DISPOSITIONS = ("full", "partial", "abstained", "nonanswer")

ERROR_CATEGORIES = frozenset(
    {
        "unsupported_fact",
        "contradicted_fact",
        "incorrect_identifier",
        "incorrect_count",
        "incorrect_status",
        "incorrect_comparison",
        "incorrect_source_attribution",
        "incorrect_runtime_source_link",
        "unsupported_mechanism_detail",
        "unsupported_causal_diagnosis",
        "unsupported_counterfactual",
        "incorrect_explanatory_relationship",
        "false_premise_acceptance",
        "incorrect_completeness",
    }
)
BLINDED_METADATA_SENTINEL = "BLINDED_PENDING_KEY_JOIN"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def display_path(path: Path) -> str:
    try:
        return path.relative_to(WORKSPACE).as_posix()
    except ValueError:
        return str(path)


def packet_inventory(packet_rows: list[dict[str, Any]]) -> dict[str, tuple[str, int]]:
    inventory: dict[str, tuple[str, int]] = {}
    for index, row in enumerate(packet_rows):
        identifier = row.get("response_id")
        if not isinstance(identifier, str):
            raise ValueError(f"packet row {index} has no response_id")
        if identifier in inventory:
            raise ValueError(f"duplicate packet response_id: {identifier}")
        question_kind = row.get("question_kind")
        total = row.get("answerable_units_total")
        if not isinstance(question_kind, str) or not isinstance(total, int) or isinstance(total, bool):
            raise ValueError(f"packet row {index} has invalid annotation metadata")
        inventory[identifier] = (question_kind, total)
    return inventory


def validate_pass(
    rows: list[dict[str, Any]],
    packet: set[str] | dict[str, tuple[str, int]],
    label: str,
    *,
    expected_ids: set[str] | None = None,
) -> str:
    """Check one annotator's rows against the guide's required schema."""

    problems = []
    seen: set[str] = set()
    packet_ids = set(packet)
    expected = packet_ids if expected_ids is None else expected_ids
    annotators = {row.get("annotator_id") for row in rows}
    if len(annotators) != 1 or None in annotators:
        shown = sorted(repr(value) for value in annotators)
        problems.append(f"{label}: expected exactly one annotator_id, found {shown}")
    for index, row in enumerate(rows):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            problems.append(f"{label} row {index}: missing fields {missing}")
            continue
        identifier = row["response_id"]
        if identifier in seen:
            problems.append(f"{label}: duplicate response_id {identifier}")
        seen.add(identifier)
        if identifier not in packet_ids:
            problems.append(f"{label}: response_id {identifier} is not in the packet")
            continue
        if identifier not in expected:
            problems.append(f"{label}: unexpected response_id {identifier}")
            continue
        if isinstance(packet, dict):
            question_kind, expected_total = packet[identifier]
            if row["episode_id"] != BLINDED_METADATA_SENTINEL:
                problems.append(f"{label} {identifier}: episode_id must remain blinded")
            if row["scenario_family"] != BLINDED_METADATA_SENTINEL:
                problems.append(f"{label} {identifier}: scenario_family must remain blinded")
            if row["condition_blinded_id"] != identifier:
                problems.append(f"{label} {identifier}: bad condition_blinded_id")
            if row["question_kind"] != question_kind:
                problems.append(f"{label} {identifier}: question_kind differs from packet")
            if row["answerable_units_total"] != expected_total:
                problems.append(f"{label} {identifier}: unit total differs from packet")
        if row["disposition"] not in DISPOSITIONS:
            problems.append(f"{label} {identifier}: bad disposition {row['disposition']!r}")
        unknown = set(row["error_categories"]) - ERROR_CATEGORIES
        if unknown:
            problems.append(f"{label} {identifier}: unknown error categories {sorted(unknown)}")
        if row["material_error"] and not row["error_categories"]:
            problems.append(f"{label} {identifier}: material_error with no category")
        if not row["material_error"] and row["error_categories"]:
            problems.append(f"{label} {identifier}: categories recorded without material_error")
        expected_substantive = row["disposition"] in ("full", "partial")
        if bool(row["substantive_answer"]) != expected_substantive:
            problems.append(
                f"{label} {identifier}: substantive_answer disagrees with disposition"
            )
        if row["answerable_units_correct"] > row["answerable_units_total"]:
            problems.append(f"{label} {identifier}: unit coverage exceeds the inventory")
        if not str(row["rationale"]).strip():
            problems.append(f"{label} {identifier}: empty rationale")
    absent = expected - seen
    if absent:
        problems.append(f"{label}: pass is incomplete; {len(absent)} responses unannotated")
    if problems:
        raise SystemExit("annotation pass rejected:\n  " + "\n  ".join(problems))
    return next(iter(annotators))


def cohen_kappa(first: list[Any], second: list[Any]) -> float | None:
    """Cohen's kappa, or None when it is undefined because one rater used a single category."""

    total = len(first)
    if total == 0:
        return None
    observed = sum(a == b for a, b in zip(first, second)) / total
    counts_first = Counter(first)
    counts_second = Counter(second)
    expected = sum(
        (counts_first[label] / total) * (counts_second[label] / total)
        for label in set(counts_first) | set(counts_second)
    )
    if expected == 1.0:
        return None
    return (observed - expected) / (1.0 - expected)


def agreement(
    first: dict[str, dict[str, Any]], second: dict[str, dict[str, Any]], field: str
) -> dict[str, Any]:
    identifiers = sorted(first)
    a = [first[identifier][field] for identifier in identifiers]
    b = [second[identifier][field] for identifier in identifiers]
    matches = sum(x == y for x, y in zip(a, b))
    return {
        "responses": len(identifiers),
        "raw_agreement": matches / len(identifiers) if identifiers else None,
        "agreements": matches,
        "disagreements": len(identifiers) - matches,
        "cohen_kappa": cohen_kappa(a, b),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--annotator-a", required=True, type=Path)
    parser.add_argument("--annotator-b", required=True, type=Path)
    parser.add_argument(
        "--adjudication",
        type=Path,
        help="third-annotator rows resolving disagreements; required to emit a final label set",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    packet_path = (WORKSPACE / args.packet).resolve()
    inventory = packet_inventory(read_jsonl(packet_path))
    packet_ids = set(inventory)
    rows_a = read_jsonl((WORKSPACE / args.annotator_a).resolve())
    rows_b = read_jsonl((WORKSPACE / args.annotator_b).resolve())
    annotator_a = validate_pass(rows_a, inventory, "annotator-a")
    annotator_b = validate_pass(rows_b, inventory, "annotator-b")
    if annotator_a == annotator_b:
        raise SystemExit("both passes carry the same annotator_id; they are not independent")

    first = {row["response_id"]: row for row in rows_a}
    second = {row["response_id"]: row for row in rows_b}
    report = {field: agreement(first, second, field) for field in BINARY_FIELDS}
    report["disposition"] = agreement(first, second, "disposition")
    report["answerable_units_correct"] = agreement(first, second, "answerable_units_correct")

    disagreements = sorted(
        identifier
        for identifier in packet_ids
        if any(first[identifier][field] != second[identifier][field] for field in BINARY_FIELDS)
        or first[identifier]["disposition"] != second[identifier]["disposition"]
        or first[identifier]["answerable_units_correct"]
        != second[identifier]["answerable_units_correct"]
    )
    quarantined = sorted(
        identifier
        for identifier in packet_ids
        if first[identifier]["evidence_problem"] or second[identifier]["evidence_problem"]
    )

    final: dict[str, dict[str, Any]] | None = (
        {identifier: first[identifier] for identifier in sorted(packet_ids)}
        if not disagreements
        else None
    )
    unresolved = list(disagreements)
    if args.adjudication is not None:
        if not disagreements:
            raise SystemExit("adjudication was supplied but the annotators had no disagreements")
        rows_c = read_jsonl((WORKSPACE / args.adjudication).resolve())
        adjudicator = validate_pass(
            rows_c,
            inventory,
            "adjudicator",
            expected_ids=set(disagreements),
        )
        if adjudicator in {annotator_a, annotator_b}:
            raise SystemExit("adjudicator must be a distinct third annotator")
        adjudicated = {row["response_id"]: row for row in rows_c}
        unresolved = sorted(set(disagreements) - set(adjudicated))
        if not unresolved:
            final = {
                identifier: adjudicated.get(identifier, first[identifier])
                for identifier in sorted(packet_ids)
            }

    payload = {
        "schema": "crane-explain-annotation-adjudication/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "COMPLETE" if final is not None else "AWAITING_ADJUDICATION",
        "packet": display_path(packet_path),
        "packet_responses": len(packet_ids),
        "annotators": sorted((annotator_a, annotator_b)),
        "agreement": report,
        "disagreement_count": len(disagreements),
        "disagreements": disagreements,
        "unresolved_disagreements": unresolved,
        "evidence_problem_quarantined_responses": quarantined,
        "quarantine_rule": "evidence_problem quarantines the whole episode, never one condition",
        "condition_key_joined": False,
        "note": (
            "Labels here are still blinded. Joining the evaluator-only key and scoring by "
            "condition is a separate step and must not run while disagreements are unresolved."
        ),
        "labels": final,
    }
    output_path = (WORKSPACE / args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "labels"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
