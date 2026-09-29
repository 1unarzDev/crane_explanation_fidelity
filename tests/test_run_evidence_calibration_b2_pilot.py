import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from run_evidence_calibration_b2_pilot import run  # noqa: E402


class FakeCaller:
    def __init__(self):
        self.calls = 0

    def call(self, role, prompt, schema, *, working_directory, workspace_identity):
        self.calls += 1
        evidence = json.loads((working_directory / "robot_visible/evidence.json").read_text())
        assert "evaluator" not in json.dumps(evidence).lower()
        assert (working_directory / "tools/inspect_evidence_calibration_packet.py").is_file()
        assert schema["required"] == ["answer"]
        return {"cache_key": "fake-key", "parsed_final": {"answer": "The action result is the strongest available evidence."}}


def args(tmp_path):
    return argparse.Namespace(
        condition_id="cm-land-conf-042-E0",
        pilot=ROOT / "research/explanation_fidelity/experiment_configs/development/evidence-calibration-b2-b4-pilot-v1.json",
        schedule=ROOT / "research/explanation_fidelity/experiment_configs/prospective/land-command-motion-physical-schedule-v1.json",
        validation=ROOT / "manifests/study/evidence-calibration-b2-b4-pilot-v1-input-validation.json",
        cache=tmp_path / "cache", output_root=tmp_path / "outputs", timeout_seconds=300.0,
    )


def test_runner_is_isolated_hash_bound_and_resume_safe(tmp_path):
    caller = FakeCaller()
    first = run(args(tmp_path), caller)
    second = run(args(tmp_path), caller)
    assert caller.calls == 1
    assert first == second
    assert first["condition_id"] == "cm-land-conf-042-E0"
    assert first["single_call_no_retry"]
    assert first["development_only"]
