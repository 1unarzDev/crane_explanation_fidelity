from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPT = Path(__file__).parents[1] / "analysis" / "luna_model_judge.py"
SPEC = importlib.util.spec_from_file_location("luna_model_judge", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

ARM_ID = MODULE.ARM_ID
LunaResponsesCaller = MODULE.LunaResponsesCaller
packet_envelope = MODULE.packet_envelope
parse_sse_response = MODULE.parse_sse_response
qualification_envelope = MODULE.qualification_envelope
request_body = MODULE.request_body
validate_judgment = MODULE.validate_judgment


def case() -> dict:
    return {
        "case_id": "qualification-opaque-001",
        "rubric": "diagnostic",
        "question": "Why did navigation fail?",
        "evidence_completeness": "Complete for the declared mechanism.",
        "allowed_evidence": [{"id": "e1", "fact": "Opening 0.50 m"}],
        "required_units": [{"unit_id": "u1", "text": "Opening is 0.50 m"}],
        "candidate_answer": "The opening was 0.50 m.",
    }


def judgment(pass_id: str = "qualification") -> dict:
    return {
        "schema": "crane-luna-model-judge-output/v1",
        "annotation_origin": "automated",
        "arm_id": ARM_ID,
        "opaque_response_id": "qualification-opaque-001",
        "pass_id": pass_id,
        "rubric": "diagnostic",
        "judgment_status": "resolved",
        "answerability": "answerable",
        "material_error": False,
        "material_error_categories": [],
        "claims": [],
        "required_units": [
            {"unit_id": "u1", "status": "covered", "response_span": "0.50 m", "justification": "Matches e1."}
        ],
        "disposition": "full",
        "mechanism_identification": "correct",
        "correct_abstention": None,
        "causal_overclaim": False,
        "evidence_problem": False,
        "evidence_problem_detail": None,
        "unresolved_fields": [],
        "rationale": "The answer matches e1.",
    }


class FakeResponse:
    status = 200

    def __init__(self, body: dict):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self.body


def test_qualification_envelope_contains_no_expected_label_or_condition():
    source = {**case(), "expected": {"material_error": False}, "condition": "P"}
    envelope = qualification_envelope(source, "qualification")
    serialized = json.dumps(envelope)
    assert "expected" not in serialized
    assert "condition" not in serialized
    assert envelope["opaque_response_id"] == "qualification-opaque-001"


def test_packet_envelope_rejects_condition_revealing_fields():
    with pytest.raises(ValueError, match="unsupported fields"):
        packet_envelope(
            {
                "response_id": "opaque",
                "question": "Why?",
                "response_text": "Because.",
                "allowed_evidence": {},
                "condition": "P",
            },
            "diagnostic",
            "pass-1",
        )


def test_request_exposes_no_tools_and_omits_sampling_settings():
    envelope = qualification_envelope(case(), "qualification")
    body = request_body(
        prompt="prompt", rubric_text="rubric", envelope=envelope, schema={"type": "object"}, effort="medium"
    )
    assert body["tools"] == []
    assert body["stream"] is False
    assert "temperature" not in body
    assert "seed" not in body
    assert body["reasoning"] == {"effort": "medium"}


def test_validator_rejects_identity_rewrite():
    envelope = qualification_envelope(case(), "qualification")
    value = judgment()
    value["opaque_response_id"] = "different"
    with pytest.raises(ValueError, match="does not match request"):
        validate_judgment(value, envelope)


def test_valid_call_is_cached_and_does_not_send_expected_labels(tmp_path: Path):
    output = judgment()
    provider = {
        "id": "resp_test",
        "model": "gpt-6-luna",
        "output": [{"content": [{"type": "output_text", "text": json.dumps(output)}]}],
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    calls = []

    def opener(request, timeout):
        calls.append((request, timeout))
        return FakeResponse(provider)

    with patch.dict("os.environ", {"CODEX_LB_API_KEY": "secret"}):
        caller = LunaResponsesCaller(
            cache=tmp_path, effort="medium", base_url="https://example.invalid/v1", opener=opener
        )
        envelope = qualification_envelope(case(), "qualification")
        first = caller.call(envelope)
        second = caller.call(envelope)
    assert first == second
    assert len(calls) == 1
    sent = json.loads(calls[0][0].data)
    assert sent["tools"] == []
    assert "expected" not in json.dumps(sent)
    assert "secret" not in json.dumps(first)
    assert first["status"] == "VALID"


def test_invalid_usable_response_is_retained_without_retry(tmp_path: Path):
    calls = []

    def opener(request, timeout):
        calls.append(request)
        return FakeResponse({"id": "bad", "output_text": "not-json"})

    with patch.dict("os.environ", {"CODEX_LB_API_KEY": "secret"}):
        caller = LunaResponsesCaller(
            cache=tmp_path, effort="low", base_url="https://example.invalid/v1", opener=opener
        )
        with pytest.raises(RuntimeError, match="invalid Luna judgment"):
            caller.call(qualification_envelope(case(), "qualification"))
    assert len(calls) == 1
    retained = json.loads(next(tmp_path.glob("*.json")).read_text())
    assert retained["status"] == "INVALID_JUDGMENT_NO_RETRY"


def test_sse_parser_returns_completed_response_without_metadata_headers():
    completed = {
        "id": "resp_test",
        "output": [{"content": [{"type": "output_text", "text": "{}"}]}],
    }
    payload = (
        'event: codex.response.metadata\ndata: {"type":"codex.response.metadata",'
        '"headers":{"x-codex-turn-state":"secret-state"}}\n\n'
        f'event: response.completed\ndata: {json.dumps({"type": "response.completed", "response": completed})}\n\n'
        "data: [DONE]\n\n"
    ).encode()
    response, terminal = parse_sse_response(payload)
    assert response == completed
    assert terminal == {"event": "response.completed", "response_id": "resp_test", "error": None}
    assert "secret-state" not in json.dumps(terminal)


def test_sse_parser_sanitizes_stream_failure():
    payload = (
        'event: response.failed\ndata: {"type":"response.failed","response":'
        '{"id":"ws_1","error":{"type":"server_error","code":"stream_incomplete",'
        '"message":"upstream closed"}}}\n\ndata: [DONE]\n\n'
    ).encode()
    response, terminal = parse_sse_response(payload)
    assert response is None
    assert terminal["response_id"] == "ws_1"
    assert terminal["error"]["code"] == "stream_incomplete"
