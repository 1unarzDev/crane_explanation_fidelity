from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_manual_inventory import REVIEW, audit  # noqa: E402


def test_manual_inventory_preserves_unknown_extractor_status() -> None:
    result = audit()
    assert result["blind_answer_count"] == 114
    assert result["manual_atomic_claim_count"] == 15
    assert result["qualified_extractor_return"] is False
    assert result["support_annotation_authorized"] is False


def test_manual_inventory_rejects_rewritten_claim(tmp_path: Path) -> None:
    document = json.loads(REVIEW.read_text(encoding="utf-8"))
    document["atomic_claims"][0]["claim_text"] = "A motor failed."
    changed = tmp_path / "changed-inventory.json"
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="manual atomic meanings changed"):
        audit(changed)
