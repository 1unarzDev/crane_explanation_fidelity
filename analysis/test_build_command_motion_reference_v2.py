import copy
import json
from pathlib import Path

import pytest

from build_command_motion_reference_v2 import build_reference
from reference_command_motion import calculate


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-compensated-001/evidence-and-diagnostic.json"


def fixture():
    export = json.loads(EXPORT.read_text(encoding="utf-8"))
    export["diagnostic_result"]["computation_version"] = "command-motion-discrepancy-v3"
    return export, calculate(export)


def test_reference_is_complete_without_exposing_candidate_plan():
    export, independent = fixture()
    reference = build_reference(export, independent, question_id="q-v2")
    serialized = json.dumps(reference)

    assert reference["completeness_audit"]["accepted"]
    assert reference["allowed_evidence"]["independent_computation"]["result"][
        "healthy_interval_s"
    ] == [0.0, 5.0]
    assert reference["allowed_evidence"]["independent_computation"][
        "execution_basis"
    ]["recovery_node_classifier"]["node_name"] == "Wait"
    assert "diagnostic_result" not in serialized
    assert "answer_plan" not in serialized
    assert "evaluator" not in serialized.lower()


def test_reference_fails_closed_on_independent_mismatch():
    export, independent = fixture()
    bad = copy.deepcopy(independent)
    bad["result"]["interval_s"] = [8.0, 19.0]
    with pytest.raises(ValueError, match="discrepancy_interval"):
        build_reference(export, bad, question_id="q-v2")

    bad = copy.deepcopy(independent)
    bad["robot_visible_provenance"]["odometry"] = "stronger-than-evidence"
    with pytest.raises(ValueError, match="odometry_provenance"):
        build_reference(export, bad, question_id="q-v2")
