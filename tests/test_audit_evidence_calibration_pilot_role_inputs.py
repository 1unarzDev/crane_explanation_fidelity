from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_role_inputs import OUTPUT, audit  # noqa: E402


def test_role_inputs_cover_every_blind_answer_without_a_model_call() -> None:
    result = audit()
    assert result["response_count"] == 114
    assert result["atomic_claim_count"] == 1084
    assert result["manual_inventory_responses"] == 1
    assert result["pilot_role_annotation_authorized"] is False
    bundle = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert all(set(entry) == {"case_id", "response_text", "claims"} for entry in bundle["entries"])


def test_role_input_audit_rejects_missing_atom(tmp_path: Path) -> None:
    bundle = json.loads(OUTPUT.read_text(encoding="utf-8"))
    bundle["entries"][0]["claims"].pop()
    changed = tmp_path / "changed-role-inputs.json"
    changed.write_text(json.dumps(bundle), encoding="utf-8")
    with pytest.raises(ValueError, match="role input bundle"):
        audit(bundle_path=changed)
