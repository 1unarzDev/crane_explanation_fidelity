from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from validate_evidence_calibration_claim_roles_v2 import INPUT_SCHEMA, RETURN_SCHEMA, validate  # noqa: E402


def test_v2_draft_reference_is_structural_and_fresh_from_v1() -> None:
    suite = json.loads((ROOT / "research/explanation_fidelity/qualification/evidence-calibration-claim-role-v2-development.json").read_text())
    prior = json.loads((ROOT / "research/explanation_fidelity/qualification/evidence-calibration-claim-role-v1-development.json").read_text())
    assert suite["status"] == "UNCALLED_CONSTRUCTION_DRAFT_NOT_FROZEN"
    assert suite["split_counts"] == {"development": 4, "heldout": 20}
    assert len(suite["cases"]) == 24
    assert len({case["case_id"] for case in suite["cases"]}) == 24
    assert not ({case["response_text"] for case in suite["cases"]}
                & {case["response_text"] for case in prior["cases"]})
    assert sum(len(case["claims"]) for case in suite["cases"]) == 41
    for case in suite["cases"]:
        payload = {"schema": INPUT_SCHEMA, "opaque_response_id": case["case_id"],
                   "response_text": case["response_text"], "claims": case["claims"]}
        returned = {"schema": RETURN_SCHEMA, "opaque_response_id": case["case_id"],
                    "claim_roles": case["expected"],
                    "attestation": "METHOD_BLIND_ROLE_KIND_POLARITY_ATTEMPT"}
        result = validate(payload, returned)
        assert result["endpoint_scoring_authorized"] is False
