from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_outcome import DEFAULT_OUTCOME, verify  # noqa: E402


def test_failed_role_qualification_is_hash_bound_and_closed() -> None:
    result = verify()
    assert result["status"] == "PASS_BOUND_FAILED_QUALIFICATION"
    assert result["retained_calls"] == 49
    assert result["heldout_exact_matches"] == {"A": 12, "B": 14}
    assert result["endpoint_scoring_authorized"] is False


def test_failed_outcome_cannot_be_relabelled_as_qualified(tmp_path: Path) -> None:
    outcome = json.loads(DEFAULT_OUTCOME.read_text(encoding="utf-8"))
    outcome["role_qualification_authorized"] = True
    path = tmp_path / "tampered.json"
    path.write_text(json.dumps(outcome), encoding="utf-8")
    with pytest.raises(ValueError, match="governance boundary changed"):
        verify(path)
