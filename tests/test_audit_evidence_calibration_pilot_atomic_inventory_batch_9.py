import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_atomic_inventory_batch_9 import REVIEW, audit  # noqa: E402


def test_exact_batch_and_scoring_boundary():
    result = audit()
    assert result["reviewed_responses_total"] == 61
    assert result["remaining_unreviewed_forms"] == 52
    assert result["batch_final_atomic_claims"] == 78
    assert result["support_annotation_authorized"] is False


def test_source_qualifier_duplicate_cannot_be_reaccepted(tmp_path):
    review = json.loads(REVIEW.read_text())
    row = next(item for item in review["rows"]
               if item["opaque_response_id"] == "ax-cc3206f1fc25ba97d96b9c8d13968a71")
    row["rejected_candidate_indices"] = []
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="atomic disposition"):
        audit(path)


def test_batch_cannot_authorize_annotation(tmp_path):
    review = json.loads(REVIEW.read_text())
    review["support_annotation_authorized"] = True
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="governance boundary"):
        audit(path)
