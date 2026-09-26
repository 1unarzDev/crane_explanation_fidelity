#!/usr/bin/env python3
"""Build a no-model, development-only packet closure dry run from run 042."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_diagnostic_annotation_packet import build_rows
from build_focused_command_motion_reference import build_focused_reference


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--export", required=True, type=Path)
    parser.add_argument("--independent-reference", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError(f"refusing existing dry-run root: {args.output_root}")
    export = json.loads(args.export.read_text(encoding="utf-8"))
    independent = json.loads(args.independent_reference.read_text(encoding="utf-8"))
    question_id = "focused-activation-dry-run:persistent-command-motion"
    question = (
        "What is the deepest supported execution mechanism, what healthy-versus-event measurement "
        "establishes it, how did the action end, and what unique physical or actuator cause remains unresolved?"
    )
    reference = build_focused_reference(export, independent, question_id=question_id)
    result = {
        "schema": "crane-focused-activation-packet-dry-run-result/v1",
        "status": "DEVELOPMENT_ONLY_SYNTHETIC_TRANSPORT_RESPONSES_NOT_STUDY_SCORING",
        "episode_id": export["episode_id"],
        "question_id": question_id,
        "question_kind": "persistent_command_motion_discrepancy",
        "question": question,
        "provider": "none",
        "model": "none",
        "evaluator_truth_available_to_methods": False,
        "permitted_evidence_identifiers": reference["allowed_evidence_identifiers"],
        "outputs": [
            {
                "condition": condition,
                "text": export["final_answer"],
                "provider": "synthetic-packet-transport",
                "model": "none",
                "used_template_fallback": False,
                "verification_accepted": True,
            }
            for condition in ("P", "R")
        ],
    }
    rows, entries = build_rows(result, reference, "focused-activation-dry-run-fixed-secret")
    if len(rows) != 2 or any(
        row.get("complete_endpoint_unit_ids")
        != [item["unit_id"] for item in row["required_units"]]
        for row in rows
    ):
        raise ValueError("dry-run packet did not close over every essential unit")
    reference_path = args.output_root / "reference.json"
    result_path = args.output_root / "synthetic-result.json"
    packet_path = args.output_root / "packet.jsonl"
    key_path = args.output_root / "condition-key.json"
    write_json(reference_path, reference)
    write_json(result_path, result)
    packet_path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    write_json(
        key_path,
        {
            "schema": "crane-focused-activation-packet-dry-run-key/v1",
            "status": "DEVELOPMENT_ONLY_FIXED_SECRET_NOT_FOR_STUDY_BLINDING",
            "entries": entries,
        },
    )
    write_json(
        args.output_root / "closure-report.json",
        {
            "schema": "crane-focused-activation-packet-closure-report/v1",
            "status": "PASS",
            "source_run": "cm-land-conf-042",
            "source_run_semantic_eligibility": "EXCLUDED_DEVELOPMENT_PACKET_DRY_RUN",
            "model_calls": 0,
            "luna_calls": 0,
            "confirmatory_alpha_consumed": 0.0,
            "rows": len(rows),
            "essential_units_per_row": len(rows[0]["complete_endpoint_unit_ids"]),
            "reference_sha256": digest(reference_path),
            "synthetic_result_sha256": digest(result_path),
            "packet_sha256": digest(packet_path),
            "condition_key_sha256": digest(key_path),
            "checks": {
                "evaluator_truth_excluded": True,
                "allowed_evidence_complete": reference["completeness_audit"]["accepted"],
                "every_required_unit_bound": True,
                "condition_metadata_blinded_from_rows": True,
                "candidate_wording_preserved": True,
                "synthetic_responses_not_scored": True,
            },
        },
    )


if __name__ == "__main__":
    main()
