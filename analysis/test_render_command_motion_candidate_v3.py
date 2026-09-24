import json
from pathlib import Path

import pytest

from render_command_motion_candidate_v3 import render


ROOT = Path(__file__).resolve().parents[1]


def load(run_id: str):
    return json.loads(
        (ROOT / f"data/robot_visible/dev/{run_id}/command-motion-diagnostic-v3.json").read_text()
    )


def test_supported_answer_uses_bounded_unordered_execution_facts():
    text = render(load("cmv2-dev-002"))
    assert "11.0--21.0 s" in text
    assert "23.0--24.0 s" in text
    assert "2 FollowPath attempts" in text
    assert "1 FollowPath failures" in text
    assert "do not by themselves establish that the discrepancy caused" in text
    assert "After the response loss" not in text
    assert "recovered before" not in text


def test_not_triggered_answer_preserves_observed_failures_and_recoveries():
    text = render(load("cmv2-dev-003"))
    assert "did not establish a sustained" in text
    assert "3 FollowPath attempts" in text
    assert "2 FollowPath failures" in text
    assert "2 source-qualified Wait invocations" in text
    assert "no observed FollowPath failure" not in text


def test_insufficient_answer_includes_attempt_count_without_diagnosing_discrepancy():
    text = render(load("cmv2-dev-001-mask-no-odometry"))
    assert "cannot be assessed" in text
    assert "407 delivered command samples" in text
    assert "0 delivered odometry samples" in text
    assert "3 FollowPath attempts" in text
    assert "execution sequence alone does not establish" in text


def test_rejects_non_robot_visible_input():
    payload = load("cmv2-dev-001")
    payload["visibility"] = "evaluator_only"
    with pytest.raises(ValueError, match="robot-visible"):
        render(payload)
