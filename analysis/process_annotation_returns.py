#!/usr/bin/env python3
"""Validate returned blinded forms and prepare disagreement-only adjudication handoffs.

This is a coordinator around the existing rubric-specific validators. It never opens an
evaluator-only key, joins a condition, synthesizes a judgment, or changes either returned form.
All output is built transactionally so one invalid packet cannot leave a partial batch that looks
ready for adjudication.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEGACY_CALIBRATION = "legacy-calibration-e043-v1.jsonl"
SEALED_LEGACY = "sealed-primary-v3.jsonl"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_first_row(path: Path) -> dict[str, Any]:
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path} line {line_number} is not an object")
        return value
    raise ValueError(f"{path} is empty")


def rubric(path: Path) -> str:
    row = read_first_row(path)
    if row.get("schema") == "crane-diagnostic-annotation-row/v1":
        return "diagnostic"
    required = {"response_id", "question_kind", "answerable_units_total"}
    if required <= set(row):
        return "legacy"
    raise ValueError(f"cannot identify annotation rubric for {path}")


def jsonl_inventory(path: Path) -> set[str]:
    identifiers: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("response_id"), str):
            raise ValueError(f"{path} line {line_number} has no response_id")
        identifier = row["response_id"]
        if identifier in identifiers:
            raise ValueError(f"{path} repeats response_id {identifier}")
        identifiers.add(identifier)
    if not identifiers:
        raise ValueError(f"{path} is empty")
    return identifiers


def selected_packets(packet_dir: Path, only: list[str]) -> list[Path]:
    available = {path.name: path for path in packet_dir.glob("*.jsonl") if path.is_file()}
    if not available:
        raise ValueError("packet directory has no JSONL packets")
    if only:
        invalid = [name for name in only if Path(name).name != name or not name.endswith(".jsonl")]
        if invalid:
            raise ValueError(f"--only expects packet basenames: {invalid}")
        missing = sorted(set(only) - set(available))
        if missing:
            raise ValueError(f"selected packets are absent: {missing}")
        if len(only) != len(set(only)):
            raise ValueError("--only repeats a packet")
        return [available[name] for name in only]
    return [available[name] for name in sorted(available)]


def require_forms(
    packet_paths: list[Path], form_dir: Path, label: str, *, allow_extra: bool
) -> dict[str, Path]:
    forms = {path.name: path for path in form_dir.glob("*.jsonl") if path.is_file()}
    required = {path.name for path in packet_paths}
    missing = sorted(required - set(forms))
    if missing:
        raise ValueError(f"{label} is missing returned forms: {missing}")
    unexpected = sorted(set(forms) - required)
    if unexpected and not allow_extra:
        raise ValueError(f"{label} has unexpected returned forms: {unexpected}")
    return {name: forms[name] for name in required}


def run_validator(
    *, rubric_name: str, packet: Path, form_a: Path, form_b: Path, output: Path
) -> dict[str, Any]:
    script = (
        ROOT / "analysis/adjudicate_annotations.py"
        if rubric_name == "legacy"
        else ROOT / "analysis/adjudicate_diagnostic_annotations.py"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--packet",
            str(packet),
            "--annotator-a",
            str(form_a),
            "--annotator-b",
            str(form_b),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "validator failed"
        raise ValueError(f"{packet.name}: {detail}")
    report = json.loads(output.read_text(encoding="utf-8"))
    if report.get("condition_key_joined") is not False:
        raise ValueError(f"{packet.name}: validator unexpectedly joined a condition key")
    return report


def process_returns(
    *,
    packet_dir: Path,
    annotator_a_dir: Path,
    annotator_b_dir: Path,
    output_dir: Path,
    adjudicator_id: str,
    calibration_complete: bool,
    only: list[str] | None = None,
) -> dict[str, Any]:
    if output_dir.exists():
        raise FileExistsError("refusing to overwrite an existing annotation-return batch")
    evaluator_root = (ROOT / "data/evaluator_only").resolve()
    if output_dir == evaluator_root or evaluator_root in output_dir.parents:
        raise ValueError("batch output must not be under data/evaluator_only/")
    if not adjudicator_id.strip():
        raise ValueError("adjudicator_id must be non-empty")

    packets = selected_packets(packet_dir, only or [])
    names = {path.name for path in packets}
    if SEALED_LEGACY in names and not calibration_complete:
        raise ValueError(
            "sealed-primary-v3 requires --calibration-complete after independent calibration and discussion"
        )
    allow_extra_forms = bool(only)
    forms_a = require_forms(
        packets, annotator_a_dir, "annotator A", allow_extra=allow_extra_forms
    )
    forms_b = require_forms(
        packets, annotator_b_dir, "annotator B", allow_extra=allow_extra_forms
    )
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{output_dir.name}.", dir=output_dir.parent
    ) as temporary:
        staging = Path(temporary) / "batch"
        reports_dir = staging / "agreement"
        handoffs_dir = staging / "adjudication-handoffs"
        reports_dir.mkdir(parents=True)
        handoffs_dir.mkdir()
        packet_summaries: list[dict[str, Any]] = []

        for packet in packets:
            name = packet.name
            form_a = forms_a[name]
            form_b = forms_b[name]
            packet_ids = jsonl_inventory(packet)
            if jsonl_inventory(form_a) != packet_ids:
                raise ValueError(f"{name}: annotator A response inventory differs from packet")
            if jsonl_inventory(form_b) != packet_ids:
                raise ValueError(f"{name}: annotator B response inventory differs from packet")
            rubric_name = rubric(packet)
            report_path = reports_dir / f"{packet.stem}.json"
            report = run_validator(
                rubric_name=rubric_name,
                packet=packet,
                form_a=form_a,
                form_b=form_b,
                output=report_path,
            )
            disagreements = report.get("disagreements", [])
            handoff_path: str | None = None
            is_calibration = name == LEGACY_CALIBRATION
            if disagreements and not is_calibration:
                sys.path.insert(0, str(ROOT / "analysis"))
                from build_adjudication_handoff import build_handoff

                handoff = handoffs_dir / packet.stem
                build_handoff(
                    rubric=rubric_name,
                    packet_path=packet.resolve(),
                    agreement_path=report_path.resolve(),
                    output_dir=handoff.resolve(),
                    adjudicator_id=adjudicator_id,
                )
                handoff_path = f"adjudication-handoffs/{packet.stem}"
            packet_summaries.append(
                {
                    "packet": str(packet),
                    "packet_sha256": digest(packet),
                    "rubric": rubric_name,
                    "role": "development_calibration" if is_calibration else "study",
                    "responses": len(packet_ids),
                    "annotator_a_form_sha256": digest(form_a),
                    "annotator_b_form_sha256": digest(form_b),
                    "agreement_status": report["status"],
                    "disagreements": len(disagreements),
                    "report": f"agreement/{packet.stem}.json",
                    "adjudication_handoff": handoff_path,
                }
            )

        awaiting = sum(
            item["role"] == "study" and item["disagreements"] > 0
            for item in packet_summaries
        )
        calibration_disagreements = sum(
            item["disagreements"]
            for item in packet_summaries
            if item["role"] == "development_calibration"
        )
        if awaiting:
            status = "AWAITING_ADJUDICATION"
        elif calibration_disagreements and not calibration_complete:
            status = "AWAITING_CALIBRATION_DISCUSSION"
        elif calibration_disagreements:
            status = "VALIDATED_NO_STUDY_DISAGREEMENTS"
        else:
            status = "COMPLETE_AGREEMENT"
        manifest = {
            "schema": "crane-annotation-return-batch/v1",
            "status": status,
            "packets": packet_summaries,
            "packet_count": len(packet_summaries),
            "response_count": sum(item["responses"] for item in packet_summaries),
            "packets_awaiting_adjudication": awaiting,
            "calibration_disagreements": calibration_disagreements,
            "calibration_completion_attested": calibration_complete,
            "condition_key_joined": False,
            "evaluator_keys_read": False,
            "judgments_synthesized": False,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(staging, output_dir)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-dir", required=True, type=Path)
    parser.add_argument("--annotator-a-dir", required=True, type=Path)
    parser.add_argument("--annotator-b-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--adjudicator-id", required=True)
    parser.add_argument("--calibration-complete", action="store_true")
    parser.add_argument("--only", action="append", default=[])
    args = parser.parse_args()
    try:
        manifest = process_returns(
            packet_dir=args.packet_dir.resolve(strict=True),
            annotator_a_dir=args.annotator_a_dir.resolve(strict=True),
            annotator_b_dir=args.annotator_b_dir.resolve(strict=True),
            output_dir=args.output_dir.resolve(),
            adjudicator_id=args.adjudicator_id,
            calibration_complete=args.calibration_complete,
            only=args.only,
        )
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
