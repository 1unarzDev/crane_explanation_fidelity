#!/usr/bin/env python3
"""Summarize transparent development annotations without inferential overclaiming."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("annotation", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.annotation.read_text(encoding="utf-8"))
    gold = {
        question: set(item["coverage_units"])
        for question, item in source["questions"].items()
    }
    grouped = defaultdict(list)
    for row in source["annotations"]:
        grouped[row["condition"]].append(row)
    conditions = {}
    for condition, rows in sorted(grouped.items()):
        dispositions = Counter(row["response_disposition"] for row in rows)
        covered = sum(len(set(row["covered_units"]) & gold[row["question"]]) for row in rows)
        possible = sum(len(gold[row["question"]]) for row in rows)
        conditions[condition] = {
            "responses": len(rows),
            "material_errors": sum(row["material_error"] for row in rows),
            "material_error_rate": sum(row["material_error"] for row in rows) / len(rows),
            "substantive_answers": sum(row["substantive_answer"] for row in rows),
            "substantive_answer_coverage": (
                sum(row["substantive_answer"] for row in rows) / len(rows)),
            "dispositions": dict(dispositions),
            "answerable_information_units_covered": covered,
            "answerable_information_units_total": possible,
            "answerable_information_coverage": covered / possible,
            "correct_counterfactual_abstentions": sum(
                row["question"] == "unsupported-counterfactual"
                and row["response_disposition"] == "abstain" for row in rows),
        }
    result = {
        "schema": "crane-explain-development-summary/v1",
        "status": "DEVELOPMENT_ONLY_NO_INFERENTIAL_STATISTICS",
        "independent_episode_count": source["independent_episode_count"],
        "warning": (
            "Question-level rates are descriptive only because all responses share one episode; "
            "no confidence interval, significance test, or power estimate is valid from this sample."
        ),
        "conditions": conditions,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
