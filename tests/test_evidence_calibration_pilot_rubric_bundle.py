from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_pilot_rubric_bundle import build  # noqa: E402


def test_candidate_rubrics_cover_valid_conditions_without_answer_text() -> None:
    rows, manifest = build()
    assert len(rows) == manifest["rubric_count"] == 57
    assert manifest["status"] == "CANDIDATE_UNREVIEWED_DO_NOT_ANNOTATE"
    assert manifest["method_answer_text_read"] is False
    assert all(provenance["method_output_read"] is False for _, _, provenance in rows)
    assert all(rubric["required_unit_prompts"] and rubric["limitation_prompts"] for _, rubric, _ in rows)
