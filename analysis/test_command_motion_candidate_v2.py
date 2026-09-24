import argparse
import json
from pathlib import Path

import pytest

from run_command_motion_candidate_v2 import run


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-compensated-001/evidence-and-diagnostic.json"


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


def args(tmp_path: Path, evidence: Path = EVIDENCE) -> argparse.Namespace:
    return argparse.Namespace(
        evidence=evidence,
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit="6bf057b5acf1763eeca1b81be6530cd218a5405b",
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="f131b9b042c42e269dcc7c646e93fc6eb5433d49",
        repository_prompt="diagnostic_repository_agent_command_motion_dev_v2.txt",
        provider="codex",
        model="test-model",
        reasoning_effort="high",
        cache=tmp_path / "cache",
        output=tmp_path / "result.json",
    )


def test_candidate_uses_deterministic_p_and_calls_only_stronger_r(tmp_path: Path):
    caller = FakeCaller()
    result = run(args(tmp_path), caller=caller)
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    assert [item["condition"] for item in result["outputs"]] == ["P", "R"]
    assert result["outputs"][0]["text"] == evidence["final_answer"]
    assert result["outputs"][0]["generation_method"] == "deterministic_checked_rendering"
    assert result["outputs"][0]["used_template_fallback"] is False
    assert result["information_parity"]["p_model_calls"] == 0
    assert result["information_parity"]["r_model_calls"] == 1
    assert len(caller.calls) == 1
    assert caller.calls[0][0] == "command-motion-candidate-v2-R"
    assert "calibrated healthy response is a comparator" in caller.calls[0][1]


def test_candidate_rejects_nonexact_or_nonrobot_visible_export(tmp_path: Path):
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    payload["final_text_verification"]["policy"] = "post-hoc-policy"
    bad = ROOT / "data/robot_visible/dev" / "candidate-v2-invalid-test.json"
    bad.write_text(json.dumps(payload), encoding="utf-8")
    try:
        with pytest.raises(ValueError, match="exact checked deterministic"):
            run(args(tmp_path, bad), caller=FakeCaller())
    finally:
        bad.unlink()
