from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

import run_contract_complete_response_pair as base  # noqa: E402


PROMPT = ROOT / (
    "research/explanation_fidelity/prompts/"
    "diagnostic_repository_agent_causal_restraint_v1.txt"
)


def test_successor_prompt_states_the_same_explicit_causal_contract() -> None:
    text = " ".join(PROMPT.read_text(encoding="utf-8").split())
    for required in (
        "Wait causing or restoring measured recovery",
        "Wait yielding task success or failure",
        "measured recovery causing the eventual task outcome",
        "command--motion discrepancy causing the terminal outcome",
        "named physical source causing the discrepancy or outcome",
        "Do not assert a positive or negative causal/effectiveness conclusion",
        "Chronology may be reported as chronology",
    ):
        assert required in text


def test_base_runner_retains_development_defaults_and_accepts_stage(monkeypatch):
    monkeypatch.setattr(
        "sys.argv",
        [
            "runner",
            "--evidence", "evidence.json",
            "--cluster-id", "cluster",
            "--family", "persistent_command_motion_discrepancy",
            "--cache", "cache",
            "--output", "output.json",
            "--study-stage", "pilot",
        ],
    )
    args = base.parse_args()
    assert args.study_stage == "pilot"
    assert base.PAIR_STATUS == "DEVELOPMENT_ONLY_NOT_CONFIRMATORY"
    assert base.BASELINE_ID == "r-contract-v1-development"
