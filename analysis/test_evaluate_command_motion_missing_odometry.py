import copy
import json
from pathlib import Path

import pytest

from evaluate_command_motion_missing_odometry import build_reference
from mask_command_motion_evidence import build_masked_export


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json"
MASKED_ID = "diagnostic-motion-dev-cm-001-mask-no-odometry"


def masked():
    return build_masked_export(json.loads(SOURCE.read_text()), MASKED_ID)


def test_reference_uses_only_masked_method_observations():
    payload = masked()
    reference = build_reference(payload, SOURCE)

    assert reference["independent_of_proposed_diagnostic_result"]
    assert reference["observations"] == {
        "delivered_command_sample_count": 376,
        "independent_odometry_sample_count": 0,
        "action_status": "aborted",
        "follow_path_failure_count": 2,
        "source_qualified_wait_recovery_count": 2,
    }
    assert reference["answerability"]["command_motion_discrepancy"] == "insufficient"
    assert reference["independent_scenario_increment"] == 0


def test_reference_is_invariant_to_proposed_result_text():
    payload = masked()
    changed = copy.deepcopy(payload)
    changed["diagnostic_result"] = {"invented": "ignored"}
    changed["final_answer"] = "invented"

    assert build_reference(payload, SOURCE) == build_reference(changed, SOURCE)


def test_reference_rejects_unmasked_odometry():
    payload = masked()
    payload["method_input"]["odometry_samples"] = [{"offset_s": 0.0}]

    with pytest.raises(ValueError, match="motion to be absent"):
        build_reference(payload, SOURCE)
