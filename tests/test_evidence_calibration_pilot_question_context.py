from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_pilot_question_context import OUTPUT, audit  # noqa: E402


def test_question_context_discloses_no_method_or_evaluator_key() -> None:
    result = audit()
    assert result["response_count"] == 3
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    assert document["evaluator_key_read"] is False
    assert document["method_identity_exposed_to_reviewer"] is False
    for row in document["rows"]:
        assert set(row) == {"opaque_response_id", "answer_sha256", "question_instruction"}


def test_question_context_rejects_unbound_question(tmp_path: Path) -> None:
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    document["rows"][0]["question_instruction"] = "Was the action successful?"
    changed = tmp_path / "changed-context.json"
    changed.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="question-only context differs"):
        audit(changed)
