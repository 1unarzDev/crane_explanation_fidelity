import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_inventory_prefix_project_review import REVIEW, audit  # noqa: E402


def test_blind_project_review_binds_all_17_forms_and_keeps_scoring_closed():
    result = audit()
    assert result["reviewed_responses"] == 17
    assert result["reviewed_candidate_claims"] == 160
    assert result["approved_actor_repairs"] == 3
    assert result["support_annotation_authorized"] is False
    assert result["endpoint_scoring_authorized"] is False


def test_claim_replacement_cannot_change_silently(tmp_path):
    review = json.loads(REVIEW.read_text())
    row = next(row for row in review["rows"] if row["approved_claim_text_replacements"])
    key = next(iter(row["approved_claim_text_replacements"]))
    row["approved_claim_text_replacements"][key] = "The trace records unspecified failures."
    changed = tmp_path / "changed-review.json"
    changed.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="actor repairs changed"):
        audit(changed)


def test_review_cannot_authorize_support_annotation(tmp_path):
    review = json.loads(REVIEW.read_text())
    review["support_annotation_authorized"] = True
    changed = tmp_path / "changed-review.json"
    changed.write_text(json.dumps(review))
    with pytest.raises(ValueError, match="governance boundary"):
        audit(changed)
