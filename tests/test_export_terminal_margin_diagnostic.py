import importlib.util
import json
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "analysis" / "export_terminal_margin_diagnostic.py"
SPEC = importlib.util.spec_from_file_location("export_terminal_margin_diagnostic", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_export_uses_goal_and_odometry_without_evaluator_label(tmp_path):
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=repository, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repository, check=True)
    config = repository / "fixture.yaml"
    config.write_text(
        "goal_checker:\n  xy_goal_tolerance: 0.40\n  trans_stopped_velocity: 0.05\n"
    )
    subprocess.run(["git", "add", "fixture.yaml"], cwd=repository, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=repository, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repository, check=True, text=True, capture_output=True
    ).stdout.strip()

    run = tmp_path / "run-1"
    run.mkdir()
    summary = run / "fixture-summary.json"
    summary.write_text(
        json.dumps(
            {
                "status": "succeeded",
                "provenance": "latest-delivered-odometry-not-proven-internal-consumption",
                "plannedPath": [{"x": 0.0, "y": 0.0, "yaw": 0.0}],
                "actionResultPose": {"x": 0.37, "y": 0.0, "yaw": 0.0},
                "finalPose": {"x": 0.56, "y": 0.0, "yaw": 0.0},
                "motionAtActionResult": {"bodySpeedMetersPerSecond": 0.048},
                "postResultCoastDistanceMeters": 0.19,
                "trajectory": [
                    {"phase": "post_result", "simSeconds": 10.0},
                    {"phase": "post_result", "simSeconds": 18.0},
                ],
                "dockingSuccessObserved": False,
            }
        )
    )

    payload = MODULE.build_export(
        summary,
        repository,
        commit,
        "fixture.yaml",
        0.40,
        "PerformanceResults/run-1/fixture-summary.json",
    )

    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["final_text_verification"]["accepted"] is True
    serialized = json.dumps(payload)
    assert "dockingSuccessObserved" not in serialized
    assert "hidden simulator state" in serialized
    assert payload["observation"]["settled_error_m"] == 0.56

    masked = MODULE.build_export(
        summary,
        repository,
        commit,
        "fixture.yaml",
        0.40,
        "PerformanceResults/run-1/fixture-summary.json",
        frozenset({"measured_speed_at_return"}),
    )
    assert masked["diagnostic_result"]["disposition"] == "insufficient"
    assert masked["observation"]["measured_speed_at_return_mps"] is None
    assert masked["evidence_boundary"]["masked_fields"] == ["measured_speed_at_return"]
    assert "independently measured speed" in masked["diagnostic_result"]["limits"]


def test_retained_goal_supports_navigate_to_pose_schema_without_supplied_path():
    summary = {
        "plannedPath": [],
        "goal": {
            "frame_id": "odom",
            "position": {"x": 0.8641434, "y": -27.586906, "z": 0.1},
            "yaw": 1.5707963267948966,
        },
        "planHistory": [
            {
                "terminal": {
                    "x": 0.8641434,
                    "y": -27.586906,
                    "yaw": 1.5707963267948966,
                }
            }
        ],
    }
    assert MODULE.retained_goal(summary) == {
        "x": 0.8641434,
        "y": -27.586906,
        "yaw": 1.5707963267948966,
    }
