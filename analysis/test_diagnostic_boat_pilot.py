import argparse
import hashlib
import json
from pathlib import Path

from run_diagnostic_boat_pilot import method_input, run


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json"
)


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


def test_method_input_excludes_derived_diagnosis():
    export = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    payload = method_input(export)

    assert payload["visibility"] == "robot_visible"
    assert "diagnostic_result" not in payload
    assert "checked_answer" not in payload
    assert "final_text_verification" not in payload


def test_runner_preserves_tool_parity_and_one_call_per_model_arm(tmp_path):
    export = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    output = tmp_path / "result.json"
    caller = FakeCaller(export["checked_answer"])
    args = argparse.Namespace(
        evidence=EVIDENCE,
        variant="unmasked",
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit=export["source"]["config_commit"],
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="38ae31ca4b6143a23e1b5fe3ff0f7d443ac4a70f",
        repository_prompt="diagnostic_repository_agent_boat_dev_v1.txt",
        provider="codex",
        model="fake-model",
        reasoning_effort="low",
        cache=tmp_path / "cache",
        output=output,
    )

    result = run(args, caller=caller)

    assert [call[0] for call in caller.calls] == [
        "diagnostic-boat-R",
        "diagnostic-boat-P-realization",
        "diagnostic-boat-N",
    ]
    assert result["single_sample_no_retry"] is True
    assert result["information_parity"]["accepted"] is True
    assert {item["condition"] for item in result["outputs"]} == {"R", "P", "T", "N"}
    assert result["outputs"][1]["condition"] == "P"
    assert result["outputs"][1]["used_template_fallback"] is False
