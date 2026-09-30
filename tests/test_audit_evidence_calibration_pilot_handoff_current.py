from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_handoff import audit  # noqa: E402


def test_handoff_reports_current_partial_measurement_without_promoting_a_result() -> None:
    result = audit()
    assert result["errors"] == []
    assert result["valid_b2_outputs"] == 57
    assert result["accepted_deterministic_b4_outputs"] == 60
    assert result["structural_atomization_returns"] == 113
    assert result["retained_ambiguous_atomization_requests"] == 1
    assert result["reviewed_method_blind_rubrics"] == 57
    assert result["common_source_context_conditions"] == 57
    assert result["blinded_atomic_packet_files"] == 0
    assert result["confirmatory_independent_n"] == 0
