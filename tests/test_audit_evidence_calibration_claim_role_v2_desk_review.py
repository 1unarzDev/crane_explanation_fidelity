from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_v2_desk_review import MANIFEST, audit  # noqa: E402


def test_v2_desk_review_is_bound_but_cannot_authorize_a_freeze() -> None:
    result = audit()
    assert result["status"] == "PASS_PROVISIONAL_SECOND_REVIEW_PENDING"
    assert (result["cases"], result["atoms"]) == (24, 39)
    assert result["qualification_freeze_authorized"] is False


def test_v2_desk_review_rejects_premature_authorization(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["qualification_freeze_authorized"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="authorization boundary changed"):
        audit(path)
