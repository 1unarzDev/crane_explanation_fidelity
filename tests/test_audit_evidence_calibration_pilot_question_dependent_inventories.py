from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_question_dependent_inventories import REVIEW, audit  # noqa: E402


def test_one_word_claims_are_bound_without_scoring() -> None:
    result = audit()
    assert result["reviewed_structural_forms_total"] == 113
    assert result["question_dependent_scope_still_requires_role_review"] == 3
    assert result["unknown_disposition_requests"] == 1
    assert result["support_annotation_authorized"] is False


def test_one_word_claim_cannot_be_silently_reinterpreted(tmp_path: Path) -> None:
    document = json.loads(REVIEW.read_text(encoding="utf-8"))
    document["rows"][0]["appended_atomic_claims"][0]["claim_text"] = "The goal failed."
    changed = tmp_path / "changed-review.json"
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="question-dependent inventory changed"):
        audit(changed)
