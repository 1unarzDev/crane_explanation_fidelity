import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
SPEC = importlib.util.spec_from_file_location(
    "export_roboboat_prospective_evidence",
    ROOT / "analysis/export_roboboat_prospective_evidence.py",
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
bind = MODULE.bind


def test_bind_changes_only_prospective_transport_metadata(tmp_path: Path) -> None:
    summary = tmp_path / "fixture-summary.json"
    summary.write_text('{"example": true}\n', encoding="utf-8")
    payload = {
        "schema": "crane-terminal-margin-development-export-v1",
        "study_status": "DEVELOPMENT_ONLY_NOT_CONFIRMATORY",
        "episode_id": "boat-ext-narrow-001",
        "source": {"fixture_summary_sha256": hashlib.sha256(summary.read_bytes()).hexdigest()},
        "observation": {"action_status": "succeeded"},
        "evidence_boundary": {"excluded": ["independent docking success label"]},
    }
    result = bind(payload, "boat-ext-narrow-001", summary)
    assert result["schema"] == "crane-roboboat-prospective-robot-visible-evidence/v1"
    assert result["study_status"] == "PROSPECTIVE_EXTERNAL_VALIDITY_ARM"
    assert result["observation"] is payload["observation"]
    assert result["land_n_added"] == 0
    assert result["land_alpha_consumed"] == 0.0


def test_bind_rejects_unknown_configuration(tmp_path: Path) -> None:
    summary = tmp_path / "fixture-summary.json"
    summary.write_text("{}\n", encoding="utf-8")
    payload = {"source": {"fixture_summary_sha256": hashlib.sha256(summary.read_bytes()).hexdigest()}}
    with pytest.raises(ValueError, match="not in the frozen"):
        bind(payload, "boat-ext-narrow-999", summary)
