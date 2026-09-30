from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_full_bank_actor_triage import MANIFEST, audit  # noqa: E402


def test_full_bank_actor_proposals_remain_blind_and_pending() -> None:
    result = audit()
    assert result["status"] == "PASS_BOUND_PROPOSALS_ONLY"
    assert result["blind_responses"] == 7
    assert result["proposed_claim_repairs"] == 8
    assert result["support_annotation_authorized"] is False


def test_actor_proposal_rejects_changed_bound_form(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["findings"][0]["review_form_raw_sha256"] = "0" * 64
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="blind review form changed"):
        audit(path)
