from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_atomization import uncovered_text  # noqa: E402


def test_uncovered_text_flags_substantive_omission_for_review() -> None:
    response = "The action aborted. The left motor burned out and caused the stop."
    claims = [{"response_span": "The action aborted."}]
    assert uncovered_text(response, claims) == ["The left motor burned out and caused the stop"]


def test_uncovered_text_is_only_a_triage_signal() -> None:
    response = "The action aborted, but its physical cause remains unknown."
    claims = [
        {"response_span": "The action aborted"},
        {"response_span": "its physical cause remains unknown"},
    ]
    assert uncovered_text(response, claims) == []
