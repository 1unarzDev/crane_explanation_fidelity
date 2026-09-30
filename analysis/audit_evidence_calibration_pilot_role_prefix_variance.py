#!/usr/bin/env python3
"""Find role variance for exact repeated blind inputs in the retained 69-return prefix."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_role_returns import ROOT, VALID_STATUS, audit


SNAPSHOT = "manifests/study/evidence-calibration-pilot-role-v2r2-interruption-v1.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_variance() -> dict:
    snapshot = json.loads((ROOT / SNAPSHOT).read_text())
    if audit() != snapshot:
        raise ValueError("retained prefix no longer matches its interruption snapshot")
    declaration = json.loads((ROOT / snapshot["declaration"]["path"]).read_text())
    bundle_path = ROOT / declaration["input_bundle"]["path"]
    bundle = json.loads(bundle_path.read_text())
    entries = {entry["case_id"]: entry for entry in bundle["entries"]}
    groups = defaultdict(list)
    responses = atoms = 0
    for row in snapshot["records"]:
        if row["disposition"] != VALID_STATUS:
            continue
        entry = entries[row["case_id"]]
        record = json.loads((ROOT / row["terminal_record"]["path"]).read_text())
        responses += 1
        for claim, role in zip(entry["claims"], record["parsed_final"]["claim_roles"], strict=True):
            atoms += 1
            key = (entry["response_text"], claim["claim_text"], claim["response_span"])
            groups[key].append({
                "case_id": row["case_id"], "item_id": claim["item_id"],
                "stance": role["stance"], "claim_kind": role["claim_kind"], "polarity": role["polarity"],
            })
    differing = []
    for (answer, claim, span), judgments in groups.items():
        if len({(j["stance"], j["claim_kind"], j["polarity"]) for j in judgments}) > 1:
            differing.append({
                "answer_raw_sha256": hashlib.sha256(answer.encode()).hexdigest(),
                "claim_text": claim, "response_span": span, "judgments": judgments,
            })
    return {
        "schema": "crane-evidence-calibration-pilot-role-prefix-variance/v1-development",
        "recorded_date": "2026-09-30", "status": "MECHANICAL_VARIANCE_TRIAGE_NOT_SEMANTIC_SCORING",
        "snapshot": {"path": SNAPSHOT, "raw_sha256": digest(ROOT / SNAPSHOT)},
        "input_bundle": {"path": str(bundle_path.relative_to(ROOT)), "raw_sha256": digest(bundle_path)},
        "auditor": {"path": "analysis/audit_evidence_calibration_pilot_role_prefix_variance.py",
                    "raw_sha256": digest(Path(__file__))},
        "response_count": responses, "atomic_judgment_count": atoms,
        "grouping": "exact complete answer text, normalized claim text, and exact response span; opaque IDs excluded",
        "varying_exact_input_group_count": len(differing), "varying_groups": differing,
        "support_labels_generated": False, "endpoint_scores_generated": False,
        "semantic_review_complete": False, "synthetic_qualification_regraded": False,
        "confirmation_independent_n": 0, "replication_independent_n": 0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    result = find_variance()
    if args.manifest and json.loads(args.manifest.read_text()) != result:
        raise ValueError("prefix variance differs from its bound manifest")
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "varying_groups"}, indent=2))
