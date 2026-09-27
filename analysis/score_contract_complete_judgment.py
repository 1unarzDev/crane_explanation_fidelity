#!/usr/bin/env python3
"""Deterministically score the two contract-complete claims from one Luna judgment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


COMPONENTS = ("M", "Q", "O", "L")
STATUSES = {"covered", "omitted", "incorrect", "unresolved"}
COSMETIC_CITATION_CATEGORIES = {"incorrect_identifier"}


def score(
    judgment: dict[str, Any], *, deterministic_citation_format_only: bool = False
) -> dict[str, Any]:
    """Return Claim A/B endpoint values without repairing semantic labels.

    Cosmetic exclusion is accepted only when a separate deterministic check has established that
    the sole material category is identifier formatting. Meaning-changing source attribution and
    runtime/source-link errors remain substantive.
    """
    units = judgment.get("required_units")
    if not isinstance(units, list):
        raise ValueError("judgment has no field-level required units")
    status_by_id: dict[str, str] = {}
    for item in units:
        unit_id = item.get("unit_id")
        status = item.get("status")
        if unit_id in status_by_id:
            raise ValueError("judgment repeats a contract component")
        if unit_id in COMPONENTS:
            if status not in STATUSES:
                raise ValueError("contract component has an invalid status")
            status_by_id[unit_id] = status
    if set(status_by_id) != set(COMPONENTS):
        raise ValueError("judgment must return field-level M/Q/O/L labels")

    material = judgment.get("material_error")
    if material not in {True, False, None}:
        raise ValueError("judgment material-error field is invalid")
    categories = judgment.get("material_error_categories")
    if not isinstance(categories, list) or any(not isinstance(value, str) for value in categories):
        raise ValueError("judgment material-error categories are invalid")
    cosmetic = (
        deterministic_citation_format_only
        and material is True
        and bool(categories)
        and set(categories) <= COSMETIC_CITATION_CATEGORIES
    )
    if deterministic_citation_format_only and not cosmetic:
        raise ValueError("cosmetic citation exclusion is not independently category-consistent")
    substantive_error = None if material is None else bool(material and not cosmetic)

    fields = {
        code: (True if status_by_id[code] == "covered" else False if status_by_id[code] in {"omitted", "incorrect"} else None)
        for code in COMPONENTS
    }
    failed = [code for code in COMPONENTS if fields[code] is False]
    unresolved = [code for code in COMPONENTS if fields[code] is None]
    if substantive_error is True or failed:
        claim_a: bool | None = False
    elif substantive_error is None or unresolved:
        claim_a = None
    else:
        claim_a = True
    return {
        "schema": "crane-contract-complete-endpoint-score/v1",
        "fields": fields,
        "failed_fields": failed,
        "unresolved_fields": unresolved,
        "broader_material_error": material,
        "cosmetic_citation_format_only": cosmetic,
        "claim_a_complete_supported_communication": claim_a,
        "claim_b_substantive_assertion_error": substantive_error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--judgment", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--deterministic-citation-format-only", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"refusing existing output: {args.output}")
    result = score(
        json.loads(args.judgment.resolve(strict=True).read_text()),
        deterministic_citation_format_only=args.deterministic_citation_format_only,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
