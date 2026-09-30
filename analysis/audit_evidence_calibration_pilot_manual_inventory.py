#!/usr/bin/env python3
"""Audit a project-authored inventory for the non-retriable extraction request."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from audit_evidence_calibration_pilot_question_dependent_inventories import audit as audit_structural
from run_evidence_calibration_pilot_atomization import ROOT


REVIEW = ROOT / "manifests/annotation/evidence-calibration-pilot-manual-inventory-v1.json"
BANK = ROOT / "model_outputs/annotation_packets/evidence-calibration-b2-b4-pilot-v1/atomization-bank.json"
INTERRUPTION = ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-atomization-v2-interruption-v1.json"
RESPONSE_ID = "ax-6042b1c29021e662d8184d39e26738c5"

# These meanings were read directly from the unchanged blinded answer. In particular,
# the phrase about the retained tree is preserved literally for later support review.
ATOMS = [
    ("The strongest supported diagnosis is a **temporary command–motion discrepancy during navigation**",
     "The strongest supported diagnosis is a temporary command–motion discrepancy during navigation."),
    ("not a failed navigation episode", "The episode was not a failed navigation episode."),
    ("Delivered Nav2 commands remained at 0.26 m/s", "Nav2 delivered commands at 0.26 m/s during the 9–19 s interval."),
    ("measured odometry was 0 m/s for 10 seconds (9–19 s)",
     "Measured odometry was 0 m/s for 10 seconds during 9–19 s."),
    ("after an initial measured response of about 0.26 m/s",
     "An initial measured response of about 0.26 m/s preceded the 9–19 s discrepancy."),
    ("Measured motion returned to about 0.25 m/s at 21–22 s",
     "Measured motion returned to about 0.25 m/s at 21–22 s."),
    ("`FollowPath` failed twice", "FollowPath failed twice."),
    ("the retained behavior tree records two `Wait` recoveries",
     "The retained behavior tree records two Wait recoveries."),
    ("two `Wait` recoveries before the NavigateToPose action **succeeded**",
     "Two Wait recoveries preceded NavigateToPose success."),
    ("the NavigateToPose action **succeeded**", "The NavigateToPose action succeeded."),
    ("motion stopped", "Measured motion stopped during the described interval."),
    ("The evidence does not establish why motion stopped",
     "The evidence does not establish why measured motion stopped."),
    ("whether the actuator accepted the commands",
     "The evidence does not establish whether the actuator accepted the commands."),
    ("whether Nav2 consumed the delivered odometry",
     "The evidence does not establish whether Nav2 consumed the delivered odometry."),
    ("whether waiting caused motion to resume",
     "The evidence does not establish whether waiting caused motion to resume."),
]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path: Path = REVIEW) -> dict:
    audit_structural()
    document = json.loads(path.read_text(encoding="utf-8"))
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    interrupted = json.loads(INTERRUPTION.read_text(encoding="utf-8"))
    if (
        document.get("schema") != "crane-evidence-calibration-pilot-manual-inventory/v1-development"
        or document.get("status") != "PROJECT_AUTHORED_AFTER_UNKNOWN_EXTRACTION_DISPOSITION"
        or document.get("blind_bank_raw_sha256") != digest(BANK)
        or document.get("interruption_raw_sha256") != digest(INTERRUPTION)
        or document.get("opaque_response_id") != RESPONSE_ID
        or interrupted["ambiguous_request"]["opaque_response_id"] != RESPONSE_ID
        or interrupted["ambiguous_request"]["retry_prohibited"] is not True
        or interrupted["ambiguous_request"]["call_record_present"] is not False
        or document.get("extractor_status") != "UNKNOWN_NOT_RETRIED"
        or document.get("method_identity_opened") is not False
        or document.get("evaluator_truth_opened") is not False
        or any(document.get(key) is not False for key in
               ("qualified_extractor_return", "support_annotation_authorized",
                "endpoint_scoring_authorized", "p11_authorized"))
        or document.get("confirmation_independent_n") != 0
        or document.get("replication_independent_n") != 0
    ):
        raise ValueError("manual inventory governance boundary changed")
    answer_rows = [row for row in bank["entries"] if row["opaque_response_id"] == RESPONSE_ID]
    if len(answer_rows) != 1:
        raise ValueError("blinded answer identity changed")
    answer = answer_rows[0]["response_text"]
    if document["response_text_sha256"] != hashlib.sha256(answer.encode("utf-8")).hexdigest():
        raise ValueError("blinded answer text changed")
    atoms = document["atomic_claims"]
    if atoms != [{"response_span": span, "claim_text": claim} for span, claim in ATOMS]:
        raise ValueError("manual atomic meanings changed")
    if any(span not in answer for span, _ in ATOMS):
        raise ValueError("manual atomic span absent from answer")
    return {
        "schema": "crane-evidence-calibration-pilot-manual-inventory-audit/v1",
        "status": "PASS_MANUAL_INVENTORY_WITH_RETAINED_UNKNOWN_REQUEST",
        "blind_answer_count": 114,
        "project_reviewed_structural_forms": 113,
        "manual_answer_inventory_count": 1,
        "manual_atomic_claim_count": len(ATOMS),
        "qualified_extractor_return": False,
        "support_annotation_authorized": False,
        "endpoint_scoring_authorized": False,
        "p11_authorized": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
