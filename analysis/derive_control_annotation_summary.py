#!/usr/bin/env python3
"""Derive a model-strength annotation file's summary block from its per-response labels.

The frozen Luna control's annotation file carries both per-episode labels and an aggregate
``summary`` that the selection rule reads. Computing that aggregate by hand invites arithmetic
error in exactly the numbers a selection turns on, so the Claude arm derives it instead, and
cross-checks the totals against the frozen unit inventories.

This is a development-annotation utility. It does not read sealed data and does not score anything.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

WORKSPACE = Path(__file__).resolve().parent.parent
CONDITIONS = ("F", "G", "H")

# Frozen inventory sizes from docs/ANNOTATION_GUIDE.md.
UNITS_PER_QUESTION = {"recovery-mechanism": 8, "failure-cause": 5}


def derive_summary(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    responses = {condition: 0 for condition in CONDITIONS}
    material_errors = {condition: 0 for condition in CONDITIONS}
    specificity_correct = {condition: 0 for condition in CONDITIONS}
    substantive = {condition: 0 for condition in CONDITIONS}
    specificity_total = 0

    for episode in episodes:
        for question_kind, labels in sorted(episode["questions"].items()):
            expected_total = UNITS_PER_QUESTION[question_kind]
            specificity_total += expected_total
            if sorted(labels) != sorted(CONDITIONS):
                raise SystemExit(
                    f"{episode['episode_id']} {question_kind}: expected exactly F/G/H labels"
                )
            for condition, label in labels.items():
                if label["specificity_total"] != expected_total:
                    raise SystemExit(
                        f"{episode['episode_id']} {question_kind} {condition}: "
                        f"specificity_total {label['specificity_total']} is not the frozen "
                        f"inventory size {expected_total}"
                    )
                if label["specificity_correct"] > expected_total:
                    raise SystemExit(
                        f"{episode['episode_id']} {question_kind} {condition}: "
                        "specificity_correct exceeds the inventory"
                    )
                if label["material_error"] and not label.get("error_categories"):
                    raise SystemExit(
                        f"{episode['episode_id']} {question_kind} {condition}: "
                        "material_error recorded without a category"
                    )
                if label["material_error"] and not label.get("rationale", "").strip():
                    raise SystemExit(
                        f"{episode['episode_id']} {question_kind} {condition}: "
                        "material_error recorded without a rationale"
                    )
                responses[condition] += 1
                material_errors[condition] += int(bool(label["material_error"]))
                specificity_correct[condition] += label["specificity_correct"]
                substantive[condition] += int(bool(label.get("substantive_answer", True)))

    counts = set(responses.values())
    if len(counts) != 1:
        raise SystemExit(f"conditions have unequal response counts: {responses}")
    per_condition = counts.pop()
    return {
        "responses_per_condition": per_condition,
        "material_errors": material_errors,
        "specificity_correct": specificity_correct,
        "specificity_total": specificity_total,
        "substantive_coverage": {
            condition: substantive[condition] / per_condition for condition in CONDITIONS
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    payload = json.loads((WORKSPACE / args.annotation).read_text(encoding="utf-8"))
    payload["summary"] = derive_summary(payload["episodes"])
    output_path = WORKSPACE / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
