import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MASK = _load("mask_v2", "analysis/mask_command_motion_evidence_v2.py")
REFERENCE = _load(
    "reference_v2", "analysis/reference_command_motion_missing_odometry_v2.py"
)


def _source():
    path = (
        ROOT
        / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/"
        / "evidence-and-diagnostic.json"
    )
    source = json.loads(path.read_text(encoding="utf-8"))
    source["method_input"]["action_status"] = "succeeded"
    source["method_input"]["action_error_code"] = 0
    sequence = source["method_input"]["execution_sequence"]
    sequence["follow_path_attempt_count"] = 2
    sequence["follow_path_failure_count"] = 1
    sequence["source_qualified_wait_recovery_count"] = 1
    return source


def test_mask_is_the_sole_packet_for_one_independent_cluster(tmp_path):
    masked = MASK.build_masked_export(_source(), "ambiguous-cluster-001")
    assert masked["method_input"]["odometry_samples"] == []
    assert masked["diagnostic_result"]["disposition"] == "insufficient"
    assert masked["evidence_mask"]["mask_id"] == "remove-delivered-odometry-v1"
    assert masked["evidence_mask"]["independent_scenario_increment"] == 1
    assert masked["evidence_mask"]["paired_unmasked_export_available_to_methods"] is False

    source = tmp_path / "masked.json"
    source.write_text("{}", encoding="utf-8")
    reference = REFERENCE.build_reference(masked, source)
    assert reference["statistical_cluster_id"] == "ambiguous-cluster-001"
    assert reference["independent_scenario_increment"] == 1
    assert reference["observations"]["action_status"] == "succeeded"
    assert "2 FollowPath attempts, 1 failures, and 1" in reference["required_propositions"][1]


def test_reference_rejects_old_paired_mask(tmp_path):
    masked = MASK.build_masked_export(_source(), "ambiguous-cluster-001")
    old = copy.deepcopy(masked)
    old["evidence_mask"]["independent_scenario_increment"] = 0
    source = tmp_path / "masked.json"
    source.write_text("{}", encoding="utf-8")
    try:
        REFERENCE.build_reference(old, source)
    except ValueError as error:
        assert "independently configured" in str(error)
    else:
        raise AssertionError("old paired-mask semantics were accepted")
