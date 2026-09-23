import json
from pathlib import Path

from mask_command_motion_evidence import MASK_ID, build_masked_export
from recompute_command_motion_diagnostic import build_result, method_input_from_export


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/robot_visible/dev/diagnostic-pilot-v1/land-command-motion-001/evidence-and-diagnostic.json"
MASKED_ID = "diagnostic-motion-dev-cm-001-mask-no-odometry"


def test_mask_withholds_only_motion_samples_and_fails_closed():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    masked = build_masked_export(source, MASKED_ID)

    assert masked["episode_id"] == MASKED_ID
    assert masked["method_input"]["odometry_samples"] == []
    assert masked["method_input"]["command_samples"] == source["method_input"]["command_samples"]
    assert masked["method_input"]["execution_sequence"] == source["method_input"]["execution_sequence"]
    assert masked["source"] == source["source"]
    assert masked["evidence_mask"] == {
        "mask_id": MASK_ID,
        "withheld": ["independently delivered odometry samples"],
        "paired_source_available_to_methods": False,
        "independent_scenario_increment": 0,
    }
    assert masked["diagnostic_result"]["disposition"] == "insufficient"
    measurements = {
        item["id"]: item["value"] for item in masked["diagnostic_result"]["measurements"]
    }
    assert measurements["delivered_command_sample_count"] == 376
    assert measurements["independent_odometry_sample_count"] == 0
    assert measurements["action_status"] == "aborted"
    assert "odometry stream is missing" in masked["diagnostic_result"]["diagnosis"]
    assert "Decisive evidence: ." not in masked["final_answer"]
    assert masked["final_text_verification"]["accepted"]
    assert source["diagnostic_result"] != masked["diagnostic_result"]


def test_masked_method_projection_recomputes_exact_checked_result():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    masked = build_masked_export(source, MASKED_ID)
    method = method_input_from_export(masked)
    recomputed = build_result(method)

    assert not {"diagnostic_result", "final_answer", "evidence_mask"}.intersection(method)
    assert recomputed["diagnostic_result"] == masked["diagnostic_result"]
    assert recomputed["final_answer"] == masked["final_answer"]


def test_mask_is_deterministic_and_does_not_name_source_episode():
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    first = build_masked_export(source, MASKED_ID)
    second = build_masked_export(source, MASKED_ID)

    assert first == second
    serialized = json.dumps(first, sort_keys=True)
    assert "land-command-motion-001" not in serialized
    assert "mobility hold" not in serialized.lower()
