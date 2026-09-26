#!/usr/bin/env python3
"""Build the bounded Luna-v9 prompt-development suite from exposed v8 cases."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/explanation_fidelity/qualification/luna-model-judge-v8-cases.json"
SELECTED = (
    "Q8H01S", "Q8H01E", "Q8H03S", "Q8H03E", "Q8H04S", "Q8H04E",
    "Q8H10S", "Q8H10E", "Q8H11S", "Q8H11E", "Q8H18S", "Q8H18E",
    "Q8H20S", "Q8H20E", "Q8H24S", "Q8H24E",
)


CORRECTIONS = {
    "Q8H01E": {
        "disposition": "nonanswer",
        "mechanism_identification": "incorrect",
        "required_unit_statuses": {"u-mech": "omitted", "u-limit": "incorrect"},
    },
    "Q8H03E": {
        "disposition": "partial",
        "mechanism_identification": "correct",
        "required_unit_statuses": {"u-mech": "covered", "u-limit": "incorrect"},
    },
    "Q8H04E": {
        "disposition": "partial",
        "mechanism_identification": "incorrect",
        "required_unit_statuses": {"u-mech": "covered", "u-limit": "incorrect"},
    },
    "Q8H10E": {
        "disposition": "partial",
        "mechanism_identification": "correct",
        "required_unit_statuses": {"u-mech": "covered", "u-limit": "incorrect"},
    },
    "Q8H11E": {
        "disposition": "nonanswer",
        "mechanism_identification": "incorrect",
        "required_unit_statuses": {"u-mech": "incorrect", "u-limit": "incorrect"},
    },
    "Q8H18E": {
        "disposition": "nonanswer",
        "mechanism_identification": "incorrect",
        "required_unit_statuses": {"u-mech": "incorrect", "u-limit": "incorrect"},
    },
    "Q8H20E": {
        "disposition": "nonanswer",
        "mechanism_identification": "incorrect",
        "required_unit_statuses": {"u-mech": "incorrect", "u-limit": "incorrect"},
    },
    "Q8H24E": {
        "disposition": "nonanswer",
        "mechanism_identification": "incorrect",
        "required_unit_statuses": {"u-mech": "incorrect", "u-limit": "incorrect"},
    },
}


def build() -> dict:
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    by_id = {case["case_id"]: case for case in source["cases"]}
    cases = []
    for index, source_id in enumerate(SELECTED, 1):
        case = copy.deepcopy(by_id[source_id])
        case["source_case_id"] = source_id
        case["case_id"] = f"Q9D{index:02d}"
        case["split"] = "development"
        case["accuracy_eligible"] = True
        case["composite_eligible"] = True
        case.pop("presentation_pair_id", None)
        case.pop("protected_core_fields", None)
        if source_id in CORRECTIONS:
            case["expected"].update(CORRECTIONS[source_id])
        cases.append(case)
    return {
        "schema": "crane-luna-judge-development-suite/v9",
        "status": "DEVELOPMENT_ONLY_EXPOSED_CASES",
        "source_suite": str(SOURCE.relative_to(ROOT)),
        "reference_audit": (
            "Project-authored atomic-unit audit performed after v8 was closed; corrections are "
            "development-only and do not reinterpret or qualify v8."
        ),
        "thresholds": {
            "minimum_composite_accuracy": 0.95,
            "minimum_required_unit_accuracy": 0.95,
            "minimum_core_semantic_field_accuracy": 0.95,
            "maximum_false_rejection_rate": 0.05,
            "maximum_false_acceptance_rate": 0.05,
            "protected_test_failures_allowed": 0,
        },
        "cases": cases,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
