#!/usr/bin/env python3
"""Build a condition-blind, disagreement-only handoff for a distinct adjudicator."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable


sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_diagnostic_annotation_form import build_form as build_diagnostic_form
from build_diagnostic_annotation_form import read_jsonl as read_diagnostic_packet
from build_legacy_annotation_form import build_form as build_legacy_form
from build_legacy_annotation_form import read_jsonl as read_legacy_packet


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = {
    "legacy": "crane-explain-annotation-adjudication/v1",
    "diagnostic": "crane-diagnostic-annotation-adjudication/v1",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_report(path: Path, rubric: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("agreement report is not a JSON object")
    if value.get("schema") != SCHEMAS[rubric]:
        raise ValueError(f"agreement report does not use the {rubric} schema")
    if value.get("status") != "AWAITING_ADJUDICATION":
        raise ValueError("agreement report is not awaiting adjudication")
    if value.get("condition_key_joined") is not False:
        raise ValueError("agreement report already claims a condition-key join")
    if value.get("labels") is not None:
        raise ValueError("agreement report unexpectedly contains final labels")
    disagreements = value.get("disagreements")
    unresolved = value.get("unresolved_disagreements")
    if (
        not isinstance(disagreements, list)
        or not disagreements
        or len(disagreements) != len(set(disagreements))
        or not all(isinstance(identifier, str) and identifier for identifier in disagreements)
    ):
        raise ValueError("agreement report has no valid disagreement inventory")
    if unresolved != disagreements:
        raise ValueError("agreement report disagreement inventories differ")
    return value


def validate_report_packet_binding(
    report: dict[str, Any], packet_path: Path, packet_ids: set[str]
) -> list[str]:
    report_packet = report.get("packet")
    if not isinstance(report_packet, str) or not report_packet:
        raise ValueError("agreement report does not identify its packet")
    reported_path = Path(report_packet)
    if not reported_path.is_absolute():
        reported_path = (ROOT / reported_path).resolve()
    else:
        reported_path = reported_path.resolve()
    if reported_path != packet_path:
        raise ValueError("agreement report and supplied packet paths differ")
    disagreements = report["disagreements"]
    unknown = set(disagreements) - packet_ids
    if unknown:
        raise ValueError(f"agreement report names unknown responses: {sorted(unknown)}")
    return disagreements


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def build_handoff(
    *,
    rubric: str,
    packet_path: Path,
    agreement_path: Path,
    output_dir: Path,
    adjudicator_id: str,
) -> dict[str, Any]:
    if rubric not in SCHEMAS:
        raise ValueError(f"unsupported rubric: {rubric}")
    if not adjudicator_id.strip():
        raise ValueError("adjudicator_id must be non-empty")
    evaluator_root = (ROOT / "data" / "evaluator_only").resolve()
    if output_dir == evaluator_root or evaluator_root in output_dir.parents:
        raise ValueError("output directory must not be under data/evaluator_only/")
    if output_dir.exists():
        raise FileExistsError("refusing to overwrite an existing adjudication handoff")

    reader: Callable[[Path], list[dict[str, Any]]]
    form_builder: Callable[[list[dict[str, Any]], str | None], list[dict[str, Any]]]
    guide: str
    if rubric == "legacy":
        reader = read_legacy_packet
        form_builder = build_legacy_form
        guide = "docs/ANNOTATION_GUIDE.md"
    else:
        reader = read_diagnostic_packet
        form_builder = build_diagnostic_form
        guide = "docs/DIAGNOSTIC_ANNOTATION_GUIDE.md"

    packet_rows = reader(packet_path)
    by_id = {row["response_id"]: row for row in packet_rows}
    if len(by_id) != len(packet_rows):
        raise ValueError("packet contains duplicate response IDs")
    report = load_report(agreement_path, rubric)
    disagreements = validate_report_packet_binding(report, packet_path, set(by_id))
    disagreement_ids = set(disagreements)
    subset = [row for row in packet_rows if row["response_id"] in disagreement_ids]
    if len(subset) != len(disagreements):
        raise ValueError("failed to materialize every disagreement exactly once")
    form = form_builder(subset, adjudicator_id)

    output_dir.mkdir(parents=True)
    packet_output = output_dir / "packet.jsonl"
    form_output = output_dir / "form.jsonl"
    guide_output = output_dir / "guide.md"
    readme_output = output_dir / "README.md"
    manifest_output = output_dir / "manifest.json"
    write_jsonl(packet_output, subset)
    write_jsonl(form_output, form)
    guide_source = ROOT / guide
    guide_output.write_text(guide_source.read_text(encoding="utf-8"), encoding="utf-8")
    readme_output.write_text(
        "# Blinded disagreement adjudication\n\n"
        "Read `guide.md` and use only the files in this directory. You are the distinct third "
        "adjudicator. Do not request condition keys, model identities, verifier/fallback "
        "metadata, either annotator's labels, or evaluator-only files.\n\n"
        "Review every row in `packet.jsonl`, replace every unset judgment in `form.jsonl`, "
        "and return only the completed form. Do not add or remove response IDs. If the "
        "evidence, question, or reference is inconsistent, set `evidence_problem=true` and "
        "explain why rather than guessing.\n",
        encoding="utf-8",
    )
    manifest = {
        "schema": "crane-adjudication-handoff/v1",
        "rubric": rubric,
        "status": "BLINDED_DISAGREEMENT_ONLY_HANDOFF",
        "source_packet": display_path(packet_path),
        "source_packet_sha256": digest(packet_path),
        "agreement_report_sha256": digest(agreement_path),
        "guide_source": guide,
        "guide_sha256": digest(guide_output),
        "response_count": len(subset),
        "response_ids": [row["response_id"] for row in subset],
        "packet_sha256": digest(packet_output),
        "form_sha256": digest(form_output),
        "condition_key_included": False,
        "prior_annotator_labels_included": False,
        "prior_annotator_identities_included": False,
    }
    manifest_output.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rubric", required=True, choices=sorted(SCHEMAS))
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--agreement", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--adjudicator-id", required=True)
    args = parser.parse_args()

    packet_path = (ROOT / args.packet).resolve(strict=True)
    agreement_path = (ROOT / args.agreement).resolve(strict=True)
    output_dir = (ROOT / args.output_dir).resolve()
    try:
        manifest = build_handoff(
            rubric=args.rubric,
            packet_path=packet_path,
            agreement_path=agreement_path,
            output_dir=output_dir,
            adjudicator_id=args.adjudicator_id,
        )
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
