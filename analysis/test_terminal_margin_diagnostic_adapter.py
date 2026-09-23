import hashlib
import json
from pathlib import Path

import pytest

from recompute_terminal_margin_diagnostic import build_result, method_input_from_export


ROOT = Path(__file__).resolve().parents[1]
EXPORT = (
    ROOT
    / "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin/evidence.json"
)
MASKED_EXPORT = (
    ROOT
    / "data/robot_visible/dev/diagnostic-pilot-v1/roboboat-terminal-margin-masked-speed/evidence.json"
)


def method_input(export_path: Path, config_path: Path) -> dict:
    export = json.loads(export_path.read_text(encoding="utf-8"))
    source = dict(export["source"])
    source["config_sha256"] = hashlib.sha256(config_path.read_bytes()).hexdigest()
    return {
        "schema": "crane-terminal-margin-method-input-v1",
        "visibility": "robot_visible",
        "episode_id": export["episode_id"],
        "evidence_boundary": export["evidence_boundary"],
        "source": source,
        "observation": export["observation"],
    }


def test_recomputes_supported_diagnosis_without_derived_answer_fields(tmp_path):
    config = tmp_path / "nav2.yaml"
    config.write_text("xy_goal_tolerance: 0.4\ntrans_stopped_velocity: 0.05\n")

    result = build_result(method_input(EXPORT, config), config)

    assert result["diagnostic_result"]["disposition"] == "supported"
    assert "only 0.026 m of task margin" in result["checked_answer"]
    assert result["final_text_verification"]["accepted"] is True


def test_masked_speed_fails_closed(tmp_path):
    config = tmp_path / "nav2.yaml"
    config.write_text("xy_goal_tolerance: 0.4\ntrans_stopped_velocity: 0.05\n")

    result = build_result(method_input(MASKED_EXPORT, config), config)

    assert result["diagnostic_result"]["disposition"] == "insufficient"
    assert "independently measured speed" in result["checked_answer"]


def test_rejects_configuration_hash_mismatch(tmp_path):
    config = tmp_path / "nav2.yaml"
    config.write_text("xy_goal_tolerance: 0.4\ntrans_stopped_velocity: 0.05\n")
    payload = method_input(EXPORT, config)
    payload["source"]["config_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="configuration hash mismatch"):
        build_result(payload, config)


def test_rejects_derived_answer_leakage(tmp_path):
    config = tmp_path / "nav2.yaml"
    config.write_text("xy_goal_tolerance: 0.4\ntrans_stopped_velocity: 0.05\n")
    payload = method_input(EXPORT, config)
    payload["diagnostic_result"] = {"disposition": "supported"}

    with pytest.raises(ValueError, match="derived answer fields"):
        build_result(payload, config)


def test_export_conversion_strips_derived_fields():
    export = json.loads(EXPORT.read_text(encoding="utf-8"))

    payload = method_input_from_export(export)

    assert payload["schema"] == "crane-terminal-margin-method-input-v1"
    assert "diagnostic_result" not in payload
    assert "checked_answer" not in payload
    assert "final_text_verification" not in payload
