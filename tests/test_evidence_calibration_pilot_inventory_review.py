from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_pilot_inventory_review import build  # noqa: E402


def test_review_forms_are_blind_pending_and_exclude_unqualified_levels(tmp_path: Path) -> None:
    result = build(tmp_path)
    assert result["forms"] == 113
    assert result["method_key_opened"] is False
    forms = sorted(tmp_path.glob("*.json"))
    assert len(forms) == 113
    for path in forms:
        form = json.loads(path.read_text(encoding="utf-8"))
        assert form["status"] == "PROJECT_REVIEW_PENDING"
        assert form["method_identity_visible"] is False
        assert form["extractor_abstraction_tags_used"] is False
        assert "method_id" not in form
        assert all("method_id" not in candidate for candidate in form["atomic_claim_candidates"])
        assert "asserted_abstraction_level" not in str(form)
        assert form["review_fields"]["inventory_complete_after_review"] is None
