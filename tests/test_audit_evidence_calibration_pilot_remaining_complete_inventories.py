from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_remaining_complete_inventories import REVIEW, audit  # noqa: E402


def test_remaining_complete_inventory_review_is_bound_and_unscored() -> None:
    result = audit()
    assert result["reviewed_responses_total"] == 110
    assert result["remaining_question_dependent_forms"] == 3
    assert result["remaining_unknown_disposition_requests"] == 1
    assert result["support_annotation_authorized"] is False
    assert result["endpoint_scoring_authorized"] is False


def test_review_rejects_candidate_omission(tmp_path: Path) -> None:
    review = json.loads(REVIEW.read_text(encoding="utf-8"))
    review["rows"][0]["accepted_candidate_indices"].pop()
    changed = tmp_path / "changed-review.json"
    changed.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(ValueError, match="review differs"):
        audit(changed)
