from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import run_evidence_calibration_claim_role_v2_reference_review as review  # noqa: E402


def test_synthetic_review_request_is_hash_bound_and_study_closed() -> None:
    request, suite, _, schema, _ = review.load_request()
    assert request["model_calls_before_freeze"] == 0
    assert request["study_output_authorized"] is False
    assert len(suite["cases"]) == 24
    assert schema["properties"]["attestation"]["const"] == "SYNTHETIC_REFERENCE_REVIEW_ONLY_NO_STUDY_LABELS"


def test_review_return_requires_every_case_in_order() -> None:
    returned = {"schema": "crane-evidence-calibration-claim-role-v2-reference-review/v1",
                "case_reviews": [{"case_id": "one", "status": "ACCEPT", "issues": []}],
                "global_issues": [],
                "attestation": "SYNTHETIC_REFERENCE_REVIEW_ONLY_NO_STUDY_LABELS"}
    review.validate_return(returned, ["one"])
    with pytest.raises(ValueError, match="exactly in order"):
        review.validate_return(returned, ["one", "two"])


def test_interrupted_intent_is_never_retried(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(review, "OUTPUT", tmp_path)
    monkeypatch.setattr(review.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="codex-cli test"))
    (tmp_path / "canary.intent").write_text(json.dumps({"terminal_record_pending": True}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="do not retry"):
        review.call("canary")
