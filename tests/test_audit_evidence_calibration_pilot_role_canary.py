from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_role_canary import MANIFEST, audit  # noqa: E402


def test_non_study_canary_is_bound_before_pilot_calls() -> None:
    result = audit()
    assert result["pilot_role_calls_admissible"] is True
    assert result["study_calls_attempted"] == 0
    assert result["endpoint_scoring_authorized"] is False


def test_canary_audit_rejects_changed_call_hash(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["call_record"]["raw_sha256"] = "0" * 64
    changed = tmp_path / "changed-canary.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="canary binding"):
        audit(changed)
