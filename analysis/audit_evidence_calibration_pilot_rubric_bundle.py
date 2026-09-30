#!/usr/bin/env python3
"""Recompute every candidate pilot rubric and verify its evaluator-only bytes."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from build_evidence_calibration_pilot_rubric_bundle import ROOT, build
from evidence_calibration_io import canonical_json_bytes


MANIFEST = ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-rubric-candidates-v1.json"
REVIEW = ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-rubric-review-v1.json"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(root: Path = ROOT) -> dict:
    manifest_path = root / MANIFEST.relative_to(ROOT)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows, expected = build(root)
    if manifest != expected:
        raise ValueError("candidate rubric manifest differs from method-blind reconstruction")
    templates = Counter()
    for cid, rubric, provenance in rows:
        for kind, value in (("rubric", rubric), ("provenance", provenance)):
            path = root / f"data/evaluator_only/analysis/evidence-calibration-b2-b4-pilot-v1/rubrics-v1/{cid}-{kind}.json"
            if path.read_bytes() != canonical_json_bytes(value) + b"\n":
                raise ValueError(f"evaluator-only {kind} changed: {cid}")
        templates[(tuple(rubric["required_unit_prompts"]), tuple(rubric["limitation_prompts"]),
                   rubric["false_premise_applicable"])] += 1
    if len(templates) != 10:
        raise ValueError("candidate rubric template inventory changed")
    review_path = root / REVIEW.relative_to(ROOT)
    review = json.loads(review_path.read_text(encoding="utf-8"))
    if (review["candidate_manifest_raw_sha256"] != sha256(manifest_path.read_bytes())
            or review["reviewed_condition_count"] != 57
            or review["reviewed_distinct_templates"] != len(templates)
            or review["method_answer_text_used"] is not False
            or review["support_annotation_authorized"] is not False):
        raise ValueError("method-blind rubric review binding changed")
    reviewed = {row["template_sha256"]: row for row in review["templates"]}
    if len(reviewed) != len(templates):
        raise ValueError("rubric review template count changed")
    for (units, limits, false_premise), count in templates.items():
        template = {"required_unit_prompts": units, "limitation_prompts": limits,
                    "false_premise_applicable": false_premise}
        template_hash = sha256(json.dumps(template, sort_keys=True, separators=(",", ":"),
                                          ensure_ascii=False).encode())
        if reviewed[template_hash]["condition_count"] != count:
            raise ValueError("rubric review template frequency changed")
    return {"schema": "crane-evidence-calibration-pilot-rubric-bundle-audit/v1",
            "status": "PASS_REVIEWED_SOURCE_CONTEXT_CANARY_PENDING", "rubrics": len(rows),
            "distinct_templates": len(templates), "candidate_manifest_raw_sha256": sha256(manifest_path.read_bytes()),
            "method_answers_used_for_rubric_content": False}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
