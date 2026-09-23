import argparse
import hashlib
import json
from pathlib import Path

from run_diagnostic_recovery_pilot import no_diagnostic_presentation, run


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/evidence.json"
DIAGNOSTIC = EVIDENCE.parent / "recovery-execution-diagnostic.json"


class FakeCaller:
    def __init__(self, template: str):
        self.template = template
        self.calls = []

    def call(self, label, prompt, schema, **kwargs):
        self.calls.append((label, prompt, kwargs))
        answer = self.template if "P-realization" in label else f"{label} answer"
        return {
            "cache_key": hashlib.sha256(label.encode()).hexdigest(),
            "latency_ms": 1,
            "parsed_final": {"answer": answer},
            "usage": {},
        }


def test_no_computation_presentation_excludes_derived_transition_linkage():
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    presentation = no_diagnostic_presentation(evidence)

    assert presentation["visibility"] == "robot_visible"
    assert presentation["behavior_tree"]["computed_planner_failure_to_recovery_linkage"] is None
    assert "transitionSequence" not in presentation["behavior_tree"]
    assert "diagnostic_result" not in presentation


def test_runner_preserves_tool_parity_and_one_call_per_model_arm(tmp_path):
    diagnostic = json.loads(DIAGNOSTIC.read_text(encoding="utf-8"))
    caller = FakeCaller(diagnostic["final_answer"])
    args = argparse.Namespace(
        evidence=EVIDENCE,
        diagnostic=DIAGNOSTIC,
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit="c46de4d7e83a18ebef3abc4c97eff1b706a79282",
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="af25ee59fae69dfb5aec3093f9f88e95050480f0",
        repository_prompt="diagnostic_repository_agent_recovery_dev_v1.txt",
        provider="codex",
        model="fake-model",
        reasoning_effort="low",
        cache=tmp_path / "cache",
        output=tmp_path / "result.json",
    )

    result = run(args, caller=caller)

    assert [item[0] for item in caller.calls] == [
        "diagnostic-recovery-R",
        "diagnostic-recovery-P-realization",
        "diagnostic-recovery-N",
    ]
    assert result["single_sample_no_retry"] is True
    assert result["information_parity"]["accepted"] is True
    assert {item["condition"] for item in result["outputs"]} == {"R", "P", "T", "N"}
    p_output = next(item for item in result["outputs"] if item["condition"] == "P")
    assert p_output["used_template_fallback"] is False
