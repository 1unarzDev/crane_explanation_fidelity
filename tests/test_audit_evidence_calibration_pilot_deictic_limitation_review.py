import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_deictic_limitation_review import REVIEW, audit  # noqa: E402


def test_deictic_review_preserves_missing_referent_and_closed_gate():
    result = audit()
    assert result["affected_responses"] == 12
    assert result["newly_reviewed_responses"] == 10
    assert result["reviewed_responses_total"] == 71
    assert result["support_label_assigned"] is False


def test_review_cannot_invent_a_named_physical_cause(tmp_path):
    review = json.loads(REVIEW.read_text())
    review["rows"][0]["reviewed_replacement_claim_text"] = "The discrepancy excludes wheel slip."
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="differs from retained blind answer"):
        audit(path)


def test_review_cannot_assign_support_label(tmp_path):
    review = json.loads(REVIEW.read_text())
    review["support_label_assigned"] = True
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="governance boundary"):
        audit(path)
