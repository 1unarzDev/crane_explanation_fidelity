from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from compose_contract_complete_answer_v5 import WORD_BUDGET, compile_answer


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "research/explanation_fidelity/experiment_configs/prospective/contract-complete-diagnostic-communication-v1-questions.json").read_text())


@pytest.mark.parametrize(
    ("run_id", "family"),
    [
        ("cr-pilot-002", "persistent_command_motion_discrepancy"),
        ("cr-pilot-003", "measured_response_recovery"),
        ("cr-pilot-006", "nominal_false_premise_or_irrelevant_obstacle"),
        ("cr-pilot-010", "missing_decisive_or_ambiguous_evidence"),
    ],
)
def test_concise_candidate_preserves_exact_contract_under_120_words(run_id: str, family: str):
    path = ROOT / "data/robot_visible/dev" / run_id / "command-motion-diagnostic-v3.json"
    raw = path.read_bytes()
    result = compile_answer(
        json.loads(raw), family=family, source_sha256=hashlib.sha256(raw).hexdigest(),
        question_registry=REGISTRY,
    )
    assert result["candidate_version"] == "p-contract-v5-concise-development"
    assert [item["component"] for item in result["components"]] == ["M", "Q", "O", "L"]
    assert result["support_check"]["passed"] is True
    assert result["completeness_check"]["passed"] is True
    assert result["communication_budget"]["passed"] is True
    assert len(result["final_answer"].split()) <= WORD_BUDGET
    assert result["final_answer"].splitlines()[0].startswith("M —")


def test_concise_recovery_keeps_all_three_comparisons_and_both_limits():
    path = ROOT / "data/robot_visible/dev/cr-pilot-003/command-motion-diagnostic-v3.json"
    raw = path.read_bytes()
    result = compile_answer(
        json.loads(raw), family="measured_response_recovery",
        source_sha256=hashlib.sha256(raw).hexdigest(), question_registry=REGISTRY,
    )
    text = result["final_answer"]
    assert "Healthy 0--5 s" in text
    assert "Event 11--21 s" in text
    assert "Recovery 23--24 s" in text
    assert "Wait caused recovery" in text
    assert "recovery caused the eventual outcome" in text
    assert "remains unresolved" in text


def test_concise_prompt_gives_r_the_same_budget_and_full_contract():
    prompt = (ROOT / "research/explanation_fidelity/prompts/diagnostic_repository_agent_contract_complete_concise_v1.txt").read_text()
    normalized = " ".join(prompt.split())
    assert "at most 120 whitespace-delimited words" in normalized
    assert "not permission to omit question-essential content" in normalized
    assert "mechanism, decisive measurement/comparison" in normalized
    assert "Scripts and templates are permitted" in normalized
