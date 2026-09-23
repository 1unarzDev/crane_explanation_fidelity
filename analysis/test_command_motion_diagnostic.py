import json
from pathlib import Path

import pytest

from export_command_motion_diagnostic import export
from reference_command_motion import calculate


ROOT = Path(__file__).resolve().parents[1]
CAPTURE = (
    ROOT
    / "data"
    / "robot_visible"
    / "dev"
    / "diagnostic-motion-instrumentation-held-001"
    / "capture"
)
EVENTS = CAPTURE / "events.jsonl"
CAPTURE_MANIFEST = CAPTURE / "manifest.json"
RUNTIME_MANIFEST = CAPTURE / "runtime_manifest.json"
BT_XML = CAPTURE / "behavior_tree.xml"
NAV2_CONFIG = ROOT / "packages" / "crane_ml" / "Tools" / "Performance" / "nav2_land_fixture.yaml"


def _export() -> dict:
    return export(
        EVENTS,
        CAPTURE_MANIFEST,
        RUNTIME_MANIFEST,
        BT_XML,
        NAV2_CONFIG,
        episode_id="diagnostic-motion-dev-cm-001",
    )


def test_retained_stream_supports_bounded_command_motion_diagnosis():
    payload = _export()

    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["final_text_verification"]["accepted"]
    assert payload["method_input"]["execution_sequence"] == {
        "follow_path_failure_count": 2,
        "follow_path_attempt_count": 3,
        "source_qualified_wait_recovery_count": 2,
        "recovery_node_classifier": {
            "classifier_basis": "retained_bt_recovery_child_exact_node_name",
            "classifier_rule": "Wait:IDLE->RUNNING",
            "node_name": "Wait",
            "number_of_retries": 2,
            "policy_sha256": "14939b78c72149b9c71b3806f2d3af63fc5de48c8bd9d07f0d13b55563f48520",
            "tree_path": "RecoveryNode/recovery_child/Sequence/Wait",
        },
    }
    serialized = json.dumps(payload).lower()
    assert "instrumentation-held" not in serialized
    assert "persistent hold" not in serialized
    assert "mobility hold" not in serialized
    assert "motor failure" not in payload["final_answer"].lower()


def test_independent_reference_recomputes_supported_interval():
    payload = _export()
    reference = calculate(payload)
    measurements = {
        item["id"]: item["value"] for item in payload["diagnostic_result"]["measurements"]
    }

    assert reference["implementation_independence"]["imports_proposed_diagnostic_core"] is False
    assert reference["result"]["disposition"] == "supported"
    assert reference["result"]["interval_s"] == [7.0, 17.0]
    assert reference["result"]["healthy_measured_planar_speed_mps"] == pytest.approx(
        measurements["calibrated_healthy_planar_speed"]
    )
    assert reference["result"]["discrepancy_commanded_planar_speed_mps"] == pytest.approx(
        measurements["discrepancy_commanded_planar_speed"]
    )
    assert reference["result"]["discrepancy_measured_planar_speed_mps"] == pytest.approx(
        measurements["discrepancy_measured_planar_speed"]
    )


def test_runtime_source_hash_mismatch_is_rejected(tmp_path: Path):
    changed = tmp_path / "changed-nav2.yaml"
    changed.write_text(NAV2_CONFIG.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Nav2 configuration hash"):
        export(
            EVENTS,
            CAPTURE_MANIFEST,
            RUNTIME_MANIFEST,
            BT_XML,
            changed,
            episode_id="diagnostic-motion-dev-cm-001",
        )


def test_evaluator_only_input_path_is_rejected():
    evaluator_path = (
        ROOT
        / "data"
        / "evaluator_only"
        / "dev"
        / "diagnostic-motion-instrumentation-held-001"
        / "fixture-summary.json"
    )
    with pytest.raises(ValueError, match="robot_visible"):
        export(
            evaluator_path,
            CAPTURE_MANIFEST,
            RUNTIME_MANIFEST,
            BT_XML,
            NAV2_CONFIG,
            episode_id="diagnostic-motion-dev-cm-001",
        )
