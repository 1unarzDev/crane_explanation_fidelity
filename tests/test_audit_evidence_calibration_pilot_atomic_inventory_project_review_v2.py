import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_atomic_inventory_project_review_v2 import REVIEW, audit  # noqa: E402


def test_review_reconciles_originals_splits_and_closed_gate():
    result = audit()
    assert result["reviewed_responses"] == 52
    assert result["composite_candidates_split"] == 11
    assert result["final_atomic_claims"] == 296
    assert result["remaining_unreviewed_forms"] == 61
    assert result["support_annotation_authorized"] is False


def test_composite_candidate_cannot_be_reaccepted(tmp_path):
    review = json.loads(REVIEW.read_text())
    row = next(row for row in review["rows"] if row["rejected_candidate_indices"])
    row["accepted_candidate_indices"] = [0] + row["accepted_candidate_indices"]
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="atomic split"):
        audit(path)


def test_review_cannot_open_endpoint_scoring(tmp_path):
    review = json.loads(REVIEW.read_text())
    review["endpoint_scoring_authorized"] = True
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="governance boundary"):
        audit(path)
