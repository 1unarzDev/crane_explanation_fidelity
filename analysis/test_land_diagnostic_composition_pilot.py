import argparse
import json
from pathlib import Path

from run_land_diagnostic_composition_pilot import (
    no_computation_presentation,
    run,
    verify_realization,
)


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data/robot_visible/dev/diagnostic-land-composition-dev-009"
COMMAND = RUN / "command-motion-diagnostic-v3.json"
GEOMETRY = RUN / "geometric-route-diagnostic-v2.json"
COMPOSITION = RUN / "diagnostic-composition-v1.json"
FIXTURE = RUN / "fixture-summary.json"


class FakeCaller:
    def __init__(self, p_answer: str):
        self.p_answer = p_answer
        self.calls = []

    def call(self, call_id, prompt, schema, **kwargs):
        self.calls.append((call_id, prompt, kwargs))
        answer = self.p_answer if call_id.endswith("P-realization") else (
            "Diagnosis: bounded.\nDecisive evidence: retained.\n"
            "Failure chain: retained.\nLimits and next check: unresolved."
        )
        return {
            "cache_key": call_id,
            "latency_ms": 1,
            "cost_usd": 0.0,
            "parsed_final": {"answer": answer},
            "usage": {},
        }


def args(tmp_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        fixture=FIXTURE,
        command=COMMAND,
        geometry=GEOMETRY,
        composition=COMPOSITION,
        repository=ROOT / "packages/crane_ml",
        repository_url="https://github.com/1unarzDev/crane_ml.git",
        repository_commit="3ebba7be193c29c5bec725af7bdcd39157738266",
        core_repository=ROOT / "packages/astro_dock/src/crane_explain",
        core_repository_commit="706985f6ed1ef4815c859b82fe486b2c1cfb7d08",
        repository_prompt="diagnostic_repository_agent_composition_dev_v1.txt",
        realization_prompt="diagnostic_composition_realization_dev_v1.txt",
        question=("What is the deepest supported explanation for the robot's behavior during "
                  "the retained observation window?"),
        question_id="diagnostic-bounded-composition-v1",
        question_kind="diagnostic-composition-and-causal-restraint-v1",
        provider="codex",
        model="test-model",
        reasoning_effort="high",
        cache=tmp_path / "cache",
        output=tmp_path / "output.json",
    )


def test_no_computation_presentation_omits_checked_diagnostics():
    command = json.loads(COMMAND.read_text(encoding="utf-8"))
    geometry = json.loads(GEOMETRY.read_text(encoding="utf-8"))
    presentation = no_computation_presentation(command, geometry)
    serialized = json.dumps(presentation)
    assert "diagnostic_result" not in serialized
    assert presentation["delivered_streams"]["time_aligned_command_motion_computation"] is None
    assert presentation["route_delivery"]["route_classification"] is None
    assert presentation["action"]["terminal_result_observed"] is False


def test_runner_gives_r_both_tools_and_accepts_exact_composition(tmp_path: Path):
    composition = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    caller = FakeCaller(composition["final_answer"])
    result = run(args(tmp_path), caller=caller)

    assert result["information_parity"]["accepted"]
    assert [item["condition"] for item in result["outputs"]] == ["N", "P", "R", "T"]
    p = next(item for item in result["outputs"] if item["condition"] == "P")
    assert p["verification_accepted"]
    assert not p["used_template_fallback"]
    assert [item[0] for item in caller.calls] == [
        "land-diagnostic-composition-R",
        "land-diagnostic-composition-P-realization",
        "land-diagnostic-composition-N",
    ]
    r_prompt = caller.calls[0][1]
    assert "recompute_command_motion_diagnostic.py" in r_prompt
    assert "export_geometric_route_diagnostic.py" in r_prompt
    assert "--allow-active-at-declared-cutoff" in r_prompt


def test_realization_verifier_rejects_terminal_overclaim():
    composition = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    text = composition["final_answer"].replace(
        "no terminal result was observed", "the action failed"
    )
    result = verify_realization(text)
    assert not result["accepted"]
    assert "the action failed" in result["forbidden_findings"]
    assert not result["required_checks"]["nonterminal"]


def test_runner_falls_back_once_when_candidate_omits_required_limit(tmp_path: Path):
    composition = json.loads(COMPOSITION.read_text(encoding="utf-8"))
    candidate = composition["final_answer"].replace(
        "Geometric evidence is insufficient", "Geometry is discussed"
    )
    result = run(args(tmp_path), caller=FakeCaller(candidate))
    p = next(item for item in result["outputs"] if item["condition"] == "P")
    t = next(item for item in result["outputs"] if item["condition"] == "T")
    assert not p["verification_accepted"]
    assert p["used_template_fallback"]
    assert p["text"] == t["text"]
