#!/usr/bin/env python3
"""Create a validator-shaped, condition-blind form for the sealed legacy packet.

The frozen rubric lists three grouping fields that the blinded packet intentionally
does not disclose.  They are system metadata, not human judgments.  This tool uses
an explicit sentinel until the evaluator-only key is joined after adjudication and
uses the opaque response ID as the condition-blinded identifier.  It never reads
the evaluator-only key.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BLINDED_METADATA_SENTINEL = "BLINDED_PENDING_KEY_JOIN"
OPAQUE_RESPONSE_ID = re.compile(r"[0-9a-f]{24}\Z")
FORM_FIELDS = (
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
PREFILLED_FIELDS = frozenset(
    {
        "response_id",
        "episode_id",
        "scenario_family",
        "question_kind",
        "condition_blinded_id",
        "answerable_units_total",
        "annotator_id",
    }
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

    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, packet_row in enumerate(packet_rows):
        response_id = packet_row.get("response_id")
        if not isinstance(response_id, str) or OPAQUE_RESPONSE_ID.fullmatch(response_id) is None:
            raise ValueError(f"packet row {index} does not have an opaque response_id")
        if response_id in seen:
            raise ValueError(f"duplicate packet response_id: {response_id}")
        seen.add(response_id)
        question_kind = packet_row.get("question_kind")
        if question_kind not in {"recovery-mechanism", "failure-cause"}:
            raise ValueError(f"packet row {index} has an unsupported question_kind")
        inventory = packet_row.get("gold_unit_inventory")
        total = packet_row.get("answerable_units_total")
        if (
            not isinstance(inventory, list)
            or not all(isinstance(unit, str) and unit.strip() for unit in inventory)
            or not isinstance(total, int)
            or isinstance(total, bool)
            or total != len(inventory)
        ):
            raise ValueError(f"packet row {index} has an invalid unit inventory")

        row = {field: None for field in FORM_FIELDS}
        row.update(
            {
                "response_id": response_id,
                "episode_id": BLINDED_METADATA_SENTINEL,
                "scenario_family": BLINDED_METADATA_SENTINEL,
                "question_kind": question_kind,
                "condition_blinded_id": response_id,
                "answerable_units_total": total,
                "annotator_id": annotator_id,
            }
        )
        output.append(row)
    return output


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
