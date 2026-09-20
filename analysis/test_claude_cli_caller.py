"""Offline tests for the Claude Code CLI adapter.

These exercise only the deterministic parts of the adapter: out-of-band schema delivery, fenced-result
extraction, provider-usage mapping onto the retained Codex key names, and the workspace-integrity
digest that substitutes for the Codex read-only sandbox. No model call is made.
"""

from __future__ import annotations

import hashlib
import json
import types

import pytest
import claude_cli_caller
from claude_cli_caller import (
    DENIED_TOOLS,
    SCHEMA_DELIVERY,
    extract_json_object,
    usage_from_result,
    workspace_digest,
)


def test_fenced_result_parses_to_the_answer_object():
    assert extract_json_object('```json\n{"answer": "abc"}\n```') == {"answer": "abc"}


def test_bare_result_parses_without_a_fence():
    assert extract_json_object('{"answer": "abc"}') == {"answer": "abc"}


def test_result_without_a_json_object_is_rejected_not_repaired():
    with pytest.raises(json.JSONDecodeError):
        extract_json_object("I could not determine the cause.")


def test_usage_maps_cache_tokens_onto_the_retained_key_names():
    mapped = usage_from_result(
        {
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 100,
                "cache_read_input_tokens": 1000,
                "output_tokens": 7,
                "output_tokens_details": {"thinking_tokens": 3},
            }
        }
    )
    assert mapped["input_tokens"] == 1110
    assert mapped["cached_input_tokens"] == 1000
    assert mapped["output_tokens"] == 7
    assert mapped["reasoning_output_tokens"] == 3


def test_missing_usage_is_reported_as_absent_rather_than_zero():
    assert usage_from_result({"result": "{}"}) is None


def test_workspace_digest_detects_any_content_change(tmp_path):
    (tmp_path / "evidence.json").write_text("{}", encoding="utf-8")
    before = workspace_digest(tmp_path)
    (tmp_path / "evidence.json").write_text("{ }", encoding="utf-8")
    assert workspace_digest(tmp_path) != before


def test_workspace_digest_detects_an_added_file(tmp_path):
    before = workspace_digest(tmp_path)
    (tmp_path / "scratch.txt").write_text("x", encoding="utf-8")
    assert workspace_digest(tmp_path) != before


def test_absent_workspace_digests_compare_equal_for_the_generation_only_condition():
    assert workspace_digest(None) == workspace_digest(None)


def test_schema_is_delivered_out_of_band_so_the_frozen_prompt_is_unmodified():
    """The in-band suffix revision altered the pinned prompt and is not used."""

    assert SCHEMA_DELIVERY == "out_of_band_json_schema_flag"


def test_every_mutating_network_and_delegation_tool_is_denied():
    for tool in ("Edit", "Write", "NotebookEdit", "WebFetch", "WebSearch", "Task"):
        assert tool in DENIED_TOOLS


def _caller(tmp_path, monkeypatch):
    """Construct a caller without invoking the real CLI for its version probe."""

    monkeypatch.setattr(
        claude_cli_caller.subprocess,
        "run",
        lambda *a, **k: types.SimpleNamespace(stdout="test-cli", stderr="", returncode=0),
    )
    return claude_cli_caller.ClaudeCliCaller(tmp_path / "cache", "test-model", "low")


def _record(caller, *, parsed_final, workspace_unmodified=True, parse_error=None):
    """Write one record straight into the answer cache for the cache-hit path to read."""

    request = {
        "adapter": caller.adapter,
        "provider": "claude-code-cli",
        "model": caller.model,
        "reasoning_effort": caller.reasoning_effort,
        "temperature": None,
        "seed": None,
        "role": "condition-h-failure-cause",
        "prompt": "prompt",
        "schema": {"type": "object"},
        "cli_version": caller.cli_version,
        "workspace_identity": None,
        "schema_delivery": claude_cli_caller.SCHEMA_DELIVERY,
        "denied_tools": list(claude_cli_caller.DENIED_TOOLS),
    }
    key = hashlib.sha256(claude_cli_caller.canonical_json(request).encode()).hexdigest()
    (caller.cache / f"{key}.json").write_text(
        json.dumps(
            {
                "request": request,
                "parsed_final": parsed_final,
                "parse_error": parse_error,
                "workspace_unmodified": workspace_unmodified,
            }
        ),
        encoding="utf-8",
    )
    return request


def _call(caller, request):
    return caller.call(
        request["role"], request["prompt"], request["schema"], workspace_identity=None
    )


def test_a_successful_cached_answer_is_returned_without_a_new_call(tmp_path, monkeypatch):
    caller = _caller(tmp_path, monkeypatch)
    request = _record(caller, parsed_final={"answer": "retained"})
    assert _call(caller, request)["parsed_final"] == {"answer": "retained"}


def test_a_cached_record_without_an_answer_is_raised_not_returned(tmp_path, monkeypatch):
    """A quota or transport failure must never be replayed as if it were a retained answer."""

    caller = _caller(tmp_path, monkeypatch)
    request = _record(caller, parsed_final=None, parse_error="cli reported error: success")
    with pytest.raises(RuntimeError, match="no parsed answer"):
        _call(caller, request)


def test_a_cached_record_with_a_modified_workspace_is_raised_not_returned(tmp_path, monkeypatch):
    caller = _caller(tmp_path, monkeypatch)
    request = _record(caller, parsed_final={"answer": "x"}, workspace_unmodified=False)
    with pytest.raises(RuntimeError, match="read-only contract violated"):
        _call(caller, request)


def test_a_failed_call_is_retained_outside_the_answer_cache(tmp_path, monkeypatch):
    """The answer cache protects successful calls from resampling; a failure is not a sample."""

    caller = _caller(tmp_path, monkeypatch)
    quota_error = {
        "is_error": True,
        "subtype": "success",
        "result": "You've hit your monthly spend limit",
        "total_cost_usd": 0.047,
    }
    monkeypatch.setattr(
        claude_cli_caller.subprocess,
        "run",
        lambda *a, **k: types.SimpleNamespace(
            stdout=json.dumps(quota_error), stderr="", returncode=1
        ),
    )
    with pytest.raises(RuntimeError, match="produced no answer"):
        caller.call("condition-h-failure-cause", "prompt", {"type": "object"})

    assert not list(caller.cache.glob("*.json")), "a failed call must not enter the answer cache"
    retained = list((caller.cache / claude_cli_caller.FAILED_CALL_DIRECTORY).glob("*.json"))
    assert len(retained) == 1, "the failed call must still be retained as evidence"
    assert json.loads(retained[0].read_text())["cost_usd"] == 0.047
