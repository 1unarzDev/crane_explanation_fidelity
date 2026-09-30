from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import run_evidence_calibration_pilot_claim_roles as pilot_roles  # noqa: E402


def test_pilot_role_declaration_binds_qualified_task_without_endpoint() -> None:
    declaration, entries, freeze, _, _ = pilot_roles.load_declared()
    assert len(entries) == 114
    assert sum(len(entry["claims"]) for entry in entries) == 1084
    assert declaration["model"] == freeze["candidate"]["model"]
    assert declaration["endpoint_scoring_authorized"] is False
    assert declaration["quality_driven_retries"] == 0


def test_pilot_role_declaration_rejects_changed_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    declaration = json.loads(pilot_roles.DECLARATION.read_text(encoding="utf-8"))
    declaration["input_bundle"]["raw_sha256"] = "0" * 64
    changed = tmp_path / "changed-declaration.json"
    changed.write_text(json.dumps(declaration), encoding="utf-8")
    monkeypatch.setattr(pilot_roles, "DECLARATION", changed)
    with pytest.raises(ValueError, match="declaration differs"):
        pilot_roles.load_declared()
