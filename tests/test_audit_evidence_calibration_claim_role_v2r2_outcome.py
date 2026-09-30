import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_claim_role_v2r2_outcome import OUTCOME, verify  # noqa: E402


def test_retained_outcome_is_bound_and_keeps_p11_closed():
    result = verify()
    assert result["retained_calls"] == 49
    assert result["heldout_exact_matches"] == {"A": 20, "B": 20}
    assert result["pilot_role_annotation_authorized"] is False
    assert result["p11_authorized"] is False


def test_outcome_cannot_authorize_endpoint_scoring(tmp_path):
    outcome = json.loads(OUTCOME.read_text())
    outcome["endpoint_scoring_authorized"] = True
    path = tmp_path / "changed-outcome.json"
    path.write_text(json.dumps(outcome))
    with pytest.raises(ValueError, match="governance boundary"):
        verify(path)
