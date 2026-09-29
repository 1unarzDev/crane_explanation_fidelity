import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from evidence_calibration_io import canonical_json_bytes  # noqa: E402
from normalize_command_motion_evidence import normalize  # noqa: E402


DIAGNOSTIC = json.loads((ROOT / "data/robot_visible/dev/cm-land-conf-042/command-motion-diagnostic-v3.json").read_text())


def test_normalizer_uses_method_input_not_old_answer_or_diagnosis():
    first = normalize(DIAGNOSTIC, configuration_id="cluster-042", question="What is supported?")
    second = normalize(DIAGNOSTIC, configuration_id="cluster-042", question="What is supported?")
    serialized = canonical_json_bytes(first)
    assert serialized == canonical_json_bytes(second)
    assert b"final_answer" not in serialized and b"diagnostic_result" not in serialized
    assert set(first["evidence"]) == {"navigate_to_pose_result", "behavior_tree_transitions",
                                      "source_anchors", "delivered_command_stream",
                                      "delivered_odometry_stream", "command_motion_computation"}
    assert len(first["evidence"]["delivered_command_stream"]["samples"]) > 0
    assert len(first["evidence"]["delivered_odometry_stream"]["samples"]) > 0


def test_missing_evidence_source_removes_odometry_without_rewriting_other_roles():
    full = normalize(DIAGNOSTIC, configuration_id="cluster-042", question="What is supported?")
    masked = normalize(DIAGNOSTIC, configuration_id="cluster-042", question="What is supported?", omit_odometry=True)
    assert "delivered_odometry_stream" not in masked["evidence"]
    assert "command_motion_computation" not in masked["evidence"]
    for role in ("navigate_to_pose_result", "behavior_tree_transitions", "source_anchors",
                 "delivered_command_stream"):
        assert masked["evidence"][role] == full["evidence"][role]
