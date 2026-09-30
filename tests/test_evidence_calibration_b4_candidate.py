from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "tests"))
from test_evidence_calibration_b3_ordinary import inputs
from prepare_evidence_calibration_b4_candidate import prepare, retain_and_realize
from realize_evidence_calibrated_explanation_v2 import realize
from maximal_supported_diagnosis import diagnose


def draft(request, plan):
    clauses = [{"clause_id": identifier, "kind": "CLAIM", "contract_id": identifier,
                "numeric_values": [{k: row[k] for k in ("slot_id", "value", "unit")}
                                   for row in plan["approved_numeric_values"] if row["claim_id"] == identifier]}
               for identifier in plan["required_claim_ids"]]
    clauses += [{"clause_id": identifier, "kind": "NON_ENTAILMENT", "contract_id": identifier,
                 "numeric_values": []} for identifier in plan["required_non_entailment_ids"]]
    return {"schema": "crane-claim-realization-candidate/v1", "response_id": request["response_id"],
            "plan_sha256": request["plan_sha256"], "clauses": clauses}


def record(request, candidate):
    raw = json.dumps(candidate)
    return {"schema": "crane-explain-model-call/v1", "return_code": 0, "timed_out": False,
            "request": {"prompt": request["prompt"], "schema": request["output_schema"]},
            "raw_final": raw, "parsed_final": json.loads(raw)}


def test_complete_candidate_retained_and_exact_existing_v2_result_used():
    args = inputs()
    before = deepcopy(args)
    request = prepare(*args)
    candidate = draft(request, args[3])
    returned = record(request, candidate)
    output = retain_and_realize(*args, request, returned)
    assert args == before
    assert output["candidate"] == candidate
    expected = realize(args[0], diagnose(*args[:3]), args[3], candidate)
    assert output["realization"] == expected
    assert expected["audit"]["status"] == "ACCEPTED"
    assert output["model_retry_authorized"] is False
    assert output["endpoint_scoring_authorized"] is False
    assert prepare(*args) == request


@pytest.mark.parametrize("mutation", ["unsupported", "wrong_number", "empty"])
def test_semantic_candidate_errors_are_retained_with_explicit_local_repair(mutation):
    args = inputs()
    request = prepare(*args)
    candidate = draft(request, args[3])
    if mutation == "unsupported":
        candidate["clauses"].append({"clause_id": "unsupported", "kind": "CLAIM",
                                     "contract_id": "claim-motor-failure", "numeric_values": []})
    elif mutation == "wrong_number":
        next(c for c in candidate["clauses"] if c["numeric_values"])["numeric_values"][0]["value"] = 99
    else:
        candidate["clauses"] = []
    output = retain_and_realize(*args, request, record(request, candidate))
    assert output["candidate"] == candidate
    assert output["realization"]["audit"]["status"] == "REPAIRED"
    assert not output["realization"]["audit"]["missing_required_claim_ids"]
    assert not output["realization"]["audit"]["missing_limitation_ids"]


@pytest.mark.parametrize("mutation", ["request", "prompt", "parsed", "technical", "response_id", "prose", "nan"])
def test_identity_transport_and_structural_failures_do_not_compile(mutation):
    args = inputs()
    request = prepare(*args)
    candidate = draft(request, args[3])
    if mutation == "response_id":
        candidate["response_id"] = "different"
    elif mutation == "prose":
        candidate["answer"] = "An invented prose channel."
    elif mutation == "nan":
        next(c for c in candidate["clauses"] if c["numeric_values"])["numeric_values"][0]["value"] = float("nan")
    returned = record(request, candidate)
    if mutation == "request":
        request["plan_sha256"] = "0" * 64
    elif mutation == "prompt":
        returned["request"]["prompt"] += "changed"
    elif mutation == "parsed":
        returned["parsed_final"]["clauses"] = []
    elif mutation == "technical":
        returned["return_code"] = 1
    with pytest.raises(ValueError):
        retain_and_realize(*args, request, returned)


def test_request_excludes_unsupported_propositions_and_binds_plan_limits():
    args = inputs()
    request = prepare(*args)
    context = json.loads(request["prompt"].split("Governed candidate data:\n", 1)[1])
    assert context["diagnostic_plan"] == json.loads(json.dumps(args[3]))
    assert context["robot_visible_evidence"] == args[1]["method_packet"]
    assert "claim-motor-failure" not in {c["claim_id"] for c in context["approved_propositions"]}
    assert {r["non_entailment_id"] for r in context["required_limitations"]} == set(args[3]["required_non_entailment_ids"])


def test_duplicate_raw_json_keys_are_rejected():
    args = inputs()
    request = prepare(*args)
    returned = record(request, draft(request, args[3]))
    returned["raw_final"] = returned["raw_final"].replace('"clauses":', '"clauses": [], "clauses":', 1)
    with pytest.raises(ValueError, match="duplicate JSON key"):
        retain_and_realize(*args, request, returned)


def test_boolean_numeric_value_is_structural_failure():
    args = inputs()
    request = prepare(*args)
    candidate = draft(request, args[3])
    next(c for c in candidate["clauses"] if c["numeric_values"])["numeric_values"][0]["value"] = True
    with pytest.raises(ValueError, match="numeric structure"):
        retain_and_realize(*args, request, record(request, candidate))
