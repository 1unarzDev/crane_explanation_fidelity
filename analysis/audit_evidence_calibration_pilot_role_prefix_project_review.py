#!/usr/bin/env python3
"""Verify blind development review bindings; never infer semantic correctness."""

from __future__ import annotations

import json
from pathlib import Path

from audit_evidence_calibration_pilot_role_returns import ROOT, VALID_STATUS, audit, digest
from audit_evidence_calibration_pilot_role_prefix_variance import find_variance


MANIFEST = ROOT / "manifests/annotation/evidence-calibration-pilot-role-prefix-project-review-v1.json"


def audit_review(path: Path = MANIFEST) -> dict:
    review = json.loads(path.read_text())
    if (review.get("schema") != "crane-evidence-calibration-pilot-role-prefix-project-review/v1-development"
            or review.get("status") != "BLIND_DEVELOPMENT_REVIEW_WITH_OPEN_MEASUREMENT_GATES"
            or review.get("review_type") != "AGENT_ASSISTED_PROJECT_REVIEW_NOT_SUPPORT_ANNOTATION"
            or any(review.get(key) is not False for key in (
                "method_key_opened", "evaluator_truth_opened", "visible_evidence_opened",
                "support_labels_generated", "endpoint_scores_generated", "returned_labels_changed",
                "synthetic_qualification_regraded", "both_pass_review_complete",
                "support_handoff_authorized", "p11_authorized"))
            or review.get("confirmation_independent_n") != 0
            or review.get("replication_independent_n") != 0):
        raise ValueError("review scope or authorization boundary changed")
    for binding in review["bindings"].values():
        if digest(ROOT / binding["path"]) != binding["raw_sha256"]:
            raise ValueError(f"review binding changed: {binding['path']}")
    snapshot = json.loads((ROOT / review["bindings"]["snapshot"]["path"]).read_text())
    if audit() != snapshot:
        raise ValueError("reviewed interrupted records changed")
    if find_variance() != json.loads((ROOT / review["bindings"]["variance"]["path"]).read_text()):
        raise ValueError("reviewed exact-input variance changed")
    bundle = json.loads((ROOT / review["bindings"]["input_bundle"]["path"]).read_text())
    entries = {entry["case_id"]: entry for entry in bundle["entries"]}
    expected = []
    atoms = {}
    for row in snapshot["records"]:
        if row["disposition"] != VALID_STATUS:
            continue
        entry = entries[row["case_id"]]
        expected.append({"case_id": row["case_id"], "slot": row["slot"],
                         "atomic_judgment_count": len(entry["claims"]),
                         "terminal_record": row["terminal_record"],
                         "project_review": "REVIEWED_WITH_CONCERNS_NO_RELABELING"})
        record = json.loads((ROOT / row["terminal_record"]["path"]).read_text())
        for claim, role in zip(entry["claims"], record["parsed_final"]["claim_roles"], strict=True):
            atoms[(row["case_id"], claim["item_id"])] = {
                "case_id": row["case_id"], "claim": claim, "returned_role": role}
    if (review["reviewed_records"] != expected or review["reviewed_response_count"] != len(expected)
            or len(expected) != 69 or review["reviewed_atomic_judgment_count"] != len(atoms)
            or len(atoms) != 669):
        raise ValueError("review scope differs from retained prefix")
    examples = review["representative_findings"]
    keys = [(item["case_id"], item["claim"]["item_id"]) for item in examples]
    if len(keys) != 9 or len(set(keys)) != 9 or any(atoms.get(key) != item for key, item in zip(keys, examples)):
        raise ValueError("review examples differ from exact claims and returns")
    return {"status": "PASS_REVIEW_BINDINGS_ONLY", "reviewed_responses": len(expected),
            "reviewed_atoms": len(atoms), "support_handoff_authorized": False,
            "endpoint_scoring_authorized": False, "p11_authorized": False}


if __name__ == "__main__":
    print(json.dumps(audit_review(), indent=2, sort_keys=True))
