import copy
import json
from pathlib import Path

import pytest

from build_command_motion_missing_reference_v2 import build_reference


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "data/robot_visible/dev/cmv2-dev-001-mask-no-odometry/command-motion-diagnostic-v3.json"
INDEPENDENT = ROOT / "data/evaluator_only/dev/cmv2-dev-001-mask-no-odometry/command-motion-missing-odometry-reference-v1.json"


def inputs():
    export = json.loads(EXPORT.read_text())
    independent = json.loads(INDEPENDENT.read_text())
    independent["observations"]["follow_path_attempt_count"] = 3
    return export, independent


def test_builds_complete_fail_closed_mask_reference():
    export, independent = inputs()
    result = build_reference(export, independent, question_id="command-motion-candidate-v2-mechanism")
    assert result["diagnosable"] is False
    assert result["completeness_audit"]["accepted"] is True
    assert result["allowed_evidence"]["evidence_mask"]["independent_scenario_increment"] == 0
    assert any(unit["unit_id"] == "cause-limit" for unit in result["required_units"])
    execution = next(unit for unit in result["required_units"] if unit["unit_id"] == "execution-sequence")
    assert "3 FollowPath attempts" in execution["text"]


def test_rejects_reference_count_drift():
    export, independent = inputs()
    changed = copy.deepcopy(independent)
    changed["observations"]["delivered_command_sample_count"] += 1
    with pytest.raises(ValueError, match="commands_retained"):
        build_reference(export, changed, question_id="command-motion-candidate-v2-mechanism")


def test_rejects_missing_attempt_count():
    export, independent = inputs()
    del independent["observations"]["follow_path_attempt_count"]
    with pytest.raises(ValueError, match="follow_path_attempts"):
        build_reference(export, independent, question_id="command-motion-candidate-v2-mechanism")
