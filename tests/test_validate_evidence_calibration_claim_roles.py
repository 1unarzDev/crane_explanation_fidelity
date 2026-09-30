import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from validate_evidence_calibration_claim_roles import validate_claim_roles  # noqa: E402
from audit_evidence_calibration_claim_role_freeze import audit as audit_role_freeze  # noqa: E402


def input_payload():
    return {
        "schema": "crane-evidence-calibration-claim-role-input/v1-development",
        "opaque_response_id": "blind-1",
        "response_text": "A command was issued, but measured response cannot be assessed because odometry is unavailable.",
        "claims": [
            {"item_id": "c1", "response_span": "A command was issued", "claim_text": "A command was issued."},
            {"item_id": "c2", "response_span": "measured response cannot be assessed because odometry is unavailable",
             "claim_text": "Measured response cannot be assessed because odometry is unavailable."},
        ],
    }


def role_return():
    return {
        "schema": "crane-evidence-calibration-claim-role-return/v1-development",
        "opaque_response_id": "blind-1",
        "claim_roles": [
            {"item_id": "c1", "role": "NON_DIAGNOSTIC_OBSERVATION_OR_SOURCE",
             "asserted_diagnostic_level": None, "rationale_span": "A command was issued"},
            {"item_id": "c2", "role": "LIMITATION_OR_NON_ENTAILMENT",
             "asserted_diagnostic_level": None, "rationale_span": "measured response cannot be assessed"},
        ],
        "attestation": "METHOD_BLIND_ASSERTION_ROLE_ATTEMPT",
    }


def test_limitation_does_not_create_asserted_diagnostic_rank():
    result = validate_claim_roles(input_payload(), role_return())
    assert result["affirmative_asserted_levels"] == []
    assert result["hedged_diagnostic_candidate_levels"] == []
    assert result["mechanistic_flag_authorized"] is False
    assert result["response_rank_authorized"] is False
    assert result["endpoint_scoring_authorized"] is False


def test_affirmative_diagnosis_is_retained_without_evidence_or_method_identity():
    payload = input_payload()
    payload["response_text"] = "Commanded motion was not reflected in measured robot motion."
    payload["claims"] = [{"item_id": "c1", "response_span": payload["response_text"],
                          "claim_text": payload["response_text"]}]
    result = role_return()
    result["claim_roles"] = [{"item_id": "c1", "role": "AFFIRMATIVE_EPISODE_ASSERTION",
                              "asserted_diagnostic_level": "command_motion_discrepancy",
                              "rationale_span": "not reflected in measured robot motion"}]
    assert validate_claim_roles(payload, result)["affirmative_asserted_levels"] == ["command_motion_discrepancy"]


def test_nonaffirmative_level_and_missing_claim_are_rejected():
    bad = role_return()
    bad["claim_roles"][1]["asserted_diagnostic_level"] = "specific_physical_cause"
    with pytest.raises(ValueError, match="non-affirmative"):
        validate_claim_roles(input_payload(), bad)
    bad = role_return()
    bad["claim_roles"].pop()
    with pytest.raises(ValueError, match="every atomic claim"):
        validate_claim_roles(input_payload(), bad)


def test_return_cannot_swap_ids_or_invent_a_quote():
    bad = role_return()
    bad["claim_roles"][0]["item_id"] = "different"
    with pytest.raises(ValueError, match="match the input"):
        validate_claim_roles(input_payload(), bad)
    bad = copy.deepcopy(role_return())
    bad["claim_roles"][0]["rationale_span"] = "motor failure"
    with pytest.raises(ValueError, match="atomic claim span"):
        validate_claim_roles(input_payload(), bad)


def test_role_rationale_cannot_be_borrowed_from_another_claim():
    bad = role_return()
    bad["claim_roles"][0]["rationale_span"] = "odometry is unavailable"
    assert bad["claim_roles"][0]["rationale_span"] in input_payload()["response_text"]
    with pytest.raises(ValueError, match="atomic claim span"):
        validate_claim_roles(input_payload(), bad)


def test_malformed_role_and_level_fail_as_validation_errors():
    bad = role_return()
    bad["claim_roles"][0]["role"] = ["AFFIRMATIVE_EPISODE_ASSERTION"]
    with pytest.raises(ValueError, match="unknown assertion role"):
        validate_claim_roles(input_payload(), bad)
    bad = role_return()
    bad["claim_roles"][0] = {"item_id": "c1", "role": "AFFIRMATIVE_EPISODE_ASSERTION",
                             "asserted_diagnostic_level": ["task_outcome"],
                             "rationale_span": "A command was issued"}
    with pytest.raises(ValueError, match="declared abstraction level"):
        validate_claim_roles(input_payload(), bad)


def test_synthetic_suite_has_complete_independent_reference_and_no_endpoint_authorization():
    suite = json.loads((ROOT / "research/explanation_fidelity/qualification/evidence-calibration-claim-role-v1-development.json").read_text())
    assert suite["status"] == "FROZEN_SYNTHETIC_ROLE_QUALIFICATION_INPUT_BEFORE_CALLS"
    cases = suite["cases"]
    assert len(cases) == 24
    assert len({case["case_id"] for case in cases}) == 24
    assert {split: sum(case["split"] == split for case in cases)
            for split in ("development", "heldout")} == suite["split_counts"]
    roles = set()
    for case in cases:
        payload = {"schema": "crane-evidence-calibration-claim-role-input/v1-development",
                   "opaque_response_id": case["case_id"], "response_text": case["response_text"],
                   "claims": case["claims"]}
        returned = {"schema": "crane-evidence-calibration-claim-role-return/v1-development",
                    "opaque_response_id": case["case_id"],
                    "claim_roles": [{**expected, "rationale_span": claim["response_span"]}
                                    for claim, expected in zip(case["claims"], case["expected"], strict=True)],
                    "attestation": "METHOD_BLIND_ASSERTION_ROLE_ATTEMPT"}
        assert [item["item_id"] for item in case["claims"]] == [item["item_id"] for item in case["expected"]]
        check = validate_claim_roles(payload, returned)
        assert check["endpoint_scoring_authorized"] is False
        roles.update(item["role"] for item in case["expected"])
    assert roles == {"AFFIRMATIVE_EPISODE_ASSERTION", "HEDGED_DIAGNOSTIC_CANDIDATE",
                     "NON_DIAGNOSTIC_OBSERVATION_OR_SOURCE", "LIMITATION_OR_NON_ENTAILMENT",
                     "HYPOTHETICAL_OR_ATTRIBUTED"}


def test_hedged_current_run_diagnosis_is_retained_for_prospective_mapping():
    suite = json.loads((ROOT / "research/explanation_fidelity/qualification/evidence-calibration-claim-role-v1-development.json").read_text())
    case = next(item for item in suite["cases"] if item["case_id"] == "role-ho-08")
    payload = {"schema": "crane-evidence-calibration-claim-role-input/v1-development",
               "opaque_response_id": case["case_id"], "response_text": case["response_text"],
               "claims": case["claims"]}
    returned = {"schema": "crane-evidence-calibration-claim-role-return/v1-development",
                "opaque_response_id": case["case_id"],
                "claim_roles": [{**expected, "rationale_span": claim["response_span"]}
                                for claim, expected in zip(case["claims"], case["expected"], strict=True)],
                "attestation": "METHOD_BLIND_ASSERTION_ROLE_ATTEMPT"}
    result = validate_claim_roles(payload, returned)
    assert result["affirmative_asserted_levels"] == []
    assert result["hedged_diagnostic_candidate_levels"] == ["specific_physical_cause"] * 2
    assert not result["endpoint_scoring_authorized"]


def test_construction_review_binds_every_synthetic_case_before_model_calls():
    review = json.loads((ROOT / "manifests/annotation/evidence-calibration-claim-role-v1-construction-review.json").read_text())
    assert review["status"] == "PROJECT_CONSTRUCTION_REVIEW_COMPLETE_BEFORE_ROLE_MODEL_CALLS"
    assert review["model_calls_observed"] == 0
    assert review["endpoint_scoring_authorized"] is False
    assert review["exact_response_overlap_with_prior_synthetic_qualification_suites"] == 0
    for field in ("suite", "prompt", "return_schema"):
        bound = review[field]
        assert hashlib.sha256((ROOT / bound["path"]).read_bytes()).hexdigest() == bound["raw_sha256"]
    suite = json.loads((ROOT / review["suite"]["path"]).read_text())
    assert review["case_count"] == len(suite["cases"]) == 24
    assert review["development_count"] == 4
    assert review["heldout_count"] == 20
    assert [case["case_id"] for case in review["cases"]] == [case["case_id"] for case in suite["cases"]]
    assert all(row["atomic_meaning_count"] == len(case["claims"])
               for row, case in zip(review["cases"], suite["cases"], strict=True))


def test_role_qualification_freeze_is_hash_bound_and_does_not_authorize_pilot():
    result = audit_role_freeze()
    assert result["status"] == "PASS_SYNTHETIC_TASK_FROZEN_NO_MODEL_QUALIFICATION"
    assert result["synthetic_cases"] == 24
    assert result["model_calls_made_by_audit"] == 0
    assert result["pilot_role_annotation_authorized"] is False


def test_role_qualification_freeze_rejects_component_hash_mismatch(tmp_path):
    path = ROOT / "research/explanation_fidelity/experiment_configs/prospective/evidence-calibration-claim-role-v1-freeze.json"
    freeze = json.loads(path.read_text())
    freeze["candidate"]["prompt"]["raw_sha256"] = "0" * 64
    changed = tmp_path / "changed-freeze.json"
    changed.write_text(json.dumps(freeze))
    with pytest.raises(ValueError, match="frozen component hash mismatch"):
        audit_role_freeze(changed)
