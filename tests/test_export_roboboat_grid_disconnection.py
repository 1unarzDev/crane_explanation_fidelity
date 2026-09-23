import base64
import hashlib
import json
from pathlib import Path
import zlib

from export_roboboat_grid_disconnection import export, recompute_compact


def _write_fixture(path: Path) -> None:
    # Three columns by two rows. The middle column blocks all 8-connected routes at >=253.
    cells = bytes((0, 253, 253, 0, 253, 253))
    path.write_text(
        json.dumps(
            {
                "status": "aborted",
                "wallSeconds": 12.5,
                "actionResultPose": {"x": 0.1, "y": 0.1, "yaw": 0.0},
                "latestCostmapSnapshot": {
                    "data": base64.b64encode(zlib.compress(cells)).decode("ascii"),
                    "dataEncoding": "base64+zlib+uint8-row-major",
                    "dataSha256": hashlib.sha256(cells).hexdigest(),
                    "frameId": "odom",
                    "origin": {"x": 0.0, "y": 0.0, "yaw": 0.0},
                    "resolution": 1.0,
                    "sizeX": 3,
                    "sizeY": 2,
                    "stamp": {"sec": 5, "nanosec": 0},
                },
            }
        ),
        encoding="utf-8",
    )


def test_export_recomputes_connectivity_and_retains_only_robot_visible_inputs(tmp_path):
    fixture = tmp_path / "fixture.json"
    controller_log = tmp_path / "controller.log"
    _write_fixture(fixture)
    controller_log.write_text(
        '[WARN] [5.100] [planner_server]: GridBased plugin failed to plan from '
        '(0.10, 0.10) to (2.10, 0.10): "Failed to create plan with tolerance of: 0.500000"\n',
        encoding="utf-8",
    )

    payload = export(
        fixture,
        controller_log,
        episode_id="boat-test",
        goal_x_m=2.1,
        goal_y_m=0.1,
        blocked_cost_threshold=253,
        committed_parent="a" * 40,
        source_state_note="test fixture",
    )

    assert payload["reference_computation"]["connected_below_threshold"] is False
    assert payload["reference_computation"]["goal_cell"]["cost"] == 253
    assert payload["reference_computation"]["matching_planner_failure_message_count"] == 1
    assert payload["diagnostic_result"]["disposition"] == "supported"
    assert payload["final_text_verification"]["accepted"] is True
    assert any(
        "simulator geometry" in item
        for item in payload["evidence_boundary"]["excluded"]
    )

    recomputed = recompute_compact(payload)
    assert recomputed["reference_computation"]["connected_below_threshold"] is False
    assert recomputed["diagnostic_result"] == payload["diagnostic_result"]
    assert recomputed["final_answer"] == payload["final_answer"]
    assert recomputed["final_text_verification"]["accepted"] is True


def test_export_rejects_corrupt_costmap_hash(tmp_path):
    fixture = tmp_path / "fixture.json"
    controller_log = tmp_path / "controller.log"
    _write_fixture(fixture)
    payload = json.loads(fixture.read_text(encoding="utf-8"))
    payload["latestCostmapSnapshot"]["dataSha256"] = "0" * 64
    fixture.write_text(json.dumps(payload), encoding="utf-8")
    controller_log.write_text("", encoding="utf-8")

    try:
        export(
            fixture,
            controller_log,
            episode_id="boat-test",
            goal_x_m=2.1,
            goal_y_m=0.1,
            blocked_cost_threshold=253,
            committed_parent=None,
            source_state_note="test fixture",
        )
    except ValueError as error:
        assert "SHA-256" in str(error)
    else:
        raise AssertionError("corrupt grid hash was accepted")
