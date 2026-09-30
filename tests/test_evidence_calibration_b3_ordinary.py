from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_method_packets import build as build_packets  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
from maximal_supported_diagnosis import diagnose  # noqa: E402
from prepare_evidence_calibration_b3_ordinary import prepare, retain_answer  # noqa: E402

SPEC = importlib.util.spec_from_file_location("realization_fixtures", ROOT / "tests/test_claim_aware_realization.py")
FIXTURES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURES)


def inputs():
    ontology = json.loads((ROOT / "configs/evidence_calibration_claim_contracts_v2_development.json").read_text())
    entry = FIXTURES.FIXTURES.entry("e3")
    facts = FIXTURES.FIXTURES.fact_packet(entry)
    result = diagnose(ontology, entry, facts)
    plan = FIXTURES.plan(result)
    asset = {"asset_id": "synthetic-source", "version": "v1", "sha256": "1" * 64}
    contract = {"contract_id": "synthetic-ordinary-test", "ordinary_runtime_presentation": json.dumps(entry["method_packet"]),
                "presentation_evidence_ids": list(entry["condition"]["available_evidence_ids"]),
                "source_assets": [asset], "primitive_tools": [asset],
                "question_instruction": entry["method_packet"]["question"], "contract_assets": [asset]}
    return ontology, entry, facts, plan, build_packets(entry, contract)


def record(request, answer):
    raw = json.dumps({"answer": answer})
    return {"schema": "crane-explain-model-call/v1", "return_code": 0, "timed_out": False,
            "request": {"prompt": request["prompt"], "schema": request["output_schema"]},
            "raw_final": raw, "parsed_final": json.loads(raw)}


def test_request_exports_supported_plan_and_preserves_v2_limitations():
    args = inputs()
    before = deepcopy(args)
    request = prepare(*args)
    assert args == before
    context = json.loads(request["prompt"].split("Governed realization data:\n", 1)[1])
    assert context["robot_visible_evidence"] == args[1]["method_packet"]
    identifiers = {row["claim_id"] for row in context["diagnostic_plan"]["approved_claims"]}
    assert identifiers == set(args[3]["required_claim_ids"])
    assert "claim-motor-failure" not in identifiers
    assert context["diagnostic_plan"]["approved_numeric_values"] == args[3]["approved_numeric_values"]
    text = " ".join(row["text"] for row in context["diagnostic_plan"]["required_limitations"])
    assert "these specific physical causes" not in text
    assert "motor failure, collision, wheel slip, or external obstruction" in text


@pytest.mark.parametrize("answer", ["", "  ", "Motor failure caused the abort.", "Measured speed was 99 m/s.",
                                    "Navigation aborted.\n\nThere is no limitation."])
def test_ordinary_answer_is_preserved_without_verification_fallback_or_repair(answer):
    request = prepare(*inputs())
    output = retain_answer(request, record(request, answer))
    assert output["answer"] == answer
    assert output["semantic_verification_executed"] is False
    assert output["answer_repaired"] is False
    assert output["fallback_executed"] is False
    assert output["endpoint_scoring_authorized"] is False


def test_changed_packet_or_b2_parity_is_rejected_before_request():
    args = list(inputs())
    packet = next(item for item in args[-1]["method_packets"] if item["method_id"] == "B2")
    packet["source_assets"] = []
    packet["packet_sha256"] = canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})
    with pytest.raises(ValueError, match="parity changed"):
        prepare(*args)


def test_stale_facts_and_plan_bindings_are_rejected():
    args = list(inputs())
    args[2]["method_packet_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="bind|bound"):
        prepare(*args)
    args = list(inputs())
    args[3]["diagnostic_result_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="bound"):
        prepare(*args)


def test_evaluator_only_fields_cannot_enter_request():
    args = list(inputs())
    args[1]["method_packet"]["nested"] = {"physical_truth": "motor failure"}
    with pytest.raises(ValueError, match="evaluator-only"):
        prepare(*args)


def test_raw_parsed_inconsistency_and_technical_failure_are_rejected():
    request = prepare(*inputs())
    returned = record(request, "Navigation aborted.")
    returned["parsed_final"]["answer"] = "A replacement answer."
    with pytest.raises(ValueError, match="raw/parsed"):
        retain_answer(request, returned)
    returned = record(request, "Navigation aborted.")
    returned["return_code"] = 1
    with pytest.raises(ValueError, match="technical failure"):
        retain_answer(request, returned)


def test_request_and_call_prompt_identity_are_bound():
    request = prepare(*inputs())
    returned = record(request, "Navigation aborted.")
    returned["request"]["prompt"] += " Modified instruction."
    with pytest.raises(ValueError, match="prompt or output-schema"):
        retain_answer(request, returned)
    request["prompt"] += " Modified instruction."
    with pytest.raises(ValueError, match="request integrity"):
        retain_answer(request, returned)
