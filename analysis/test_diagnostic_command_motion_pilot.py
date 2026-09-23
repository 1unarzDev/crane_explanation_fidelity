import argparse
import json
from pathlib import Path

from run_diagnostic_command_motion_pilot import no_computation_presentation, run


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json"


class FakeCaller:
    def __init__(self, p_answer: str):
        self.p_answer = p_answer
        self.calls = []

    def call(self, call_id, prompt, schema, **kwargs):
        self.calls.append((call_id, prompt, kwargs))
        answer = self.p_answer if call_id.endswith("P-realization") else "Diagnosis: bounded\nDecisive evidence: retained.\nFailure chain: retained.\nLimits and next check: unresolved."
        return {
            "cache_key": call_id,
            "latency_ms": 1,
            "cost_usd": 0.0,
            "parsed_final": {"answer": answer},
            "usage": {},
        }


def test_no_computation_presentation_omits_checked_result():
    export = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    from recompute_command_motion_diagnostic import method_input_from_export

    presentation = no_computation_presentation(method_input_from_export(export))
    serialized = json.dumps(presentation)
    assert "diagnostic_result" not in serialized
    assert "time_aligned_window_computation" in serialized
    assert presentation["delivered_streams"]["command_sample_count"] == 376


def test_runner_preserves_tool_parity_and_accepts_checked_p_candidate(tmp_path: Path):
    export = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    caller = FakeCaller(export["final_answer"])
    output = tmp_path / "pilot.json"
    args = argparse.Namespace(
        evidence=EVIDENCE,
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit="6bf057b5acf1763eeca1b81be6530cd218a5405b",
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="c1aad36f4b50654b3c1aa6d5155ac01474368cfb",
        repository_prompt="diagnostic_repository_agent_command_motion_dev_v1.txt",
        provider="codex",
        model="test-model",
        reasoning_effort="low",
        cache=tmp_path / "cache",
        output=output,
    )
    result = run(args, caller=caller)

    assert result["information_parity"]["accepted"]
    assert [item["condition"] for item in result["outputs"]] == ["N", "P", "R", "T"]
    p = next(item for item in result["outputs"] if item["condition"] == "P")
    assert p["verification_accepted"]
    assert not p["used_template_fallback"]
    assert [item[0] for item in caller.calls] == [
        "diagnostic-command-motion-R",
        "diagnostic-command-motion-P-realization",
        "diagnostic-command-motion-N",
    ]


def test_runner_uses_declared_compensation_question_without_changing_parity(tmp_path: Path):
    export = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    caller = FakeCaller(export["final_answer"])
    question = (
        "What temporarily prevented continued progress, what changed before success, "
        "and what remains unresolved?"
    )
    args = argparse.Namespace(
        evidence=EVIDENCE,
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit="6bf057b5acf1763eeca1b81be6530cd218a5405b",
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="f131b9b042c42e269dcc7c646e93fc6eb5433d49",
        repository_prompt="diagnostic_repository_agent_command_motion_dev_v1.txt",
        provider="codex",
        model="test-model",
        reasoning_effort="low",
        cache=tmp_path / "cache",
        output=tmp_path / "pilot.json",
        question=question,
        question_id="diagnostic-command-motion-compensation-v1",
        question_kind="diagnostic-same-mechanism-different-outcome-v1",
    )

    result = run(args, caller=caller)
    assert result["question"] == question
    assert result["question_id"] == "diagnostic-command-motion-compensation-v1"
    assert result["question_kind"] == "diagnostic-same-mechanism-different-outcome-v1"
    assert all(question in prompt for _, prompt, _ in caller.calls)
    assert result["information_parity"]["accepted"]
