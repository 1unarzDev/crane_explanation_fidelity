import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
import build_evidence_calibration_five_method_packet_candidate as candidate
from build_evidence_calibration_method_packets import build
from evidence_calibration_io import canonical_sha256
from prepare_evidence_calibration_b2_agent import prepare, retain_answer, PROMPT


@pytest.fixture
def inputs():
    diagnostic = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-043/command-motion-diagnostic-v3.json").read_text())
    catalog = json.loads((ROOT / candidate.CATALOG).read_text())
    entry = candidate.materialize(diagnostic, "test-configuration", "measured_response_recovery", catalog)[-1]
    return entry, build(entry, candidate.execution_contract(entry, diagnostic))


def record(request, answer):
    raw = json.dumps({"answer": answer})
    return {"schema": "crane-explain-model-call/v1", "return_code": 0, "timed_out": False,
            "request": {"prompt": request["prompt"], "schema": request["output_schema"]},
            "raw_final": raw, "parsed_final": json.loads(raw),
            "events": [{"type": "tool_use", "tool": "local_computation"}]}


def test_request_preserves_prompt_visible_access_and_stable_workspace_identity(inputs):
    original = copy.deepcopy(inputs)
    request = prepare(*inputs)
    assert inputs == original
    assert request == prepare(*inputs)
    assert request["prompt"].startswith(PROMPT.read_text())
    assert inputs[0]["method_packet"]["question"] in request["prompt"]
    assert "local computations" in request["prompt"]
    assert len(request["workspace_identity"]["inventory"]["files"]) == 5
    assert "contracts/claim_contracts.json" not in request["workspace_identity"]["inventory"]["files"]
    assert request["harness_permissions_enforced"] is False
    assert request["model_calls_authorized"] is False
    assert "approved_claim_ids" not in request["prompt"]


@pytest.mark.parametrize("answer", ["", "Motor failure caused the abort.", "Measured speed was 99 m/s.",
                                    "Navigation succeeded.\n\nEvidence is limited."])
def test_answers_remain_verbatim_and_tool_events_are_not_semantic_rejected(inputs, answer):
    request = prepare(*inputs)
    output = retain_answer(*inputs, request, record(request, answer))
    assert output["answer"] == answer
    assert output["semantic_verification_executed"] is False
    assert output["fallback_executed"] is False
    assert output["harness_event_audit_required"] is True
    assert output["endpoint_scoring_authorized"] is False


@pytest.mark.parametrize("mutation", ["asset", "contract", "flag", "method", "missing", "evidence"])
def test_packet_mutations_rejected_before_request(inputs, mutation):
    entry, packets = copy.deepcopy(inputs)
    packet = next(p for p in packets["method_packets"] if p["method_id"] == "B2")
    if mutation == "asset": packet["source_assets"][0]["sha256"] = "0" * 64
    elif mutation == "contract": packet["contract_assets"] = next(p for p in packets["method_packets"] if p["method_id"] == "B4")["contract_assets"]
    elif mutation == "flag": packet["final_claim_verification"] = True
    elif mutation == "method": packet["method_class"] = "FULL_EVIDENCE_CALIBRATED"
    elif mutation == "missing": packets["method_packets"].pop()
    else: entry["method_packet"]["question"] = "changed"
    packet["packet_sha256"] = canonical_sha256({k:v for k,v in packet.items() if k != "packet_sha256"})
    with pytest.raises(ValueError): prepare(entry, packets)


@pytest.mark.parametrize("mutation", ["request", "prompt", "parsed", "technical", "duplicate"])
def test_technical_and_identity_failures_are_retained_without_fallback(inputs, mutation):
    request = prepare(*inputs)
    returned = record(request, "Navigation succeeded.")
    if mutation == "request": request["condition_id"] = "different"
    elif mutation == "prompt": returned["request"]["prompt"] += "changed"
    elif mutation == "parsed": returned["parsed_final"]["answer"] = "replacement"
    elif mutation == "technical": returned["return_code"] = 1
    else: returned["raw_final"] = '{"answer":"first","answer":"Navigation succeeded."}'
    with pytest.raises(ValueError): retain_answer(*inputs, request, returned)
