#!/usr/bin/env python3
"""Create a blank, condition-blind annotation form from a diagnostic packet.

The form contains only opaque response identifiers and rubric fields.  It never
reads the evaluator-only key and deliberately omits packet evidence and response
text: annotators review those in the packet while recording judgments here.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OPAQUE_RESPONSE_ID = re.compile(r"[0-9a-f]{24}\Z")
JUDGMENT_FIELDS = (
    "supported_diagnostic_success",
    "material_error",
    "error_categories",
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
FORM_FIELDS = (
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"packet line {line_number} is not an object")
        rows.append(value)
    if not rows:
        raise ValueError("packet is empty")
    return rows


def build_form(
    packet_rows: list[dict[str, Any]], annotator_id: str | None = None
) -> list[dict[str, Any]]:
    if annotator_id is not None and not annotator_id.strip():
        raise ValueError("annotator_id must be non-empty when supplied")

    form: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, packet_row in enumerate(packet_rows):
        if packet_row.get("schema") != "crane-diagnostic-annotation-row/v1":
            raise ValueError(f"packet row {index} has an unsupported schema")
        response_id = packet_row.get("response_id")
        if not isinstance(response_id, str) or OPAQUE_RESPONSE_ID.fullmatch(response_id) is None:
            raise ValueError(f"packet row {index} does not have an opaque response_id")
        if response_id in seen:
            raise ValueError(f"duplicate packet response_id: {response_id}")
        seen.add(response_id)
        required_units = packet_row.get("required_units")
        if not isinstance(required_units, list) or not all(
            isinstance(unit, str) and unit.strip() for unit in required_units
        ):
            raise ValueError(f"packet row {index} has an invalid required_units inventory")

        row: dict[str, Any] = {
            "response_id": response_id,
            "annotator_id": annotator_id,
            **{field: None for field in JUDGMENT_FIELDS},
            "required_units_total": len(required_units),
        }
        # Keep a stable field order for reviewers editing JSONL by hand.
        form.append({field: row[field] for field in FORM_FIELDS})
    return form


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--annotator-id")
    args = parser.parse_args()

    packet_path = (ROOT / args.packet).resolve(strict=True)
    output_path = (ROOT / args.output).resolve()
    evaluator_root = (ROOT / "data" / "evaluator_only").resolve()
    if evaluator_root in output_path.parents:
        parser.error("--output must not be under data/evaluator_only/")
    if output_path.exists():
        raise SystemExit("refusing to overwrite an existing annotation form")

    rows = build_form(read_jsonl(packet_path), args.annotator_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    print(json.dumps({"form": str(output_path), "responses": len(rows)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
