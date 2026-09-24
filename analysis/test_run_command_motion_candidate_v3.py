import argparse
import json
from pathlib import Path

import pytest

from run_command_motion_candidate_v3 import run


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/robot_visible/dev/cmv2-dev-002/command-motion-diagnostic-v3.json"


class FakeCaller:
    def __init__(self):
        self.calls = []

    def call(self, call_id, prompt, schema, **kwargs):
        self.calls.append((call_id, prompt, kwargs))
        return {
            "cache_key": "r-only",
            "latency_ms": 1,
            "cost_usd": 0.0,
            "parsed_final": {"answer": "R answer"},
            "usage": {},
        }


def args(tmp_path: Path):
    return argparse.Namespace(
        evidence=EVIDENCE,
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit="8d1d308579fb4ea9f15186eb3d38a040edf52da0",
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="bea12562324fa2caf9290698cfadddcb22bd8a8b",
        repository_prompt="diagnostic_repository_agent_command_motion_dev_v2.txt",
        question="Did the discrepancy prevent continuation?",
        question_id="candidate-v3-mechanism",
        question_kind="diagnostic-mechanism-or-false-premise-v3",
        provider="codex",
        model="test-model",
        reasoning_effort="high",
        cache=tmp_path / "cache",
        output=tmp_path / "result.json",
    )


def test_v3_uses_exact_renderer_and_calls_only_r(tmp_path: Path):
    caller = FakeCaller()
    result = run(args(tmp_path), caller=caller)
    assert result["candidate"] == "bounded-command-motion-candidate-v3"
    assert result["outputs"][0]["verification_policy"] == "exact-bounded-command-motion-candidate-v3"
    assert "2 FollowPath attempts" in result["outputs"][0]["text"]
    assert len(caller.calls) == 1
    assert caller.calls[0][0] == "command-motion-candidate-v3-R"
    assert caller.calls[0][2]["workspace_identity"]["candidate_version"].endswith("v3")


def test_v3_requires_explicit_question_identity(tmp_path: Path):
    for field in ("question", "question_id", "question_kind"):
        values = args(tmp_path)
        setattr(values, field, "")
        with pytest.raises(ValueError, match=f"explicit {field}"):
            run(values, caller=FakeCaller())


def test_v3_refuses_existing_output(tmp_path: Path):
    values = args(tmp_path)
    values.output.write_text("already exists")
    with pytest.raises(FileExistsError):
        run(values, caller=FakeCaller())
