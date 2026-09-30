from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_v2_reference_adjudication import MANIFEST, audit  # noqa: E402


def test_reviewer_defects_and_uncalled_repair_are_hash_bound() -> None:
    result = audit()
    assert result["status"] == "PASS_BOUND_REPAIR_UNCALLED"
    assert (result["reviewed_cases"], result["flagged_cases"], result["global_issues"]) == (24, 8, 3)
    assert result["endpoint_scoring_authorized"] is False


def test_adjudication_cannot_claim_role_qualification(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["role_qualification_authorized"] = True
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="authorization boundary changed"):
        audit(path)
