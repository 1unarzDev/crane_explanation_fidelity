from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from audit_evidence_calibration_pilot_atomization import uncovered_text  # noqa: E402
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, RETURN_SCHEMA, validate  # noqa: E402


def test_revised_reference_preserves_original_review_input() -> None:
    revised = json.loads((ROOT / "research/explanation_fidelity/qualification/evidence-calibration-claim-role-v2r2-development.json").read_text())
    original = json.loads((ROOT / "research/explanation_fidelity/qualification/evidence-calibration-claim-role-v2-development.json").read_text())
    assert revised["status"] == "UNCALLED_REVISED_CONSTRUCTION_DRAFT_NOT_FROZEN"
    assert revised["split_counts"] == {"development": 4, "heldout": 20}
    assert len(revised["cases"]) == 24
    assert sum(len(case["claims"]) for case in revised["cases"]) == 39
    assert [case["case_id"] for case in revised["cases"]] == [case["case_id"] for case in original["cases"]]
    changed = []
    for case, prior in zip(revised["cases"], original["cases"], strict=True):
        payload = {"schema": INPUT_SCHEMA, "opaque_response_id": case["case_id"],
                   "response_text": case["response_text"], "claims": case["claims"]}
        returned = {"schema": RETURN_SCHEMA, "opaque_response_id": case["case_id"],
                    "claim_roles": case["expected"],
                    "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT"}
        assert validate(payload, returned)["endpoint_scoring_authorized"] is False
        assert uncovered_text(case["response_text"], case["claims"]) == []
        if case != prior:
            changed.append(case["case_id"])
    assert changed == ["rk2-dev-03", "rk2-ho-03", "rk2-ho-04", "rk2-ho-09",
                       "rk2-ho-12", "rk2-ho-16", "rk2-ho-20"]
