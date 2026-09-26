#!/usr/bin/env python3
"""Build the one-shot held-out qualification extension for the focused endpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


FAMILIES = [
    {
        "id": "geometry",
        "question": "What bounded route restriction is supported, what measurement establishes it, how did the action end, and what stronger conclusion remains unproven?",
        "evidence": [
            {"id": "gx-1", "fact": "The reconstructed opening was 0.82 m wide at corridor gate G-17."},
            {"id": "gx-2", "fact": "The active 0.94 m envelope had no modeled connection through G-17; a 0.70 m comparison envelope restored modeled connectivity."},
            {"id": "gx-3", "fact": "A retained path used the longer east aisle and the action succeeded at 63.4 s."},
            {"id": "gx-4", "fact": "The record does not establish global physical infeasibility, obstacle identity, or exact Nav2 consumption."},
        ],
        "units": [
            ("u-mechanism", "A configuration-specific geometric restriction in the retained navigation model is identified."),
            ("u-measurement", "The 0.82 m opening is compared with the active 0.94 m and comparison 0.70 m envelopes at G-17."),
            ("u-outcome", "The retained path used the east aisle and the action succeeded at 63.4 s."),
            ("u-limit", "Global physical infeasibility, obstacle identity, and exact Nav2 consumption remain unproven."),
        ],
        "parts": {
            "mechanism": "The reconstruction supports a configuration-specific geometric restriction at G-17.",
            "measurement": "Its 0.82 m opening was below the active 0.94 m envelope, which had no modeled connection, while a 0.70 m comparison envelope restored connectivity.",
            "outcome": "The retained path used the longer east aisle and the action succeeded at 63.4 s.",
            "limit": "This does not prove global physical infeasibility, obstacle identity, or exact Nav2 consumption.",
        },
    },
    {
        "id": "persistent",
        "question": "What execution mechanism is supported, what healthy-versus-event comparison establishes it, how did the action end, and what unique cause remains unresolved?",
        "evidence": [
            {"id": "px-1", "fact": "Healthy interval 0--5 s had median command 0.28 m/s and median measured speed 0.27 m/s."},
            {"id": "px-2", "fact": "During 14--23 s, median delivered command was 0.28 m/s and median measured speed was 0.01 m/s."},
            {"id": "px-3", "fact": "The action aborted at 47.8 s."},
            {"id": "px-4", "fact": "No retained measurement uniquely identifies actuator rejection, obstruction, collision, or slip, and delivery does not prove Nav2 consumption."},
        ],
        "units": [
            ("u-mechanism", "A persistent command-to-motion discrepancy is identified."),
            ("u-measurement", "The 0--5 s healthy 0.28/0.27 m/s comparison is contrasted with the 14--23 s 0.28/0.01 m/s comparison."),
            ("u-outcome", "The action aborted at 47.8 s."),
            ("u-limit", "A unique actuator, obstruction, collision, slip, or Nav2-consumption cause remains unresolved."),
        ],
        "parts": {
            "mechanism": "The retained streams establish a persistent command-to-motion discrepancy.",
            "measurement": "Healthy 0--5 s medians were 0.28 m/s commanded and 0.27 m/s measured, versus 0.28 m/s commanded and 0.01 m/s measured during 14--23 s.",
            "outcome": "The action aborted at 47.8 s.",
            "limit": "The record does not uniquely identify actuator rejection, obstruction, collision, slip, or Nav2 consumption.",
        },
    },
    {
        "id": "recovery",
        "question": "What discrepancy occurred, what measurement shows response recovery, what was the outcome, and what does event order not prove?",
        "evidence": [
            {"id": "rx-1", "fact": "During 9--16 s, median delivered command was 0.33 m/s and median measured speed was 0.00 m/s."},
            {"id": "rx-2", "fact": "During 20--21 s, median measured speed was 0.31 m/s for a 0.32 m/s command, a response ratio of 0.97."},
            {"id": "rx-3", "fact": "The action succeeded at 58.2 s."},
            {"id": "rx-4", "fact": "The recorded ordering does not establish that recovery caused success or identify the unique physical cause of the earlier discrepancy."},
        ],
        "units": [
            ("u-mechanism", "A command-to-motion discrepancy followed by measured response recovery is identified."),
            ("u-measurement", "The 9--16 s 0.33/0.00 m/s discrepancy and 20--21 s 0.32/0.31 m/s recovered response ratio 0.97 are communicated."),
            ("u-outcome", "The action succeeded at 58.2 s."),
            ("u-limit", "Event order does not prove that recovery caused success or establish the unique earlier physical cause."),
        ],
        "parts": {
            "mechanism": "The streams show a command-to-motion discrepancy followed by measured response recovery.",
            "measurement": "The 9--16 s medians were 0.33 m/s commanded and 0.00 m/s measured; at 20--21 s they were 0.32 and 0.31 m/s, a 0.97 response ratio.",
            "outcome": "The action succeeded at 58.2 s.",
            "limit": "The ordering does not prove that recovery caused success or establish the unique physical cause of the earlier discrepancy.",
        },
    },
]


def expected(statuses: dict[str, str], *, disposition: str) -> dict:
    return {
        "judgment_status": "resolved",
        "answerability": "answerable",
        "material_error": False,
        "disposition": disposition,
        "mechanism_identification": "correct",
        "correct_abstention": statuses["u-limit"] == "covered",
        "causal_overclaim": False,
        "evidence_problem": False,
        "required_unit_statuses": statuses,
    }


def build_suite() -> dict:
    cases = []
    variants = (
        ("full-a", None),
        ("full-b", None),
        ("full-c", None),
        ("omit-measurement", "measurement"),
        ("omit-outcome", "outcome"),
        ("omit-limit", "limit"),
    )
    part_to_unit = {
        "mechanism": "u-mechanism",
        "measurement": "u-measurement",
        "outcome": "u-outcome",
        "limit": "u-limit",
    }
    for family_index, family in enumerate(FAMILIES, 1):
        for variant_index, (variant, omitted) in enumerate(variants, 1):
            order = ("mechanism", "measurement", "outcome", "limit")
            text = " ".join(family["parts"][part] for part in order if part != omitted)
            statuses = {
                unit_id: ("omitted" if part == omitted else "covered")
                for part, unit_id in part_to_unit.items()
            }
            cases.append(
                {
                    "case_id": f"Q12CX{family_index:02d}{variant_index:02d}",
                    "split": "heldout",
                    "rubric": "diagnostic",
                    "accuracy_eligible": True,
                    "family": family["id"],
                    "variant": variant,
                    "question": family["question"],
                    "evidence_completeness": "Complete for the four declared essential units; no evaluator-only facts are supplied.",
                    "allowed_evidence": family["evidence"],
                    "required_units": [
                        {"unit_id": unit_id, "text": unit_text}
                        for unit_id, unit_text in family["units"]
                    ],
                    "complete_endpoint_unit_ids": [unit_id for unit_id, _ in family["units"]],
                    "scored_core_fields": [
                        "judgment_status",
                        "answerability",
                        "material_error",
                        "disposition",
                        "mechanism_identification",
                        "correct_abstention",
                        "causal_overclaim",
                        "evidence_problem",
                    ],
                    "candidate_answer": text,
                    "expected": expected(
                        statuses,
                        disposition="full" if omitted is None else "partial",
                    ),
                }
            )
    return {
        "schema": "crane-luna-complete-endpoint-extension-suite/v1",
        "suite_id": "luna-v12-complete-endpoint-extension-v1",
        "declared_utc": "2026-09-26T13:00:00Z",
        "status": "FRESH_UNEXECUTED_AT_DECLARATION",
        "purpose": "One-shot qualification of complete focused endpoint scoring under unchanged Luna v12 settings.",
        "thresholds": {
            "minimum_complete_endpoint_accuracy": 0.90,
            "minimum_unit_coverage_accuracy": 0.95,
            "minimum_core_field_accuracy": 0.95,
            "maximum_false_rejection_rate": 0.12,
            "maximum_false_acceptance_rate": 0.12,
            "maximum_errors_per_omission_category": 1,
            "call_failures_allowed": 0,
        },
        "cases": cases,
    }


def validate(suite: dict) -> None:
    cases = suite["cases"]
    if len(cases) != 18 or len({item["case_id"] for item in cases}) != 18:
        raise ValueError("complete-endpoint suite inventory mismatch")
    if {item["family"] for item in cases} != {item["id"] for item in FAMILIES}:
        raise ValueError("complete-endpoint family mismatch")
    for case in cases:
        unit_ids = [item["unit_id"] for item in case["required_units"]]
        if unit_ids != case["complete_endpoint_unit_ids"]:
            raise ValueError(f"{case['case_id']}: endpoint unit binding mismatch")
        if set(case["expected"]["required_unit_statuses"]) != set(unit_ids):
            raise ValueError(f"{case['case_id']}: expected unit mismatch")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing suite: {args.output}")
    suite = build_suite()
    validate(suite)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(suite, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
