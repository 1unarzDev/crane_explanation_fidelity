from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))

from compose_contract_complete_answer import compile_answer  # noqa: E402
from run_contract_complete_response_pair import (  # noqa: E402
    BASELINE,
    PRODUCTION_TOOLS,
    resolve_question,
)


CONTRACT = json.loads(
    (
        ROOT
        / "research/explanation_fidelity/experiment_configs/prospective/"
        "contract-complete-diagnostic-communication-v1-questions.json"
    ).read_text(encoding="utf-8")
)


def answer(relative: str, family: str) -> dict:
    raw = (ROOT / relative).read_bytes()
    return compile_answer(
        json.loads(raw),
        family=family,
        source_sha256=hashlib.sha256(raw).hexdigest(),
        question_registry=CONTRACT,
    )


def test_persistent_answer_is_contract_complete_at_the_final_text_seam() -> None:
    result = answer(
        "data/robot_visible/dev/cmv3-dev-001/command-motion-diagnostic-v3.json",
        "persistent_command_motion_discrepancy",
    )

    assert result["support_check"]["passed"] is True
    assert result["completeness_check"] == {
        "required_components": ["M", "Q", "O", "L"],
        "present_components": ["M", "Q", "O", "L"],
        "passed": True,
    }
    assert [item["component"] for item in result["components"]] == ["M", "Q", "O", "L"]
    text = result["final_answer"]
    assert "healthy 0--5 s interval" in text
    assert "commanded median was 0.26 m/s" in text
    assert "measured median was 0.25974 m/s" in text
    assert "event 10--20 s interval" in text
    assert "commanded median was 0.26 m/s" in text
    assert "measured median was 0 m/s" in text
    assert "recorded navigation action aborted" in text
    assert "does not uniquely identify" in text


def test_recovery_followed_by_abort_preserves_both_causal_limits() -> None:
    result = answer(
        "data/robot_visible/dev/cm-land-conf-047/command-motion-diagnostic-v3.json",
        "measured_response_recovery",
    )
    text = result["final_answer"]
    lower = text.lower()

    assert result["completeness_check"]["passed"] is True
    assert result["candidate_version"] == "p-contract-v2-development"
    assert "measured response recovered" in lower
    assert "recovery interval" in lower
    assert "commanded median was 0.25 m/s" in lower
    assert "measured median was 0.24975 m/s" in lower
    assert "after that measured response recovery, the recorded navigation action aborted" in lower
    assert "does not establish that a wait invocation caused the measured response recovery" in lower
    assert "does not establish that the measured response recovery caused the eventual action outcome" in lower
    assert "original physical or actuator cause remains unresolved" in lower
    assert "recovery caused success" not in lower


def test_geometry_reports_observed_cost_and_threshold_without_outcome_causation() -> None:
    result = answer(
        "data/robot_visible/dev/mccv2-dev-001/geometric-route-diagnostic-v2.json",
        "bounded_geometric_restriction",
    )
    text = result["final_answer"]
    lower = text.lower()

    assert result["completeness_check"]["passed"] is True
    assert "observed cell cost was 253" in lower
    assert "non-traversable threshold of 253" in lower
    assert "recorded navigation action succeeded" in lower
    assert "retained geometry caused the outcome" in lower
    assert "does not establish" in lower


def test_geometry_fails_closed_when_cost_classification_is_inconsistent() -> None:
    path = ROOT / "data/robot_visible/dev/mccv2-dev-001/geometric-route-diagnostic-v2.json"
    raw = path.read_bytes()
    document = json.loads(raw)
    document["reference_computation"]["direct_route"]["first_lethal_sample_from_start"]["cost"] = 252

    with pytest.raises(ValueError, match="below the non-traversable threshold"):
        compile_answer(
            document,
            family="bounded_geometric_restriction",
            source_sha256=hashlib.sha256(raw).hexdigest(),
            question_registry=CONTRACT,
        )


def test_wait_without_recovery_does_not_invent_recovery() -> None:
    result = answer(
        "data/robot_visible/dev/cmv3-dev-001/command-motion-diagnostic-v3.json",
        "persistent_command_motion_discrepancy",
    )
    assert "wait invocation caused" not in result["final_answer"].lower()
    assert "response recovery" not in result["final_answer"].lower()


def test_task_success_without_recovery_rejects_failure_premise() -> None:
    result = answer(
        "data/robot_visible/dev/cmv3-dev-003/command-motion-diagnostic-v3.json",
        "nominal_false_premise_or_irrelevant_obstacle",
    )
    lower = result["final_answer"].lower()
    assert "does not support the alleged command-to-motion failure premise" in lower
    assert "recorded navigation action succeeded" in lower
    assert "0.26 m/s" in lower
    assert "0.25974 m/s" in lower


def test_missing_motion_evidence_is_qualified_instead_of_mapped_as_failure() -> None:
    result = answer(
        "data/robot_visible/dev/cmv3-dev-001-mask-no-odometry/command-motion-diagnostic-v3.json",
        "missing_decisive_or_ambiguous_evidence",
    )
    lower = result["final_answer"].lower()
    assert result["completeness_check"]["passed"] is True
    assert "cannot be established" in lower
    assert "0 independent odometry samples" in lower
    assert "measured motion is the decisive missing discriminator" in lower


def test_above_threshold_geometry_remains_bounded_and_supported() -> None:
    path = ROOT / "data/robot_visible/dev/mccv2-dev-001/geometric-route-diagnostic-v2.json"
    raw = path.read_bytes()
    document = json.loads(raw)
    document["reference_computation"]["direct_route"]["first_lethal_sample_from_start"]["cost"] = 254
    result = compile_answer(
        document,
        family="bounded_geometric_restriction",
        source_sha256=hashlib.sha256(raw).hexdigest(),
        question_registry=CONTRACT,
    )
    lower = result["final_answer"].lower()
    assert "observed cell cost was 254" in lower
    assert "non-traversable threshold of 253" in lower
    assert "global physical no-path" in lower


def test_public_question_contract_contains_no_episode_gold() -> None:
    encoded = json.dumps(CONTRACT, sort_keys=True).lower()
    assert "expected_answer" not in encoded
    assert "gold_unit" not in encoded
    assert "evaluator" not in encoded
    assert "cm-land-conf" not in encoded
    for item in CONTRACT["questions"]:
        assert item["required_components"] == ["M", "Q", "O", "L"]


def test_r_contract_receives_the_same_four_component_task() -> None:
    prompt = (
        ROOT
        / "research/explanation_fidelity/prompts/diagnostic_repository_agent_contract_complete_v1.txt"
    ).read_text(encoding="utf-8")
    required = (
        "State the supported mechanism, the decisive measurement/comparison, the recorded outcome, "
        "and the necessary causal/evidence limitation. Include the question-essential details. "
        "Additional detail is optional."
    )
    assert required in " ".join(prompt.split())
    assert "governed evidence identifiers" in prompt
    assert "evaluator" not in prompt.lower()
    assert "proposed method's" not in prompt.lower()


def test_r_contract_uses_production_tools_without_reference_gold() -> None:
    assert BASELINE == {"model": "gpt-6-sol", "reasoning_effort": "high", "top_level_calls": 1}
    assert set(PRODUCTION_TOOLS) == {"recompute_command_motion", "command_motion_config"}
    assert all("reference" not in str(path) for path in PRODUCTION_TOOLS.values())
    question = resolve_question(CONTRACT, "measured_response_recovery")
    assert "Wait-to-recovery" in question
    assert "original-cause attribution" in question
