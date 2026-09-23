import copy
import json
from pathlib import Path

import pytest

from export_recovery_execution_diagnostic import build_export


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = (
    ROOT
    / "data/robot_visible/dev/ecological-pilot-v1/eco-pilot-001/evidence.json"
)


def write_evidence(tmp_path: Path, payload: dict) -> Path:
    path = tmp_path / "evidence.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_actual_warehouse_episode_reconstructs_four_bounded_invocations():
    export = build_export(EVIDENCE, "governed:eco-pilot-001/evidence.json")

    result = export["diagnostic_result"]
    assert result["disposition"] == "supported"
    assert "at least 4 source-qualified recovery invocations" in result["diagnosis"]
    assert "Spin->SUCCESS, Wait->SUCCESS, BackUp->SUCCESS, Spin->SUCCESS" in result["diagnosis"]
    assert "eventually succeeded" in result["failure_chain"]
    assert "lower bound" in result["limits"]
    assert "physical cause" in result["limits"]
    assert export["final_text_verification"]["accepted"] is True


def test_feedback_count_sixteen_does_not_become_invocation_count():
    export = build_export(EVIDENCE, "governed:eco-pilot-001/evidence.json")

    assert export["method_input"]["maximum_nav2_feedback_recovery_count"] == 16
    assert "at least 16" not in export["final_answer"]
    assert "maximum_nav2_feedback_recovery_count=" not in export["final_answer"]


def test_missing_planner_recovery_eligibility_fails_to_insufficient(tmp_path):
    evidence = copy.deepcopy(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    evidence["bt"]["transitionSequence"] = [
        transition
        for transition in evidence["bt"]["transitionSequence"]
        if transition["recordId"] != "bt-transition-002760"
    ]

    export = build_export(
        write_evidence(tmp_path, evidence), "development-mutation:evidence.json"
    )

    assert export["diagnostic_result"]["disposition"] == "insufficient"
    assert "Only 3 of 4" in export["diagnostic_result"]["diagnosis"]


def test_duplicate_invocation_identity_is_rejected(tmp_path):
    evidence = copy.deepcopy(json.loads(EVIDENCE.read_text(encoding="utf-8")))
    evidence["bt"]["recoveryInvocations"][1]["invocationId"] = (
        evidence["bt"]["recoveryInvocations"][0]["invocationId"]
    )

    with pytest.raises(ValueError, match="invocation IDs must be unique"):
        build_export(
            write_evidence(tmp_path, evidence), "development-mutation:evidence.json"
        )
