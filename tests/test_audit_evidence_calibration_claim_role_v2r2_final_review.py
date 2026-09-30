from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_v2r2_final_review import MANIFEST, audit  # noqa: E402


def test_v2r2_review_permits_only_a_separate_task_freeze() -> None:
    result = audit()
    assert result["status"] == "PASS_FOR_MEASUREMENT_TASK_FREEZE_ONLY"
    assert (result["cases"], result["atoms"]) == (24, 39)
    assert result["role_qualification_authorized"] is False
    assert result["endpoint_scoring_authorized"] is False


def test_v2r2_review_rejects_premature_qualification(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["role_qualification_authorized"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="authorization boundary changed"):
        audit(path)
