from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from run_evidence_calibration_pilot_atomization import load_declared_inputs  # noqa: E402


def test_pilot_extraction_is_bound_to_blind_bank_and_inventory_only() -> None:
    declaration, entries, _, freeze, _, _ = load_declared_inputs()
    assert len(entries) == 114
    assert all(set(entry) == {"opaque_response_id", "response_text"} for entry in entries)
    assert declaration["support_annotation_authorized"] is False
    assert declaration["unqualified_output_fields"] == ["asserted_abstraction_level"]
    assert "evaluator_only" not in str(declaration)
    assert freeze["candidate"]["quality_driven_retries"] == 0
