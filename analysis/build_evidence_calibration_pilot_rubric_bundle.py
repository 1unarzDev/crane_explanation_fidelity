#!/usr/bin/env python3
"""Materialize unreviewed method-blind pilot rubrics from independent references."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from build_evidence_calibration_pilot_rubric import build as build_rubric
from evidence_calibration_io import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]
SALT = ROOT / "data/evaluator_only/annotation_keys/evidence-calibration-b2-b4-pilot-v1/atomization-salt.txt"
DEFAULT_ROOT = ROOT / "data/evaluator_only/analysis/evidence-calibration-b2-b4-pilot-v1/rubrics-v1"
DEFAULT_MANIFEST = ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-rubric-candidates-v1.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(root: Path = ROOT) -> tuple[list[tuple[str, dict, dict]], dict]:
    salt = (root / SALT.relative_to(ROOT)).read_text(encoding="utf-8").strip()
    outputs = sorted((root / "model_outputs/evidence-calibration-b2-b4-pilot-v1/b2").glob("*.json"))
    if len(outputs) != 57:
        raise ValueError("rubric bundle requires exactly 57 retained valid B2 outputs")
    rows = []
    families = Counter()
    for output in outputs:
        cid = output.stem
        rubric, provenance = build_rubric(cid, salt, root)
        rows.append((cid, rubric, provenance))
        families[provenance["family"]] += 1
        if provenance["method_output_read"] is not False:
            raise ValueError("rubric builder inspected a method answer")
        if not rubric["required_unit_prompts"] or not rubric["limitation_prompts"]:
            raise ValueError(f"empty rubric content: {cid}")
    records = []
    for cid, rubric, provenance in rows:
        records.append({
            "condition_id": cid,
            "rubric_path": str((DEFAULT_ROOT / f"{cid}-rubric.json").relative_to(ROOT)),
            "rubric_raw_sha256": sha256(canonical_json_bytes(rubric) + b"\n"),
            "provenance_path": str((DEFAULT_ROOT / f"{cid}-provenance.json").relative_to(ROOT)),
            "provenance_raw_sha256": sha256(canonical_json_bytes(provenance) + b"\n"),
            "family": provenance["family"],
        })
    manifest = {
        "schema": "crane-evidence-calibration-pilot-rubric-candidates/v1",
        "pilot_id": "evidence-calibration-b2-b4-pilot-v1",
        "status": "CANDIDATE_UNREVIEWED_DO_NOT_ANNOTATE",
        "development_only": True,
        "rubric_count": len(rows),
        "family_condition_counts": dict(sorted(families.items())),
        "method_answer_text_read": False,
        "review_required_before_annotation": True,
        "records": records,
    }
    return rows, manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    rows, manifest = build()
    args.output_root.mkdir(parents=True, exist_ok=True)
    for cid, rubric, provenance in rows:
        (args.output_root / f"{cid}-rubric.json").write_bytes(canonical_json_bytes(rubric) + b"\n")
        (args.output_root / f"{cid}-provenance.json").write_bytes(canonical_json_bytes(provenance) + b"\n")
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_bytes(canonical_json_bytes(manifest) + b"\n")
    print(json.dumps({"status": manifest["status"], "rubrics": len(rows),
                      "family_condition_counts": manifest["family_condition_counts"]}, indent=2))


if __name__ == "__main__":
    main()
