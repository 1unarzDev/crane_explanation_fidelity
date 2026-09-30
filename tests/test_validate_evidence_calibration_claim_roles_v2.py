from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, RETURN_SCHEMA, validate  # noqa: E402


def example() -> tuple[dict, dict]:
    payload = {
        "schema": INPUT_SCHEMA,
        "opaque_response_id": "synthetic-01",
        "response_text": "The trace records a Wait completion; motor failure is not established.",
        "claims": [
            {"item_id": "c1", "response_span": "The trace records a Wait completion",
             "claim_text": "The trace records a completed Wait recovery action."},
            {"item_id": "c2", "response_span": "motor failure is not established",
             "claim_text": "Motor failure is not established."},
        ],
    }
    returned = {
        "schema": RETURN_SCHEMA,
        "opaque_response_id": "synthetic-01",
        "claim_roles": [
            {"item_id": "c1", "stance": "ASSERTED_CURRENT_EPISODE",
             "claim_kind": "RECOVERY_TRACE_EVENT", "polarity": "POSITIVE",
             "rationale_span": "Wait completion"},
            {"item_id": "c2", "stance": "INFERENCE_LIMITATION",
             "claim_kind": "SPECIFIC_PHYSICAL_CAUSE", "polarity": "NOT_APPLICABLE",
             "rationale_span": "motor failure is not established"},
        ],
        "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT",
    }
    return payload, returned


def test_v2_structure_is_valid_but_never_authorizes_scoring() -> None:
    payload, returned = example()
    result = validate(payload, returned)
    assert result["claim_count"] == 2
    assert result["role_kind_polarity_qualified"] is False
    assert result["endpoint_scoring_authorized"] is False


def test_v2_rejects_limitation_as_negative_physical_finding() -> None:
    payload, returned = example()
    altered = deepcopy(returned)
    altered["claim_roles"][1]["polarity"] = "NEGATIVE"
    with pytest.raises(ValueError, match="cannot carry episode polarity"):
        validate(payload, altered)


def test_v2_rejects_rationale_from_another_atom() -> None:
    payload, returned = example()
    altered = deepcopy(returned)
    altered["claim_roles"][1]["rationale_span"] = "Wait completion"
    with pytest.raises(ValueError, match="its own claim span"):
        validate(payload, altered)


def test_v2_rejects_missing_or_reordered_claims() -> None:
    payload, returned = example()
    altered = deepcopy(returned)
    altered["claim_roles"].reverse()
    with pytest.raises(ValueError, match="exactly and in order"):
        validate(payload, altered)
