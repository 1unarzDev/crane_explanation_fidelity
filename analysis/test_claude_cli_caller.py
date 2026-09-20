"""Offline tests for the Claude Code CLI adapter.

These exercise only the deterministic parts of the adapter: out-of-band schema delivery, fenced-result
extraction, provider-usage mapping onto the retained Codex key names, and the workspace-integrity
digest that substitutes for the Codex read-only sandbox. No model call is made.
"""

from __future__ import annotations

import json

import pytest
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
