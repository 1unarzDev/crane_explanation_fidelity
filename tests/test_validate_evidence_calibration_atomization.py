from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from validate_evidence_calibration_atomization import validate  # noqa: E402


def inputs():
    entry = {"opaque_response_id": "ax-opaque", "response_text": "The action aborted. The cause remains unknown."}
    value = {
        "schema": "crane-evidence-calibration-atomization-return/v1",
        "opaque_response_id": "ax-opaque",
        "claims": [
            {"response_span": "The action aborted.", "claim_text": "The action aborted.", "asserted_abstraction_level": "task_outcome"},
            {"response_span": "The cause remains unknown.", "claim_text": "The physical cause remains unknown.", "asserted_abstraction_level": "specific_physical_cause"},
        ],
        "unresolved_spans": [],
        "attestation": "METHOD_BLIND_EXHAUSTIVE_EXTRACTION_ATTEMPT",
    }
    return entry, value


def test_structural_validation_does_not_claim_semantic_completeness() -> None:
    result = validate(*inputs())
    assert result["claim_count"] == 2
    assert result["semantic_completeness_established"] is False
    assert result["support_annotation_authorized"] is False


def test_invalid_span_and_duplicate_claim_fail_closed() -> None:
    entry, value = inputs()
    value["claims"][0]["response_span"] = "The motor failed."
    with pytest.raises(ValueError, match="invalid span"):
        validate(entry, value)
    _, value = inputs()
    value["claims"].append(dict(value["claims"][0]))
    with pytest.raises(ValueError, match="duplicate"):
        validate(entry, value)


def test_unresolved_assertion_blocks_packet_readiness() -> None:
    entry, value = inputs()
    value["unresolved_spans"] = ["The cause remains unknown."]
    assert validate(entry, value)["status"] == "REVIEW_REQUIRED_UNRESOLVED_ASSERTION"
