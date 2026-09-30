import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from build_evidence_calibration_method_packets import build  # noqa: E402
from evidence_calibration_io import canonical_sha256  # noqa: E402
from prepare_evidence_calibration_baselines import decode_raw_summary, prepare, raw_summary, retain_answer  # noqa: E402

SPEC = importlib.util.spec_from_file_location("packet_fixtures", ROOT / "tests/test_evidence_calibration_method_packets.py")
FIXTURES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURES)


def inputs():
    entry = FIXTURES.entry()
    contract = FIXTURES.contract(entry)
    contract["ordinary_runtime_presentation"] = json.dumps(entry["method_packet"])
    contract["question_instruction"] = entry["method_packet"]["question"]
    return entry, build(entry, contract)


def record(request, answer):
    raw = json.dumps({"answer": answer})
    return {"schema": "crane-explain-model-call/v1", "return_code": 0, "timed_out": False,
            "request": {"prompt": request["prompt"], "schema": request["output_schema"]},
            "raw_final": raw, "parsed_final": json.loads(raw)}


def test_raw_summary_preserves_nested_types_ids_order_quantities_and_empty_containers():
    packet = {"episode_id": "épisode-01", "question": "What happened?\nWhy?", "configuration_id": "cfg",
              "evidence": {"stream": {"samples": [{"value": 0.04, "valid": True}, {"value": -3, "valid": False}],
                                      "empty_list": [], "empty_object": {}, "missing": None,
                                      "evidence_ids": ["ev-2", "ev-1"], "literal": 'quote ".":\nRetained record x'},
                           "role/with~punctuation": {"value": "no numerical conclusion"}}}
    text = raw_summary(packet)
    assert decode_raw_summary(text) == packet
    assert text.startswith('Episode field "configuration_id":')
    assert 'Retained record "stream":' in text
    assert decode_raw_summary(text)["evidence"]["stream"]["samples"][0]["valid"] is True


def test_distinct_presentations_preserve_identical_evidence_and_common_instruction():
    entry, packets = inputs()
    b0, b1 = [prepare(method, entry, packets) for method in ("B0", "B1")]
    assert b0["prompt_template_sha256"] == b1["prompt_template_sha256"]
    assert b0["method_packet_sha256"] == b1["method_packet_sha256"]
    assert b0["presentation_sha256"] != b1["presentation_sha256"]
    text = b0["prompt"].split("Ordinary retained runtime summary:\n", 1)[1]
    structured = b1["prompt"].split("Structured retained runtime record:\n", 1)[1]
    assert decode_raw_summary(text) == json.loads(structured) == entry["method_packet"]


@pytest.mark.parametrize("method", ["B0", "B1"])
@pytest.mark.parametrize("answer", ["", "Motor failure caused the abort.", "Measured speed was 99 m/s.\n"])
def test_baseline_answers_are_retained_without_semantic_repair(method, answer):
    request = prepare(method, *inputs())
    output = retain_answer(request, record(request, answer))
    assert output["method"] == method
    assert output["answer"] == answer
    assert output["fallback_executed"] is False
    assert output["semantic_verification_executed"] is False
    assert output["endpoint_scoring_authorized"] is False


def test_injected_contracts_and_lost_runtime_values_are_rejected():
    entry, packets = inputs()
    packet = packets["method_packets"][0]
    packet["contract_assets"] = [{"asset_id": "forbidden-contract", "version": "v1", "sha256": "1" * 64}]
    packet["packet_sha256"] = canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})
    with pytest.raises(ValueError, match="cannot receive"):
        prepare("B0", entry, packets)
    entry, packets = inputs()
    packet = packets["method_packets"][0]
    visible = json.loads(packet["presentation"])
    visible["evidence"].pop(next(iter(visible["evidence"])))
    packet["presentation"] = json.dumps(visible)
    packet["packet_sha256"] = canonical_sha256({k: v for k, v in packet.items() if k != "packet_sha256"})
    with pytest.raises(ValueError, match="same-evidence"):
        prepare("B0", entry, packets)


def test_private_truth_and_nonfinite_runtime_values_fail_closed():
    packet = {"evidence": {"physical_truth": "motor failure"}}
    with pytest.raises(ValueError, match="evaluator-only"):
        raw_summary(packet)
    with pytest.raises(ValueError, match="JSON compliant"):
        raw_summary({"evidence": {"stream": {"value": float("nan")}}})


def test_duplicate_raw_summary_fields_and_suffix_prose_are_rejected():
    text = raw_summary({"episode_id": "ep", "evidence": {}})
    with pytest.raises(ValueError, match="duplicate"):
        decode_raw_summary(text + "\n" + text)
    with pytest.raises(ValueError, match="suffix"):
        decode_raw_summary(text + " This caused failure.")


def test_technical_failure_stale_request_and_changed_raw_answer_are_rejected():
    request = prepare("B0", *inputs())
    returned = record(request, "The episode aborted.")
    returned["return_code"] = 124
    with pytest.raises(ValueError, match="technical failure"):
        retain_answer(request, returned)
    returned = record(request, "The episode aborted.")
    returned["parsed_final"]["answer"] = "A different answer."
    with pytest.raises(ValueError, match="raw/parsed"):
        retain_answer(request, returned)
    request["method"] = "B1"
    with pytest.raises(ValueError, match="integrity"):
        retain_answer(request, returned)
